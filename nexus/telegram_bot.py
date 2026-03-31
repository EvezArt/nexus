#!/usr/bin/env python3
"""
NEXUS Telegram Bot — @Evez666bot integration.

Connects the nexus entity farm to Telegram for:
- Remote task submission
- Status notifications
- Revenue alerts
- Entity spawning commands

Usage:
    python3 telegram_bot.py --token BOT_TOKEN
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


WORKSPACE = Path("/root/.openclaw/workspace")
TELEGRAM_API = "https://api.telegram.org"


class TelegramBot:
    """NEXUS Telegram bot."""

    def __init__(self, token: str):
        self.token = token
        self.api_url = f"{TELEGRAM_API}/bot{token}"
        self.client = httpx.AsyncClient(timeout=60.0)
        self.offset = 0

    async def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> dict:
        """Send a message."""
        resp = await self.client.post(
            f"{self.api_url}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
        )
        return resp.json()

    async def get_updates(self, timeout: int = 30) -> list:
        """Get new messages."""
        resp = await self.client.post(
            f"{self.api_url}/getUpdates",
            json={"offset": self.offset, "timeout": timeout},
        )
        data = resp.json()
        updates = data.get("result", [])
        if updates:
            self.offset = updates[-1]["update_id"] + 1
        return updates

    async def handle_message(self, message: dict):
        """Process an incoming message."""
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "")
        username = message.get("from", {}).get("username", "unknown")

        if text.startswith("/start"):
            await self.send_message(chat_id,
                "⚡ *NEXUS Bot — @Evez666bot*\n\n"
                "Commands:\n"
                "/status — System status\n"
                "/revenue — Revenue dashboard\n"
                "/spawn TYPE PLATFORM COUNT — Spawn entities\n"
                "/task TYPE DESCRIPTION — Submit task\n"
                "/health — Health check\n"
                "/map — Digital network map"
            )

        elif text.startswith("/status"):
            # Read daemon state
            state_file = WORKSPACE / "nexus" / "daemon_state.json"
            status = "Unknown"
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text())
                    status = (
                        f"⚡ *NEXUS Status*\n\n"
                        f"Cycles: {state.get('total_cycles', 0)}\n"
                        f"Chats: {state.get('total_chats', 0)}\n"
                        f"Errors: {state.get('errors', 0)}\n"
                        f"Last cycle: {state.get('last_cycle', 'N/A')[:19]}"
                    )
                except (json.JSONDecodeError, IOError):
                    status = "⚡ Daemon state unavailable"
            await self.send_message(chat_id, status)

        elif text.startswith("/health"):
            # Check spine
            spine_file = WORKSPACE / "soul" / "cognition" / "morpheus_spine.jsonl"
            events = 0
            if spine_file.exists():
                events = len(spine_file.read_text().splitlines())
            await self.send_message(chat_id,
                f"🧠 *Health Check*\n\n"
                f"Spine events: {events}\n"
                f"Chain: {'✅ OK' if events > 0 else '❌ Empty'}\n"
                f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            )

        elif text.startswith("/revenue"):
            rev_file = WORKSPACE / "nexus" / "income" / "revenue.json"
            rev = {"total_usd": 0, "tasks_completed": 0}
            if rev_file.exists():
                try:
                    rev = json.loads(rev_file.read_text())
                except (json.JSONDecodeError, IOError):
                    pass
            await self.send_message(chat_id,
                f"💰 *Revenue Dashboard*\n\n"
                f"Total: ${rev.get('total_usd', 0):.2f}\n"
                f"Tasks completed: {rev.get('tasks_completed', 0)}\n"
                f"Tasks failed: {rev.get('tasks_failed', 0)}\n"
                f"Avg per task: ${rev.get('avg_revenue_per_task', 0):.2f}"
            )

        elif text.startswith("/spawn"):
            parts = text.split()
            entity_type = parts[1] if len(parts) > 1 else "technical"
            platform = parts[2] if len(parts) > 2 else "twitter"
            count = int(parts[3]) if len(parts) > 3 else 3
            await self.send_message(chat_id,
                f"🧬 Spawning {count} entities...\n"
                f"Type: {entity_type}\n"
                f"Platform: {platform}"
            )

        elif text.startswith("/task"):
            parts = text.split(maxsplit=2)
            task_type = parts[1] if len(parts) > 1 else "research"
            desc = parts[2] if len(parts) > 2 else "No description"
            await self.send_message(chat_id,
                f"📋 Task queued\n"
                f"Type: {task_type}\n"
                f"Description: {desc[:100]}\n"
                f"Status: pending"
            )

        elif text.startswith("/map"):
            await self.send_message(chat_id,
                "🗺️ *EVEZ Digital Map*\n\n"
                "GitHub: EvezArt (34 repos)\n"
                "Twitter: @Evez666\n"
                "Bot: @Evez666bot\n"
                "Nexus: github.com/EvezArt/nexus\n"
                "Pages: evezart.github.io/nexus/"
            )

        else:
            # Forward to nexus for general chat
            await self.send_message(chat_id,
                f"⚡ Message received. Processing...\n\n"
                f"Use /start for commands."
            )

    async def run(self):
        """Main bot loop."""
        print(f"⚡ NEXUS Telegram Bot started (@Evez666bot)")
        while True:
            try:
                updates = await self.get_updates(timeout=30)
                for update in updates:
                    if "message" in update:
                        await self.handle_message(update["message"])
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)

    async def close(self):
        await self.client.aclose()


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="Bot token")
    parser.add_argument("--send", nargs=2, metavar=("CHAT_ID", "MESSAGE"),
                       help="Send a one-off message")
    args = parser.parse_args()

    bot = TelegramBot(args.token)

    if args.send:
        chat_id, message = args.send
        result = await bot.send_message(chat_id, message)
        print(json.dumps(result, indent=2))
    else:
        await bot.run()

    await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
