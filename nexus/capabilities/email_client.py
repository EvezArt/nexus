"""
Nexus Email Client — read, send, and manage email.

Capabilities:
- Read inbox (IMAP or Gmail API)
- Send emails (SMTP or Gmail API)
- Search by sender, subject, date, content
- Label/folder management
- Attachment extraction
- Auto-categorization (urgent, newsletter, notification)

Configuration:
    Set credentials in nexus/config.json under "email" key.
    Supports Gmail OAuth2 and generic IMAP/SMTP.

Usage:
    from nexus.capabilities.email_client import EmailClient
    email = EmailClient()
    inbox = await email.fetch(limit=10, unread_only=True)
    await email.send(to="...", subject="...", body="...")
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict


WORKSPACE = Path("/root/.openclaw/workspace")
CONFIG_FILE = WORKSPACE / "nexus" / "config.json"


@dataclass
class Email:
    """Normalized email across providers."""
    id: str
    sender: str
    recipient: str = ""
    subject: str = ""
    body: str = ""
    body_html: str = ""
    date: str = ""
    labels: List[str] = field(default_factory=list)
    attachments: List[Dict[str, str]] = field(default_factory=list)
    is_read: bool = False
    is_urgent: bool = False
    raw_headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def summary(self) -> str:
        return f"[{'UNREAD' if not self.is_read else 'read'}] {self.sender}: {self.subject}"


class EmailClient:
    """
    Email integration for the nexus.

    Supports two backends:
    1. Gmail API (google-api-python-client + OAuth2)
    2. IMAP/SMTP (imaplib + smtplib)
    """

    def __init__(self, backend: str = "gmail"):
        self.backend = backend
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Load email config from nexus config."""
        if CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text())
                return cfg.get("email", {})
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    async def connect(self) -> bool:
        """
        Establish connection to email provider.

        Returns:
            True if connected successfully
        """
        # TODO: Implement Gmail OAuth2 flow
        # TODO: Or IMAP connection with credentials
        # TODO: Store token/refresh in config
        raise NotImplementedError(
            "EmailClient.connect() is a stub. Implementation options:\n"
            "1. Gmail API: pip install google-api-python-client google-auth-oauthlib\n"
            "   → OAuth2 flow, store token.json, refresh on expiry\n"
            "2. IMAP: imaplib.IMAP4_SSL + smtplib.SMTP_SSL\n"
            "   → Store credentials in nexus/config.json"
        )

    async def fetch(self, limit: int = 20, unread_only: bool = False,
                    query: Optional[str] = None) -> List[Email]:
        """
        Fetch emails from inbox.

        Args:
            limit: Max emails to fetch
            unread_only: Only unread messages
            query: Search query (Gmail query syntax or IMAP SEARCH)

        Returns:
            List of Email objects
        """
        # TODO: Implement email fetching
        raise NotImplementedError("EmailClient.fetch() is a stub. Needs IMAP or Gmail API connection.")

    async def send(self, to: str, subject: str, body: str,
                   html: bool = False, cc: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> str:
        """
        Send an email.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (plain text or HTML)
            html: Treat body as HTML
            cc: CC recipients
            attachments: File paths to attach

        Returns:
            Message ID of sent email
        """
        # TODO: Implement email sending
        raise NotImplementedError("EmailClient.send() is a stub. Needs SMTP or Gmail API connection.")

    async def mark_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        # TODO: Implement
        raise NotImplementedError("EmailClient.mark_read() is a stub.")

    async def delete(self, message_id: str, permanent: bool = False) -> bool:
        """Delete an email (move to trash by default)."""
        # TODO: Implement
        raise NotImplementedError("EmailClient.delete() is a stub.")

    async def categorize(self, email: Email) -> Email:
        """
        Auto-categorize an email based on content.

        Sets labels and urgency flags.
        """
        # TODO: Implement heuristic categorization
        # TODO: Consider LLM-based categorization for ambiguous cases
        urgent_keywords = ["urgent", "asap", "deadline", "critical", "emergency", "action required"]
        if any(kw in email.subject.lower() for kw in urgent_keywords):
            email.is_urgent = True
        return email

    def summary(self, emails: List[Email]) -> str:
        """Generate a human-readable summary of emails."""
        if not emails:
            return "Inbox is empty."
        lines = []
        urgent = [e for e in emails if e.is_urgent]
        if urgent:
            lines.append(f"⚠️ {len(urgent)} URGENT emails:")
            for e in urgent:
                lines.append(f"  {e.summary}")
        rest = [e for e in emails if not e.is_urgent]
        if rest:
            lines.append(f"\n📬 {len(rest)} other emails:")
            for e in rest[:10]:
                lines.append(f"  {e.summary}")
        return "\n".join(lines)
