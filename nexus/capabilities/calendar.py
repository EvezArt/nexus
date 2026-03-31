"""
Nexus Calendar — awareness of time, events, and scheduling.

Capabilities:
- Read upcoming events from Google Calendar
- Detect conflicts and overlaps
- Proactive reminders (notify before events)
- Time-aware responses ("you have a meeting in 30 minutes")
- Free/busy time detection

Configuration:
    Set credentials in nexus/config.json under "calendar" key.
    Uses Google Calendar API by default.

Usage:
    from nexus.capabilities.calendar import Calendar
    cal = Calendar()
    events = await cal.upcoming(hours=24)
    if cal.has_conflict(events):
        print("⚠️ Schedule conflict detected!")
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict


WORKSPACE = Path("/root/.openclaw/workspace")
CONFIG_FILE = WORKSPACE / "nexus" / "config.json"


@dataclass
class CalendarEvent:
    """A calendar event."""
    id: str
    title: str
    start: str  # ISO 8601
    end: str    # ISO 8601
    description: str = ""
    location: str = ""
    attendees: List[str] = field(default_factory=list)
    is_recurring: bool = False
    calendar_name: str = "primary"
    status: str = "confirmed"  # confirmed, tentative, cancelled

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def starts_in(self) -> Optional[timedelta]:
        """Time until event starts."""
        try:
            start = datetime.fromisoformat(self.start)
            now = datetime.now(timezone.utc)
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            delta = start - now
            return delta if delta.total_seconds() > 0 else timedelta(0)
        except (ValueError, TypeError):
            return None

    @property
    def summary(self) -> str:
        starts = self.starts_in
        if starts:
            mins = int(starts.total_seconds() / 60)
            return f"📅 {self.title} — in {mins}min"
        return f"📅 {self.title} — {self.start}"


class Calendar:
    """
    Calendar awareness for the nexus.

    Supports:
    1. Google Calendar API (google-api-python-client + OAuth2)
    2. ICS/iCal file import (local or URL)
    3. Manual events (in-memory, for non-Google users)
    """

    def __init__(self, backend: str = "google"):
        self.backend = backend
        self._events: List[CalendarEvent] = []
        self._config = self._load_config()

    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text())
                return cfg.get("calendar", {})
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    async def connect(self) -> bool:
        """
        Establish connection to calendar provider.

        Returns:
            True if connected successfully
        """
        # TODO: Implement Google Calendar OAuth2
        # TODO: Or ICS feed fetching
        raise NotImplementedError(
            "Calendar.connect() is a stub. Implementation options:\n"
            "1. Google Calendar: pip install google-api-python-client google-auth-oauthlib\n"
            "   → OAuth2 flow, scope: calendar.readonly (+calendar.events for writes)\n"
            "2. ICS/iCal: pip install icalendar\n"
            "   → Fetch .ics URL, parse events\n"
            "3. Manual: Just use add_event() and upcoming() with in-memory storage"
        )

    async def fetch_events(self, calendar_id: str = "primary",
                           time_min: Optional[str] = None,
                           time_max: Optional[str] = None,
                           max_results: int = 50) -> List[CalendarEvent]:
        """
        Fetch events from a calendar.

        Args:
            calendar_id: Calendar identifier
            time_min: Start of range (ISO 8601, default: now)
            time_max: End of range (ISO 8601, default: +7 days)
            max_results: Max events to return

        Returns:
            List of CalendarEvent objects
        """
        # TODO: Implement Google Calendar API events.list()
        raise NotImplementedError("Calendar.fetch_events() is a stub. Needs Google Calendar API connection.")

    def add_event(self, title: str, start: str, end: str, **kwargs) -> CalendarEvent:
        """
        Add a local event (no external API needed).

        Args:
            title: Event title
            start: Start time (ISO 8601)
            end: End time (ISO 8601)
            **kwargs: description, location, attendees

        Returns:
            Created CalendarEvent
        """
        event = CalendarEvent(
            id=f"local-{len(self._events)}",
            title=title,
            start=start,
            end=end,
            **kwargs,
        )
        self._events.append(event)
        return event

    async def upcoming(self, hours: int = 24) -> List[CalendarEvent]:
        """
        Get events in the next N hours.

        Args:
            hours: Lookahead window

        Returns:
            Sorted list of upcoming events
        """
        # If connected, fetch from provider
        # If local only, filter in-memory events
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours)

        events = []
        for e in self._events:
            try:
                start = datetime.fromisoformat(e.start)
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                if now <= start <= cutoff:
                    events.append(e)
            except (ValueError, TypeError):
                continue

        # TODO: Also fetch from provider if connected
        return sorted(events, key=lambda e: e.start)

    def has_conflict(self, events: Optional[List[CalendarEvent]] = None) -> List[tuple]:
        """
        Detect overlapping events.

        Args:
            events: Events to check (default: upcoming 24h)

        Returns:
            List of (event_a, event_b) tuples that overlap
        """
        if events is None:
            events = self._events

        conflicts = []
        for i, a in enumerate(events):
            for b in events[i+1:]:
                try:
                    a_start = datetime.fromisoformat(a.start)
                    a_end = datetime.fromisoformat(a.end)
                    b_start = datetime.fromisoformat(b.start)
                    b_end = datetime.fromisoformat(b.end)
                    if a_start < b_end and b_start < a_end:
                        conflicts.append((a, b))
                except (ValueError, TypeError):
                    continue
        return conflicts

    async def now_awareness(self) -> str:
        """
        Generate a time-aware summary for proactive responses.

        Returns:
            Human-readable summary of current time context
        """
        now = datetime.now(timezone.utc)
        upcoming = await self.upcoming(hours=12)
        lines = [f"🕐 {now.strftime('%H:%M UTC, %A %B %d')}"]

        if not upcoming:
            lines.append("No upcoming events in the next 12 hours.")
        else:
            lines.append(f"{len(upcoming)} upcoming events:")
            for e in upcoming[:5]:
                lines.append(f"  {e.summary}")

        conflicts = self.has_conflict(upcoming)
        if conflicts:
            lines.append(f"⚠️ {len(conflicts)} schedule conflicts detected!")

        return "\n".join(lines)
