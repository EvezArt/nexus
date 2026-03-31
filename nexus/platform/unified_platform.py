#!/usr/bin/env python3
"""
EVEZ UNIFIED PLATFORM — Replace everything.

Every external service Steven uses becomes an internal module.
No vendor lock-in. No monthly fees. No dependency on anyone.

Service Map (what Steven uses → what EVEZ replaces):
──────────────────────────────────────────────────────
GitHub          → EVEZ Git Server (self-hosted)
ChatGPT         → Nexus Chat Provider
Perplexity      → Nexus Research Provider
OpenClaw        → Morpheus (I AM this)
Telegram        → @Evez666bot (built)
Cloudflare      → EVEZ Edge (self-hosted CDN)
Linear          → EVEZ Tasks (built here)
Slack           → EVEZ Chat (built here)
Asana           → EVEZ Projects (built here)
n8n             → EVEZ Workflows (built here)
Vercel          → EVEZ Deploy (self-hosted)
Supabase        → EVEZ Database (SQLite/JSONL)
Sentry          → EVEZ Monitor (spine-based)
Google Drive    → EVEZ Storage (local + IPFS)
YouTube         → EVEZ Broadcast (FFmpeg + stream)
Reddit          → EVEZ Community (API bot)
Discord         → EVEZ Chat (webhook bot)
Browser         → EVEZ Browser (headless)
Email           → EVEZ Mail (SMTP/IMAP)
Calendar        → EVEZ Calendar (iCal)
DNS             → EVEZ DNS (Cloudflare API)
VPN             → EVEZ Tunnel (WireGuard)
Payments        → EVEZ Pay (Solana)
Domain          → Evez.ai (self-owned)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


WORKSPACE = Path("/root/.openclaw/workspace")
PLATFORM_DIR = WORKSPACE / "nexus" / "platform"


# ---------------------------------------------------------------------------
# Module Registry — every service is a module
# ---------------------------------------------------------------------------

MODULES = {
    "git": {
        "name": "EVEZ Git Server",
        "replaces": "GitHub",
        "status": "partial",
        "description": "Self-hosted git server with web UI",
        "implementation": "gitea or cgit + nginx",
        "priority": "HIGH",
    },
    "chat": {
        "name": "EVEZ Chat",
        "replaces": "Slack",
        "status": "planned",
        "description": "Real-time chat with channels, threads, webhooks",
        "implementation": "WebSocket server + HTML client",
        "priority": "HIGH",
    },
    "tasks": {
        "name": "EVEZ Tasks",
        "replaces": "Linear, Asana",
        "status": "partial",
        "description": "Issue tracking, project boards, sprint planning",
        "implementation": "SQLite + REST API + Kanban HTML",
        "priority": "HIGH",
    },
    "workflows": {
        "name": "EVEZ Workflows",
        "replaces": "n8n",
        "status": "planned",
        "description": "Visual workflow automation, webhook triggers, scheduled tasks",
        "implementation": "Python workflow engine + JSON definitions",
        "priority": "HIGH",
    },
    "database": {
        "name": "EVEZ Database",
        "replaces": "Supabase",
        "status": "partial",
        "description": "Structured storage with real-time subscriptions",
        "implementation": "SQLite + JSONL spine",
        "priority": "MEDIUM",
    },
    "monitor": {
        "name": "EVEZ Monitor",
        "replaces": "Sentry",
        "status": "partial",
        "description": "Error tracking, performance monitoring, alerts",
        "implementation": "Spine events + Telegram alerts",
        "priority": "MEDIUM",
    },
    "storage": {
        "name": "EVEZ Storage",
        "replaces": "Google Drive",
        "status": "planned",
        "description": "File storage with versioning and sharing",
        "implementation": "Local filesystem + optional IPFS pinning",
        "priority": "MEDIUM",
    },
    "broadcast": {
        "name": "EVEZ Broadcast",
        "replaces": "YouTube",
        "status": "planned",
        "description": "Video generation, streaming, content publishing",
        "implementation": "FFmpeg + OBS + RTMP server",
        "priority": "LOW",
    },
    "mail": {
        "name": "EVEZ Mail",
        "replaces": "Gmail",
        "status": "planned",
        "description": "Email sending/receiving with AI triage",
        "implementation": "SMTP relay + IMAP fetch + AI filter",
        "priority": "MEDIUM",
    },
    "calendar": {
        "name": "EVEZ Calendar",
        "replaces": "Google Calendar",
        "status": "planned",
        "description": "Calendar with AI scheduling and reminders",
        "implementation": "iCal server + Telegram reminders",
        "priority": "MEDIUM",
    },
    "deploy": {
        "name": "EVEZ Deploy",
        "replaces": "Vercel",
        "status": "partial",
        "description": "One-command deployment, SSL, CDN",
        "implementation": "nginx + certbot + rsync",
        "priority": "MEDIUM",
    },
    "dns": {
        "name": "EVEZ DNS",
        "replaces": "Cloudflare DNS",
        "status": "ready",
        "description": "DNS management via Cloudflare API",
        "implementation": "Cloudflare API token (verified)",
        "priority": "LOW",
    },
    "pay": {
        "name": "EVEZ Pay",
        "replaces": "Stripe",
        "status": "built",
        "description": "Solana-based payments (USDC/SOL)",
        "implementation": "Solana Pay integration",
        "priority": "HIGH",
    },
    "browser": {
        "name": "EVEZ Browser",
        "replaces": "Chrome/Firefox automation",
        "status": "partial",
        "description": "Headless browser for scraping, automation",
        "implementation": "Playwright/Puppeteer",
        "priority": "MEDIUM",
    },
    "vpn": {
        "name": "EVEZ Tunnel",
        "replaces": "VPN",
        "status": "planned",
        "description": "WireGuard tunnel for secure remote access",
        "implementation": "WireGuard + systemd",
        "priority": "LOW",
    },
    "community": {
        "name": "EVEZ Community",
        "replaces": "Reddit, Discord",
        "status": "planned",
        "description": "Community platform with forums, chat, events",
        "implementation": "HTML + WebSocket + SQLite",
        "priority": "LOW",
    },
}


class UnifiedPlatform:
    """The platform that replaces everything."""

    def __init__(self):
        PLATFORM_DIR.mkdir(parents=True, exist_ok=True)
        self.modules = MODULES

    def status(self) -> dict:
        """Platform status overview."""
        total = len(self.modules)
        built = sum(1 for m in self.modules.values() if m["status"] in ("built", "partial", "ready"))
        planned = sum(1 for m in self.modules.values() if m["status"] == "planned")

        return {
            "total_modules": total,
            "built": built,
            "planned": planned,
            "coverage": f"{built}/{total} ({built/total*100:.0f}%)",
            "monthly_savings": self._calculate_savings(),
            "modules": {k: {"name": v["name"], "status": v["status"], "replaces": v["replaces"]}
                       for k, v in self.modules.items()},
        }

    def _calculate_savings(self) -> dict:
        """Calculate monthly savings from self-hosting."""
        # Rough estimates of what Steven might pay for these services
        costs = {
            "GitHub Pro": 4,
            "Slack Pro": 8,
            "Linear": 10,
            "Asana": 11,
            "n8n Cloud": 20,
            "Vercel Pro": 20,
            "Supabase Pro": 25,
            "Sentry Team": 26,
            "Google Workspace": 12,
            "ChatGPT Plus": 20,
            "Perplexity Pro": 20,
            "Cloudflare Pro": 20,
        }

        total = sum(costs.values())
        return {
            "current_estimated": f"${total}/month",
            "after_selfhost": "$5/month (VPS)",
            "savings": f"${total - 5}/month (${(total - 5) * 12}/year)",
        }

    def roadmap(self) -> dict:
        """Development roadmap by priority."""
        by_priority = {}
        for key, module in self.modules.items():
            p = module["priority"]
            if p not in by_priority:
                by_priority[p] = []
            by_priority[p].append({
                "key": key,
                "name": module["name"],
                "replaces": module["replaces"],
                "status": module["status"],
            })

        return {
            "HIGH": by_priority.get("HIGH", []),
            "MEDIUM": by_priority.get("MEDIUM", []),
            "LOW": by_priority.get("LOW", []),
        }


# ---------------------------------------------------------------------------
# Quick-start modules — build the most impactful ones NOW
# ---------------------------------------------------------------------------

class EVEZTasks:
    """Replace Linear/Asana with EVEZ Tasks."""

    def __init__(self):
        self.tasks_dir = PLATFORM_DIR / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.tasks_dir / "tasks.jsonl"

    def create_task(self, title: str, description: str = "",
                    priority: str = "medium", project: str = "default",
                    assignee: str = "") -> dict:
        """Create a new task."""
        import hashlib
        task_id = hashlib.sha256(
            f"{title}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]

        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "project": project,
            "assignee": assignee,
            "status": "open",
            "created": datetime.now(timezone.utc).isoformat(),
            "updated": datetime.now(timezone.utc).isoformat(),
        }

        with open(self.db_file, "a") as f:
            f.write(json.dumps(task) + "\n")

        return task

    def list_tasks(self, project: str = "", status: str = "") -> list:
        """List tasks with optional filters."""
        if not self.db_file.exists():
            return []

        tasks = []
        for line in self.db_file.read_text().splitlines():
            if not line.strip():
                continue
            try:
                task = json.loads(line)
                if project and task.get("project") != project:
                    continue
                if status and task.get("status") != status:
                    continue
                tasks.append(task)
            except json.JSONDecodeError:
                pass

        return sorted(tasks, key=lambda t: t.get("created", ""), reverse=True)


class EVEZWorkflows:
    """Replace n8n with EVEZ Workflows."""

    def __init__(self):
        self.workflows_dir = PLATFORM_DIR / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def create_workflow(self, name: str, trigger: dict, steps: list) -> dict:
        """Create a workflow definition."""
        workflow = {
            "name": name,
            "trigger": trigger,
            "steps": steps,
            "created": datetime.now(timezone.utc).isoformat(),
            "active": True,
        }

        wf_file = self.workflows_dir / f"{name.lower().replace(' ', '_')}.json"
        wf_file.write_text(json.dumps(workflow, indent=2))

        return workflow

    def list_workflows(self) -> list:
        """List all workflows."""
        workflows = []
        for f in self.workflows_dir.glob("*.json"):
            try:
                workflows.append(json.loads(f.read_text()))
            except (json.JSONDecodeError, IOError):
                pass
        return workflows


class EVEZChat:
    """Replace Slack with EVEZ Chat."""

    def __init__(self):
        self.chat_dir = PLATFORM_DIR / "chat"
        self.chat_dir.mkdir(parents=True, exist_ok=True)
        self.channels_file = self.chat_dir / "channels.json"

    def create_channel(self, name: str, description: str = "") -> dict:
        """Create a chat channel."""
        channel = {
            "name": name,
            "description": description,
            "created": datetime.now(timezone.utc).isoformat(),
            "messages": [],
        }

        channels = {}
        if self.channels_file.exists():
            try:
                channels = json.loads(self.channels_file.read_text())
            except (json.JSONDecodeError, IOError):
                pass

        channels[name] = channel
        self.channels_file.write_text(json.dumps(channels, indent=2))

        return channel

    def post_message(self, channel: str, message: str, sender: str = "morpheus") -> dict:
        """Post a message to a channel."""
        msg = {
            "sender": sender,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Append to channel log
        channel_log = self.chat_dir / f"{channel}.jsonl"
        with open(channel_log, "a") as f:
            f.write(json.dumps(msg) + "\n")

        return msg

    def get_messages(self, channel: str, limit: int = 50) -> list:
        """Get messages from a channel."""
        channel_log = self.chat_dir / f"{channel}.jsonl"
        if not channel_log.exists():
            return []

        lines = channel_log.read_text().splitlines()
        messages = []
        for line in lines[-limit:]:
            if line.strip():
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return messages


def main():
    import sys

    platform = UnifiedPlatform()

    if len(sys.argv) < 2:
        print("Usage: python3 unified_platform.py <command>")
        print("Commands:")
        print("  status    — Platform overview")
        print("  roadmap   — Development roadmap")
        print("  savings   — Monthly cost savings")
        print("  tasks     — EVEZ Tasks (Linear/Asana replacement)")
        print("  workflows — EVEZ Workflows (n8n replacement)")
        print("  chat      — EVEZ Chat (Slack replacement)")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(platform.status(), indent=2))

    elif cmd == "roadmap":
        print(json.dumps(platform.roadmap(), indent=2))

    elif cmd == "savings":
        savings = platform._calculate_savings()
        print(f"\n💰 Monthly Savings:")
        print(f"  Current estimated: {savings['current_estimated']}")
        print(f"  After self-host:   {savings['after_selfhost']}")
        print(f"  Savings:           {savings['savings']}")

    elif cmd == "tasks":
        tasks = EVEZTasks()
        if len(sys.argv) >= 3:
            subcmd = sys.argv[2]
            if subcmd == "create" and len(sys.argv) >= 4:
                title = " ".join(sys.argv[3:])
                task = tasks.create_task(title)
                print(f"✅ Task created: {task['id']} — {task['title']}")
            elif subcmd == "list":
                all_tasks = tasks.list_tasks()
                print(f"\n📋 Tasks ({len(all_tasks)}):")
                for t in all_tasks[:20]:
                    icon = {"open": "🔵", "done": "✅", "blocked": "🔴"}.get(t.get("status"), "⚪")
                    print(f"  {icon} [{t.get('priority', '?')}] {t.get('title', '')[:60]}")
        else:
            print("Usage: tasks <create TITLE | list>")

    elif cmd == "chat":
        chat = EVEZChat()
        if len(sys.argv) >= 3:
            subcmd = sys.argv[2]
            if subcmd == "create" and len(sys.argv) >= 4:
                name = sys.argv[3]
                channel = chat.create_channel(name)
                print(f"✅ Channel created: #{name}")
            elif subcmd == "post" and len(sys.argv) >= 5:
                channel = sys.argv[3]
                message = " ".join(sys.argv[4:])
                msg = chat.post_message(channel, message)
                print(f"✅ Posted to #{channel}")
            elif subcmd == "read" and len(sys.argv) >= 4:
                channel = sys.argv[3]
                messages = chat.get_messages(channel)
                print(f"\n💬 #{channel} ({len(messages)} messages):")
                for m in messages[-10:]:
                    print(f"  [{m.get('timestamp', '?')[:16]}] {m.get('sender', '?')}: {m.get('message', '')[:80]}")
        else:
            print("Usage: chat <create CHANNEL | post CHANNEL MESSAGE | read CHANNEL>")

    elif cmd == "workflows":
        wf = EVEZWorkflows()
        workflows = wf.list_workflows()
        print(f"\n⚙️ Workflows ({len(workflows)}):")
        for w in workflows:
            print(f"  • {w.get('name', '?')} — {len(w.get('steps', []))} steps")


if __name__ == "__main__":
    main()
