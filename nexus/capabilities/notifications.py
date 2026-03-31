"""
Nexus Notifications — unified multi-channel notification dispatch.

Capabilities:
- Route notifications to best channel (Telegram, email, push, desktop)
- Priority-based routing (urgent → all channels, info → log only)
- Deduplication (don't spam same notification)
- Rate limiting (max N notifications per hour)
- Notification history

Usage:
    from nexus.capabilities.notifications import Notifier
    ntf = Notifier()
    await ntf.notify("Server CPU at 95%", priority="urgent")
    await ntf.notify("Daily report ready", priority="normal", channel="telegram")
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


WORKSPACE = Path("/root/.openclaw/workspace")
NOTIFICATION_LOG = WORKSPACE / "nexus" / "notifications.jsonl"


class Priority(str, Enum):
    LOW = "low"          # Log only
    NORMAL = "normal"    # Preferred channel
    HIGH = "high"        # Multiple channels
    URGENT = "urgent"    # All channels, bypass rate limit


class Channel(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    PUSH = "push"
    DESKTOP = "desktop"
    LOG = "log"          # Always available, writes to file


@dataclass
class Notification:
    """A notification to dispatch."""
    message: str
    priority: Priority = Priority.NORMAL
    channel: Optional[Channel] = None
    title: str = ""
    dedup_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    dispatched: bool = False
    dispatch_channel: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "priority": self.priority.value if isinstance(self.priority, Priority) else self.priority,
            "channel": self.channel.value if isinstance(self.channel, Channel) else self.channel,
            "title": self.title,
            "dedup_key": self.dedup_key,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "dispatched": self.dispatched,
            "dispatch_channel": self.dispatch_channel,
        }


class Notifier:
    """
    Unified notification dispatcher.

    Routing logic:
    - URGENT → all available channels
    - HIGH → preferred channel + log
    - NORMAL → preferred channel (or log)
    - LOW → log only
    """

    # Which channels each priority level uses
    PRIORITY_CHANNELS = {
        Priority.LOW: [Channel.LOG],
        Priority.NORMAL: [Channel.TELEGRAM, Channel.LOG],
        Priority.HIGH: [Channel.TELEGRAM, Channel.EMAIL, Channel.LOG],
        Priority.URGENT: [Channel.TELEGRAM, Channel.EMAIL, Channel.PUSH, Channel.DESKTOP, Channel.LOG],
    }

    def __init__(self, max_per_hour: int = 20):
        self.max_per_hour = max_per_hour
        self._recent: List[Notification] = []
        self._dedup_cache: Dict[str, float] = {}

    def _should_dedup(self, key: str, window_seconds: int = 300) -> bool:
        """Check if notification was recently sent with same dedup key."""
        if not key:
            return False
        now = time.time()
        if key in self._dedup_cache:
            if now - self._dedup_cache[key] < window_seconds:
                return True
        self._dedup_cache[key] = now
        return False

    def _rate_limited(self) -> bool:
        """Check if we've hit the rate limit."""
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        recent_count = sum(1 for n in self._recent if n.created_at > one_hour_ago)
        return recent_count >= self.max_per_hour

    async def notify(self, message: str, priority: str = "normal",
                     channel: Optional[str] = None,
                     title: str = "",
                     dedup_key: Optional[str] = None,
                     **metadata) -> Notification:
        """
        Send a notification.

        Args:
            message: Notification message
            priority: "low", "normal", "high", "urgent"
            channel: Force specific channel (overrides routing)
            title: Notification title
            dedup_key: Deduplicate by this key (suppress repeats within 5min)
            **metadata: Additional metadata

        Returns:
            Notification object (check dispatched field)
        """
        pri = Priority(priority)
        chan = Channel(channel) if channel else None

        ntf = Notification(
            message=message,
            priority=pri,
            channel=chan,
            title=title or message[:50],
            dedup_key=dedup_key,
            metadata=metadata,
        )

        # Deduplication
        if dedup_key and self._should_dedup(dedup_key):
            ntf.dispatched = False
            ntf.dispatch_channel = "deduplicated"
            return ntf

        # Rate limiting (except urgent)
        if pri != Priority.URGENT and self._rate_limited():
            ntf.dispatched = False
            ntf.dispatch_channel = "rate_limited"
            self._log(ntf)
            return ntf

        # Dispatch
        channels = [chan] if chan else self.PRIORITY_CHANNELS.get(pri, [Channel.LOG])

        for ch in channels:
            try:
                await self._dispatch_to_channel(ntf, ch)
                ntf.dispatched = True
                ntf.dispatch_channel = ch.value
                break  # First successful channel wins (unless URGENT sends to all)
            except Exception:
                continue

        self._recent.append(ntf)
        self._log(ntf)
        return ntf

    async def _dispatch_to_channel(self, ntf: Notification, channel: Channel):
        """Dispatch notification to a specific channel."""
        if channel == Channel.LOG:
            # Always works — just write to file
            return
        elif channel == Channel.TELEGRAM:
            # TODO: Wire to telegram_bot.py send
            raise NotImplementedError("Telegram dispatch not wired to telegram_bot.py yet")
        elif channel == Channel.EMAIL:
            # TODO: Wire to email_client.py
            raise NotImplementedError("Email dispatch not wired to email_client.py yet")
        elif channel == Channel.PUSH:
            # TODO: Implement push notification (FCM, web push, etc.)
            raise NotImplementedError("Push notifications not implemented")
        elif channel == Channel.DESKTOP:
            # TODO: Implement desktop notification (notify-send, osascript)
            raise NotImplementedError("Desktop notifications not implemented")

    def _log(self, ntf: Notification):
        """Log notification to file."""
        NOTIFICATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(NOTIFICATION_LOG, "a") as f:
            f.write(json.dumps(ntf.to_dict()) + "\n")

    def history(self, limit: int = 50) -> List[dict]:
        """Read notification history."""
        if not NOTIFICATION_LOG.exists():
            return []
        lines = NOTIFICATION_LOG.read_text().strip().split("\n")
        entries = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    def summary(self) -> str:
        """Human-readable notification summary."""
        if not self._recent:
            return "No recent notifications."
        lines = [f"🔔 {len(self._recent)} recent notifications:"]
        for ntf in self._recent[-10:]:
            status = "✅" if ntf.dispatched else "❌"
            lines.append(f"  {status} [{ntf.priority.value}] {ntf.message[:60]}")
        return "\n".join(lines)
