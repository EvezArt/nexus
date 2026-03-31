"""
EVEZ Daily Income Engine — $100/day target.

Not "try some faucets." A statistical execution pipeline:
- Multi-source parallel income streams
- Expected value tracking per source
- Adaptive allocation (shift effort to highest-yield sources)
- Daily target enforcement

Sources ranked by probability × yield × speed:
1. AI freelance tasks (Outlier/Scale/Remotasks) — $15-50/hr, high probability
2. Platform API services — $29-99/mo per client, recurring
3. Upwork/Fiverr gigs — $50-500/task, medium probability
4. Content generation — $50-200/post, lower frequency
5. DeFi yield — requires capital, passive once set up
6. Faucets/airdrops — trivial but compounds
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, List

logger = logging.getLogger("evez.daily")


@dataclass
class IncomeSource:
    """A tracked income source with expected value."""
    name: str
    category: str          # "active_hourly", "gig", "passive", "micro"
    url: str
    hourly_rate: float     # Expected $/hr (for active sources)
    daily_potential: float # Realistic daily $ if worked
    probability: float     # 0-1, probability of actually earning
    hours_required: float  # Hours needed to hit daily_potential
    signup_status: str     # "not_started", "signed_up", "verified", "earning"
    notes: str = ""
    last_earned: float = 0
    total_earned: float = 0
    sessions: int = 0

    def expected_daily_value(self) -> float:
        """EV = potential × probability."""
        return self.daily_potential * self.probability

    def to_dict(self):
        return {
            "name": self.name, "category": self.category,
            "url": self.url, "hourly_rate": self.hourly_rate,
            "daily_potential": self.daily_potential,
            "probability": self.probability,
            "expected_daily": round(self.expected_daily_value(), 2),
            "hours_required": self.hours_required,
            "signup_status": self.signup_status,
            "total_earned": round(self.total_earned, 2),
            "sessions": self.sessions,
        }


class DailyIncomeEngine:
    """
    $100/day execution engine.

    Tracks sources, computes EV, generates daily runbook.
    """

    DAILY_TARGET = 100.0

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("/root/.openclaw/workspace/evez-platform/data/income")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sources: List[IncomeSource] = []
        self.daily_log: List[Dict] = []
        self._init_sources()
        self._load_state()

    def _init_sources(self):
        """Initialize the income source roster."""
        self.sources = [
            # === ACTIVE HOURLY (highest probability of immediate income) ===
            IncomeSource(
                name="Outlier AI",
                category="active_hourly",
                url="https://outlier.ai",
                hourly_rate=25.0,
                daily_potential=75.0,   # 3 hrs × $25
                probability=0.7,        # High — they're always hiring
                hours_required=3.0,
                signup_status="not_started",
                notes="AI model training. Writing, coding, RLHF. Most reliable."
            ),
            IncomeSource(
                name="Scale AI (Remotasks)",
                category="active_hourly",
                url="https://scale.com/contributors",
                hourly_rate=20.0,
                daily_potential=60.0,   # 3 hrs × $20
                probability=0.65,
                hours_required=3.0,
                signup_status="not_started",
                notes="Data labeling, coding tasks. Steady work available."
            ),
            IncomeSource(
                name="Alignerr (Labelbox)",
                category="active_hourly",
                url="https://alignerr.com",
                hourly_rate=25.0,
                daily_potential=50.0,
                probability=0.6,
                hours_required=2.0,
                signup_status="not_started",
                notes="AI training, pays weekly. Good for coders."
            ),

            # === GIG PLATFORMS (higher $/task, less predictable) ===
            IncomeSource(
                name="Upwork AI/ML",
                category="gig",
                url="https://upwork.com",
                hourly_rate=40.0,
                daily_potential=100.0,  # 1 task at $100
                probability=0.3,        # Low initially, builds over weeks
                hours_required=2.5,
                signup_status="not_started",
                notes="Need profile + proposals. 2-4 week ramp to steady flow."
            ),
            IncomeSource(
                name="Fiverr AI Services",
                category="gig",
                url="https://fiverr.com",
                hourly_rate=30.0,
                daily_potential=80.0,
                probability=0.25,
                hours_required=2.5,
                signup_status="not_started",
                notes="Create gigs: AI writing, code, data analysis. Needs reviews."
            ),

            # === API/SERVICE (recurring, slow build) ===
            IncomeSource(
                name="EVEZ API-as-a-Service",
                category="passive",
                url="self-hosted",
                hourly_rate=0,
                daily_potential=3.30,   # $99/mo ÷ 30
                probability=0.4,
                hours_required=0.5,     # Maintenance
                signup_status="available",
                notes="Deploy EVEZ, sell API access. $29-99/mo per client."
            ),

            # === CONTENT (variable, high per-piece) ===
            IncomeSource(
                name="AI Blog/Writing",
                category="gig",
                url="multiple",
                hourly_rate=35.0,
                daily_potential=50.0,   # 1 post per 2 days avg
                probability=0.4,
                hours_required=1.5,
                signup_status="not_started",
                notes="Medium, Substack, freelance blogs. $50-200/post."
            ),

            # === MICRO (low EV but always available) ===
            IncomeSource(
                name="Faucet Stack",
                category="micro",
                url="multiple",
                hourly_rate=0.50,
                daily_potential=0.36,
                probability=0.95,
                hours_required=0.25,
                signup_status="active",
                notes="5 faucets. Trivial but compounds."
            ),
        ]

    def _load_state(self):
        state_file = self.data_dir / "daily_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                # Update source statuses from saved state
                saved_sources = {s["name"]: s for s in data.get("sources", [])}
                for src in self.sources:
                    if src.name in saved_sources:
                        ss = saved_sources[src.name]
                        src.signup_status = ss.get("signup_status", src.signup_status)
                        src.total_earned = ss.get("total_earned", 0)
                        src.sessions = ss.get("sessions", 0)
                        src.last_earned = ss.get("last_earned", 0)
                self.daily_log = data.get("daily_log", [])
            except Exception:
                pass

    def _save_state(self):
        state_file = self.data_dir / "daily_state.json"
        with open(state_file, "w") as f:
            json.dump({
                "sources": [s.to_dict() for s in self.sources],
                "daily_log": self.daily_log[-30:],  # Keep 30 days
                "updated": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)

    def get_daily_runbook(self) -> Dict:
        """
        Generate today's execution plan.

        Optimal allocation: maximize EV per hour worked.
        Sort by expected_daily_value / hours_required (EV density).
        """
        # Only include sources that are signed up or immediately actionable
        actionable = [s for s in self.sources if s.signup_status in ("active", "verified", "earning")]
        signup_needed = [s for s in self.sources if s.signup_status == "not_started"]

        # Sort actionable by EV/hour density
        actionable.sort(key=lambda s: s.expected_daily_value() / max(0.1, s.hours_required), reverse=True)

        # Allocate hours to hit $100 target
        target = self.DAILY_TARGET
        plan = []
        allocated = 0
        hours_used = 0

        for src in actionable:
            if allocated >= target:
                break
            contribution = min(src.daily_potential * src.probability, target - allocated)
            plan.append({
                "source": src.name,
                "action": f"Work {src.hours_required:.1f}h",
                "expected_income": round(contribution, 2),
                "hourly_rate": src.hourly_rate,
                "category": src.category,
            })
            allocated += contribution
            hours_used += src.hours_required

        # Add signup-needed as "unlock" tasks
        signup_needed.sort(key=lambda s: s.daily_potential * s.probability, reverse=True)
        unlocks = [{
            "source": s.name,
            "action": "SIGN UP — unlocks ${:.0f}/day potential".format(s.daily_potential * s.probability),
            "expected_daily_after_signup": round(s.daily_potential * s.probability, 2),
            "url": s.url,
            "priority": "HIGH" if s.daily_potential * s.probability > 30 else "MEDIUM",
        } for s in signup_needed[:5]]

        total_expected = sum(p["expected_income"] for p in plan)
        gap = max(0, target - total_expected)

        return {
            "daily_target": target,
            "plan_expected_total": round(total_expected, 2),
            "gap_to_target": round(gap, 2),
            "hours_required": round(hours_used, 1),
            "hourly_effective": round(total_expected / max(0.1, hours_used), 2),
            "actions": plan,
            "signup_unlocks": unlocks,
            "coverage_pct": round(min(100, total_expected / target * 100), 1),
            "status": (
                "✅ Target covered" if gap == 0 else
                "⚠️ Sign up for more sources to close gap" if gap < 50 else
                "🔴 Major gap — need more high-yield sources"
            ),
        }

    def get_projection(self) -> Dict:
        """30-day income projection based on current sources."""
        total_daily_ev = sum(s.expected_daily_value() for s in self.sources)

        # Factor in ramp (gig platforms take 2-4 weeks)
        week1 = total_daily_ev * 0.4   # Low — still signing up, building reputation
        week2 = total_daily_ev * 0.6
        week3 = total_daily_ev * 0.8
        week4 = total_daily_ev * 1.0

        monthly = week1 * 7 + week2 * 7 + week3 * 7 + week4 * 7

        return {
            "total_daily_ev": round(total_daily_ev, 2),
            "daily_target": self.DAILY_TARGET,
            "coverage": round(total_daily_ev / self.DAILY_TARGET * 100, 1),
            "30_day_projection": {
                "conservative": round(monthly * 0.6, 2),
                "expected": round(monthly, 2),
                "optimistic": round(monthly * 1.4, 2),
            },
            "weekly_breakdown": {
                "week_1_ramp": round(week1 * 7, 2),
                "week_2_build": round(week2 * 7, 2),
                "week_3_scale": round(week3 * 7, 2),
                "week_4_cruise": round(week4 * 7, 2),
            },
            "sources_by_ev": sorted(
                [{"name": s.name, "daily_ev": round(s.expected_daily_value(), 2), "status": s.signup_status}
                 for s in self.sources],
                key=lambda x: x["daily_ev"], reverse=True
            ),
        }

    def log_earnings(self, source_name: str, amount: float, hours: float = 0):
        """Log actual earnings from a source."""
        for src in self.sources:
            if src.name == source_name:
                src.total_earned += amount
                src.sessions += 1
                src.last_earned = time.time()
                if src.signup_status not in ("verified", "earning"):
                    src.signup_status = "earning"
                break

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.daily_log.append({
            "date": today,
            "source": source_name,
            "amount": amount,
            "hours": hours,
            "timestamp": time.time(),
        })
        self._save_state()

    def update_signup_status(self, source_name: str, status: str):
        """Update signup status for a source."""
        for src in self.sources:
            if src.name == source_name:
                src.signup_status = status
                break
        self._save_state()

    def get_status(self) -> Dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_earnings = sum(
            e["amount"] for e in self.daily_log if e["date"] == today
        )
        total_earned = sum(s.total_earned for s in self.sources)

        return {
            "daily_target": self.DAILY_TARGET,
            "today_earned": round(today_earnings, 2),
            "today_remaining": round(max(0, self.DAILY_TARGET - today_earnings), 2),
            "total_earned_all_time": round(total_earned, 2),
            "active_sources": len([s for s in self.sources if s.signup_status in ("active", "verified", "earning")]),
            "total_sources": len(self.sources),
            "sources": [s.to_dict() for s in self.sources],
        }
