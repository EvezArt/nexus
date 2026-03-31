#!/usr/bin/env python3
"""
NEXUS INCOME ENGINE — Autonomous task execution for revenue.

This is how the entity farm generates value:
1. Accepts tasks via HTTP API (research, writing, coding, analysis)
2. Routes to the best provider (ChatGPT for code, Perplexity for research)
3. Executes and delivers results
4. Tracks completed work and revenue

Revenue models:
- Per-task pricing (research reports, code generation, analysis)
- Subscription API access (monthly recurring)
- Freelance automation (Upwork/Fiverr task completion)
- Content generation (blog posts, documentation, analysis)

The engine doesn't just chat — it DOES WORK.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

import sys
sys.path.insert(0, str(Path(__file__).parent))
from nexus_core import NexusCore
from providers.base import Message


WORKSPACE = Path("/root/.openclaw/workspace")
INCOME_DIR = WORKSPACE / "nexus" / "income"
TASKS_FILE = INCOME_DIR / "tasks.jsonl"
REVENUE_FILE = INCOME_DIR / "revenue.json"
LEDGER_FILE = INCOME_DIR / "ledger.jsonl"


@dataclass
class Task:
    """A billable task."""
    id: str
    type: str  # "research", "writing", "coding", "analysis", "trading"
    description: str
    status: str = "pending"  # pending, running, completed, failed, delivered
    created: str = ""
    completed: str = ""
    provider: str = "auto"
    result: str = ""
    revenue_usd: float = 0.0
    client_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created:
            self.created = datetime.now(timezone.utc).isoformat()


class IncomeEngine:
    """Autonomous task execution and revenue tracking."""

    def __init__(self):
        INCOME_DIR.mkdir(parents=True, exist_ok=True)
        self.core = NexusCore()
        self.tasks: Dict[str, Task] = {}
        self.revenue = self._load_revenue()
        self._load_tasks()

    def _load_tasks(self):
        if TASKS_FILE.exists():
            for line in TASKS_FILE.read_text().splitlines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        self.tasks[data["id"]] = Task(**data)
                    except (json.JSONDecodeError, KeyError):
                        pass

    def _save_task(self, task: Task):
        with open(TASKS_FILE, "a") as f:
            f.write(json.dumps(asdict(task)) + "\n")

    def _load_revenue(self) -> dict:
        if REVENUE_FILE.exists():
            try:
                return json.loads(REVENUE_FILE.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "total_usd": 0.0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_revenue_per_task": 0.0,
            "uptime_hours": 0.0,
        }

    def _save_revenue(self):
        REVENUE_FILE.write_text(json.dumps(self.revenue, indent=2))

    def _log_ledger(self, entry: dict):
        with open(LEDGER_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    async def submit_task(self, task_type: str, description: str,
                          price_usd: float = 0.0,
                          client_id: str = "",
                          provider: str = "auto") -> Task:
        """Submit a new task for execution."""
        import hashlib
        task_id = hashlib.sha256(
            f"{task_type}:{description}:{time.time()}".encode()
        ).hexdigest()[:12]

        task = Task(
            id=task_id,
            type=task_type,
            description=description,
            revenue_usd=price_usd,
            client_id=client_id,
            provider=provider,
        )

        self.tasks[task_id] = task
        self._save_task(task)

        return task

    async def execute_task(self, task_id: str) -> Task:
        """Execute a pending task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = "running"
        self._save_task(task)

        try:
            # Build provider-specific prompt based on task type
            prompts = {
                "research": f"Research the following thoroughly and provide a comprehensive report with citations:\n\n{task.description}",
                "writing": f"Write the following content:\n\n{task.description}",
                "coding": f"Implement the following:\n\n{task.description}",
                "analysis": f"Analyze the following and provide insights:\n\n{task.description}",
                "trading": f"Analyze the following market situation and provide actionable recommendations:\n\n{task.description}",
            }

            prompt = prompts.get(task.type, task.description)

            # Route to appropriate provider
            provider = task.provider
            if provider == "auto":
                if task.type in ("research", "trading"):
                    provider = "perplexity"
                elif task.type in ("coding", "analysis"):
                    provider = "chatgpt"
                else:
                    provider = "auto"

            resp = await self.core.chat(prompt, provider=provider)

            task.result = resp.content
            task.status = "completed"
            task.completed = datetime.now(timezone.utc).isoformat()

            # Track revenue
            if task.revenue_usd > 0:
                self.revenue["total_usd"] += task.revenue_usd
                self._log_ledger({
                    "ts": task.completed,
                    "type": "revenue",
                    "amount_usd": task.revenue_usd,
                    "task_id": task.id,
                    "task_type": task.type,
                    "client_id": task.client_id,
                    "provider": resp.provider,
                    "tokens_used": resp.tokens_used,
                })

            self.revenue["tasks_completed"] += 1
            self.revenue["avg_revenue_per_task"] = (
                self.revenue["total_usd"] / max(1, self.revenue["tasks_completed"])
            )
            self._save_revenue()
            self._save_task(task)

        except Exception as e:
            task.status = "failed"
            task.result = f"Error: {str(e)}"
            task.completed = datetime.now(timezone.utc).isoformat()
            self.revenue["tasks_failed"] += 1
            self._save_revenue()
            self._save_task(task)

        return task

    async def execute_pending(self) -> List[Task]:
        """Execute all pending tasks."""
        results = []
        for task in list(self.tasks.values()):
            if task.status == "pending":
                result = await self.execute_task(task.id)
                results.append(result)
        return results

    def get_dashboard(self) -> dict:
        """Revenue and task dashboard."""
        pending = sum(1 for t in self.tasks.values() if t.status == "pending")
        running = sum(1 for t in self.tasks.values() if t.status == "running")
        completed = sum(1 for t in self.tasks.values() if t.status == "completed")
        failed = sum(1 for t in self.tasks.values() if t.status == "failed")

        return {
            "revenue": self.revenue,
            "tasks": {
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "total": len(self.tasks),
            },
            "providers": self.core.available_providers(),
        }

    async def close(self):
        await self.core.close()
