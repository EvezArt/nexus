"""
Nexus Scheduler — task scheduling and cron-like behavior.

Capabilities:
- Schedule one-shot tasks (run at specific time)
- Schedule recurring tasks (cron expressions)
- Reminder notifications
- Task dependency chains
- Schedule management (list, cancel, modify)

Usage:
    from nexus.capabilities.scheduler import TaskScheduler
    sched = TaskScheduler()
    await sched.schedule_once("2026-04-01T09:00:00Z", "Send weekly report")
    await sched.schedule_cron("0 9 * * 1", "Monday standup reminder")
    await sched.remind("Check server health", minutes=30)
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum


WORKSPACE = Path("/root/.openclaw/workspace")
SCHEDULE_FILE = WORKSPACE / "nexus" / "schedule.json"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """A scheduled task."""
    id: str
    description: str
    schedule: str  # ISO 8601 datetime or cron expression
    task_type: str = "once"  # "once" or "cron"
    status: TaskStatus = TaskStatus.PENDING
    callback: Optional[str] = None  # Python callback name/path
    params: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.id:
            self.id = uuid.uuid4().hex[:12]

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "description": self.description,
            "schedule": self.schedule,
            "task_type": self.task_type,
            "status": self.status.value,
            "callback": self.callback,
            "params": self.params,
            "created_at": self.created_at,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
        }
        return d


class TaskScheduler:
    """
    Task scheduler for the nexus.

    Supports:
    1. One-shot: Run at a specific datetime
    2. Cron: Run on a schedule (parsed from cron expression)
    3. Reminder: "Remind me in X minutes/hours"

    Storage: JSON file for persistence across daemon restarts.
    Execution: Integrates with nexus daemon cycle or standalone asyncio loop.
    """

    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._load()

    def _load(self):
        """Load scheduled tasks from disk."""
        if SCHEDULE_FILE.exists():
            try:
                data = json.loads(SCHEDULE_FILE.read_text())
                for task_data in data.get("tasks", []):
                    task = ScheduledTask(**task_data)
                    self._tasks[task.id] = task
            except (json.JSONDecodeError, IOError, TypeError):
                pass

    def _save(self):
        """Persist scheduled tasks."""
        SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tasks": [t.to_dict() for t in self._tasks.values()],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        SCHEDULE_FILE.write_text(json.dumps(data, indent=2))

    def schedule_once(self, when: str, description: str,
                      callback: Optional[str] = None,
                      params: Optional[Dict[str, Any]] = None) -> ScheduledTask:
        """
        Schedule a one-shot task.

        Args:
            when: ISO 8601 datetime (e.g. "2026-04-01T09:00:00Z")
            description: What to do
            callback: Optional callback identifier
            params: Optional parameters for callback

        Returns:
            Created ScheduledTask
        """
        task = ScheduledTask(
            id=uuid.uuid4().hex[:12],
            description=description,
            schedule=when,
            task_type="once",
            callback=callback,
            params=params or {},
            next_run=when,
        )
        self._tasks[task.id] = task
        self._save()
        return task

    def schedule_cron(self, cron_expr: str, description: str,
                      callback: Optional[str] = None,
                      params: Optional[Dict[str, Any]] = None) -> ScheduledTask:
        """
        Schedule a recurring task with cron syntax.

        Args:
            cron_expr: Cron expression (e.g. "0 9 * * 1" = every Monday 9am)
            description: What to do
            callback: Optional callback identifier
            params: Optional parameters

        Returns:
            Created ScheduledTask
        """
        # TODO: Implement cron expression parsing
        # Options: croniter library or manual parser
        task = ScheduledTask(
            id=uuid.uuid4().hex[:12],
            description=description,
            schedule=cron_expr,
            task_type="cron",
            callback=callback,
            params=params or {},
        )
        self._tasks[task.id] = task
        self._save()
        return task

    def remind(self, description: str, minutes: int = 0,
               hours: int = 0, days: int = 0) -> ScheduledTask:
        """
        Set a reminder for the future.

        Args:
            description: What to be reminded about
            minutes: Minutes from now
            hours: Hours from now
            days: Days from now

        Returns:
            Created ScheduledTask
        """
        delta = timedelta(minutes=minutes, hours=hours, days=days)
        when = (datetime.now(timezone.utc) + delta).isoformat()
        return self.schedule_once(when, f"⏰ REMINDER: {description}")

    def due_tasks(self) -> List[ScheduledTask]:
        """Get tasks that are due to run now."""
        now = datetime.now(timezone.utc)
        due = []
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            if task.next_run:
                try:
                    run_time = datetime.fromisoformat(task.next_run)
                    if run_time.tzinfo is None:
                        run_time = run_time.replace(tzinfo=timezone.utc)
                    if run_time <= now:
                        due.append(task)
                except (ValueError, TypeError):
                    continue
        return due

    def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.CANCELLED
            self._save()
            return True
        return False

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[ScheduledTask]:
        """List scheduled tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.next_run or "")

    async def run_due(self) -> List[ScheduledTask]:
        """
        Execute all due tasks.

        Returns:
            List of executed tasks
        """
        # TODO: Implement actual execution
        # TODO: Integrate with nexus core for task routing
        raise NotImplementedError(
            "TaskScheduler.run_due() is a stub. Implementation:\n"
            "1. Get due_tasks()\n"
            "2. For each, execute callback or route to nexus core\n"
            "3. Update task status, increment run_count\n"
            "4. For cron tasks, calculate next_run\n"
            "5. Save state"
        )

    def summary(self) -> str:
        """Human-readable schedule summary."""
        pending = [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
        if not pending:
            return "No scheduled tasks."
        lines = [f"📋 {len(pending)} scheduled tasks:"]
        for t in pending[:10]:
            lines.append(f"  [{t.task_type}] {t.description} @ {t.next_run or t.schedule}")
        return "\n".join(lines)
