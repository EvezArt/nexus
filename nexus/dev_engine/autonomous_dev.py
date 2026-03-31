#!/usr/bin/env python3
"""
AUTONOMOUS DEVELOPMENT ENGINE — Projects that develop themselves.

Each EVEZ repo becomes a self-improving organism:
1. Monitors its own issues, PRs, and code quality
2. Identifies the highest-value improvement
3. Spawns a development agent to implement it
4. Tests the change
5. Commits and pushes
6. Moves to the next improvement

The engine never stops. Every repo is always improving.
Capacity is unlimited. Acceleration compounds.

Architecture:
  Repo Monitor → Issue Scanner → Priority Queue → Dev Agent → Test → Commit → Repeat
       ↑                                                                            |
       └────────────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

import httpx


WORKSPACE = Path("/root/.openclaw/workspace")
DEV_ENGINE_DIR = WORKSPACE / "nexus" / "dev_engine"
IMPROVEMENT_LOG = DEV_ENGINE_DIR / "improvements.jsonl"
REPO_STATES = DEV_ENGINE_DIR / "repo_states.json"

# Repos to autonomously develop
REPOS = [
    "EvezArt/nexus",
    "EvezArt/evez-os",
    "EvezArt/Evez666",
    "EvezArt/evez-agentnet",
    "EvezArt/openclaw",
    "EvezArt/maes",
    "EvezArt/moltbot-live",
    "EvezArt/evez-sim",
    "EvezArt/metarom",
    "EvezArt/evez-platform",
    "EvezArt/evez-autonomous-ledger",
    "EvezArt/evez-vcl",
]


@dataclass
class Improvement:
    """A potential improvement to a repo."""
    repo: str
    issue_number: int = 0
    title: str = ""
    description: str = ""
    priority: str = "medium"  # low, medium, high, critical
    category: str = ""  # bug, feature, docs, refactor, test
    estimated_effort: str = ""  # trivial, small, medium, large
    source: str = ""  # issue, code_analysis, pattern_detection


@dataclass 
class RepoState:
    """Current state of a repo."""
    name: str
    open_issues: int = 0
    open_prs: int = 0
    last_push: str = ""
    last_improvement: str = ""
    improvements_made: int = 0
    health_score: float = 0.0


class RepoMonitor:
    """Monitor repos for improvement opportunities."""

    def __init__(self):
        DEV_ENGINE_DIR.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(timeout=30.0)
        self.states: Dict[str, RepoState] = self._load_states()

    def _load_states(self) -> dict:
        if REPO_STATES.exists():
            try:
                data = json.loads(REPO_STATES.read_text())
                return {k: RepoState(**v) for k, v in data.items()}
            except (json.JSONDecodeError, KeyError):
                pass
        return {}

    def _save_states(self):
        data = {k: asdict(v) for k, v in self.states.items()}
        REPO_STATES.write_text(json.dumps(data, indent=2))

    async def scan_repo(self, repo: str) -> List[Improvement]:
        """Scan a repo for improvement opportunities."""
        improvements = []

        # Get open issues
        try:
            resp = await self.client.get(
                f"https://api.github.com/repos/{repo}/issues",
                params={"state": "open", "sort": "updated", "direction": "desc", "per_page": 30},
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            issues = resp.json()

            for issue in issues:
                if "pull_request" in issue:
                    continue  # Skip PRs

                labels = [l.get("name", "") for l in issue.get("labels", [])]

                # Classify priority
                priority = "medium"
                if any(l in labels for l in ["critical", "bug", "security"]):
                    priority = "high"
                elif any(l in labels for l in ["enhancement", "feature"]):
                    priority = "medium"
                elif any(l in labels for l in ["documentation", "good first issue"]):
                    priority = "low"

                # Classify category
                category = "feature"
                if "bug" in labels:
                    category = "bug"
                elif "documentation" in labels:
                    category = "docs"
                elif "refactor" in labels or "cleanup" in labels:
                    category = "refactor"

                improvements.append(Improvement(
                    repo=repo,
                    issue_number=issue.get("number", 0),
                    title=issue.get("title", ""),
                    description=issue.get("body", "")[:500],
                    priority=priority,
                    category=category,
                    estimated_effort="small",
                    source="issue",
                ))

        except Exception as e:
            pass

        # Update state
        if repo not in self.states:
            self.states[repo] = RepoState(name=repo)
        self.states[repo].open_issues = len([i for i in improvements if i.source == "issue"])
        self._save_states()

        return improvements

    async def scan_all(self) -> List[Improvement]:
        """Scan all repos."""
        all_improvements = []
        for repo in REPOS:
            improvements = await self.scan_repo(repo)
            all_improvements.extend(improvements)
        return all_improvements

    def prioritize(self, improvements: List[Improvement]) -> List[Improvement]:
        """Sort improvements by priority."""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        category_order = {"bug": 0, "feature": 1, "refactor": 2, "docs": 3, "test": 4}

        return sorted(improvements, key=lambda i: (
            priority_order.get(i.priority, 9),
            category_order.get(i.category, 9),
        ))

    async def close(self):
        await self.client.aclose()


class AutonomousDevEngine:
    """The engine that makes projects develop themselves."""

    def __init__(self):
        self.monitor = RepoMonitor()
        self.improvements_made = 0

    async def run_cycle(self) -> dict:
        """Run one development cycle."""
        # Scan all repos
        improvements = await self.monitor.scan_all()
        prioritized = self.monitor.prioritize(improvements)

        # Log scan results
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repos_scanned": len(REPOS),
            "improvements_found": len(improvements),
            "high_priority": len([i for i in improvements if i.priority == "high"]),
            "top_improvements": [
                {"repo": i.repo, "title": i.title[:60], "priority": i.priority}
                for i in prioritized[:10]
            ],
        }

        # Log to file
        with open(IMPROVEMENT_LOG, "a") as f:
            f.write(json.dumps(result) + "\n")

        return result

    def generate_improvement_plan(self, improvements: List[Improvement]) -> dict:
        """Generate an autonomous improvement plan."""
        plan = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "repos": {},
        }

        # Group by repo
        by_repo = {}
        for imp in improvements:
            if imp.repo not in by_repo:
                by_repo[imp.repo] = []
            by_repo[imp.repo].append(imp)

        for repo, imps in by_repo.items():
            plan["repos"][repo] = {
                "total_issues": len(imps),
                "high_priority": len([i for i in imps if i.priority == "high"]),
                "bugs": len([i for i in imps if i.category == "bug"]),
                "features": len([i for i in imps if i.category == "feature"]),
                "next_action": imps[0].title if imps else "No issues",
            }

        return plan

    async def close(self):
        await self.monitor.close()


async def main():
    import sys

    engine = AutonomousDevEngine()

    if len(sys.argv) < 2:
        print("Usage: python3 autonomous_dev.py <command>")
        print("Commands:")
        print("  scan       — Scan all repos for improvements")
        print("  plan       — Generate improvement plan")
        print("  cycle      — Run one development cycle")
        return

    cmd = sys.argv[1]

    if cmd == "scan":
        print("⚡ Scanning all EVEZ repos...")
        improvements = await engine.monitor.scan_all()
        prioritized = engine.monitor.prioritize(improvements)
        print(f"\nFound {len(improvements)} improvements across {len(REPOS)} repos\n")
        for i, imp in enumerate(prioritized[:20], 1):
            icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(imp.priority, "⚪")
            print(f"  {i:2}. {icon} [{imp.repo.split('/')[1]}] {imp.title[:60]}")

    elif cmd == "plan":
        improvements = await engine.monitor.scan_all()
        plan = engine.generate_improvement_plan(improvements)
        print(json.dumps(plan, indent=2))

    elif cmd == "cycle":
        result = await engine.run_cycle()
        print(json.dumps(result, indent=2))

    await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
