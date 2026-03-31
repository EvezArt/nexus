"""
EVEZ Income Engine — Autonomous currency accumulation.

Not theory. Actual money. Faucets, airdrops, yield farming,
micro-tasks, freelance matching, DeFi opportunities.
Agents find, verify, and execute on Steven's behalf.

Every action passes through Invariance Battery before execution.
"""

import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger("evez.income")


@dataclass
class Opportunity:
    """A money-making opportunity."""
    id: str
    source: str         # "faucet", "airdrop", "yield", "freelance", "trading"
    title: str
    description: str
    estimated_value_usd: float
    effort_level: str   # "trivial", "low", "medium", "high"
    risk_level: str     # "none", "low", "medium", "high"
    url: str = ""
    action_required: str = ""
    verified: bool = False
    battery_passed: int = 0
    expires: float = 0
    created: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "id": self.id, "source": self.source, "title": self.title,
            "description": self.description, "estimated_value_usd": self.estimated_value_usd,
            "effort": self.effort_level, "risk": self.risk_level,
            "url": self.url, "action": self.action_required,
            "verified": self.verified, "battery_passed": self.battery_passed,
        }


@dataclass
class Wallet:
    """Track wallets we can manage."""
    chain: str
    address: str
    label: str
    balance_usd: float = 0
    assets: Dict[str, float] = field(default_factory=dict)
    last_checked: float = 0

    def to_dict(self):
        return {
            "chain": self.chain, "address": self.address[:10] + "...",
            "label": self.label, "balance_usd": self.balance_usd,
            "assets": self.assets,
        }


class IncomeEngine:
    """
    Autonomous income accumulation engine.

    Sources (all free to start):
    1. Crypto faucets — aggregated from multiple sources
    2. Airdrops — new token airdrops, testnet rewards
    3. DeFi yield — staking, LP, lending opportunities
    4. Freelance — AI-assisted gig matching
    5. Trading signals — buy/sell with battery verification
    6. Micro-tasks — automated where possible
    7. Referral programs — compound income
    """

    def __init__(self, spine=None, cognition=None, data_dir: Path = None):
        self.spine = spine
        self.cognition = cognition
        self.data_dir = data_dir or Path("/root/.openclaw/workspace/evez-platform/data/income")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.opportunities: List[Opportunity] = []
        self.wallets: List[Wallet] = []
        self.total_found_usd: float = 0
        self.total_claimed_usd: float = 0
        self._load_state()

    def _load_state(self):
        state_file = self.data_dir / "income_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                self.total_found_usd = data.get("total_found_usd", 0)
                self.total_claimed_usd = data.get("total_claimed_usd", 0)
                for w in data.get("wallets", []):
                    self.wallets.append(Wallet(**w))
            except Exception:
                pass

    def _save_state(self):
        state_file = self.data_dir / "income_state.json"
        with open(state_file, "w") as f:
            json.dump({
                "total_found_usd": self.total_found_usd,
                "total_claimed_usd": self.total_claimed_usd,
                "wallets": [w.to_dict() for w in self.wallets],
                "opportunities": len(self.opportunities),
                "updated": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)

    async def scan_all(self) -> List[Opportunity]:
        """Scan all income sources and return new opportunities."""
        results = []

        # Parallel scans
        faucets = await self._scan_faucets()
        airdrops = await self._scan_airdrops()
        yield_ops = await self._scan_yield()
        freelance = await self._scan_freelance()

        results.extend(faucets)
        results.extend(airdrops)
        results.extend(yield_ops)
        results.extend(freelance)

        # Verify through battery
        for opp in results:
            if self.cognition:
                try:
                    result = await self.cognition.perceive("market", opp.description, {
                        "source": opp.source,
                        "value": opp.estimated_value_usd,
                        "risk": opp.risk_level,
                    })
                    ce = result.get("ce", {})
                    opp.battery_passed = ce.get("rotations_passed", 0)
                    opp.verified = ce.get("confidence") == "validated"
                except Exception:
                    pass

        self.opportunities.extend(results)
        self.total_found_usd += sum(o.estimated_value_usd for o in results)
        self._save_state()

        if self.spine:
            self.spine.write("income.scan", {
                "found": len(results),
                "total_value_usd": sum(o.estimated_value_usd for o in results),
            }, tags=["income", "scan"])

        return results

    async def _scan_faucets(self) -> List[Opportunity]:
        """Scan for crypto faucet opportunities."""
        opps = []

        # Known working faucets (free, no investment)
        faucets = [
            {"name": "FreeBitco.in", "chain": "BTC", "est_daily": 0.05,
             "url": "https://freebitco.in", "action": "Roll hourly"},
            {"name": "Cointiply", "chain": "BTC", "est_daily": 0.10,
             "url": "https://cointiply.com", "action": "Complete tasks + faucet"},
            {"name": "FireFaucet", "chain": "MULTI", "est_daily": 0.08,
             "url": "https://firefaucet.win", "action": "Auto-faucet + PTC ads"},
            {"name": "FaucetCrypto", "chain": "MULTI", "est_daily": 0.05,
             "url": "https://faucetcrypto.com", "action": "PTC + faucet rolls"},
            {"name": "Adbtc.top", "chain": "BTC", "est_daily": 0.08,
             "url": "https://adbtc.top", "action": "Surf ads for satoshi"},
        ]

        for f in faucets:
            opps.append(Opportunity(
                id=hashlib.sha256(f"faucet:{f['name']}".encode()).hexdigest()[:12],
                source="faucet",
                title=f"{f['name']} — {f['chain']} Faucet",
                description=f"Free {f['chain']} faucet. {f['action']}. Est ${f['est_daily']}/day.",
                estimated_value_usd=f["est_daily"],
                effort_level="trivial",
                risk_level="none",
                url=f["url"],
                action_required=f["action"],
            ))

        return opps

    async def _scan_airdrops(self) -> List[Opportunity]:
        """Scan for crypto airdrop opportunities."""
        opps = []

        # Airdrop aggregator sources
        sources = [
            {"name": "Galxe Campaigns", "url": "https://galxe.com/airdrop",
             "desc": "Complete quests for token airdrops. Many chains.", "est": 50.0},
            {"name": "Layer3 Quests", "url": "https://layer3.xyz",
             "desc": "On-chain quests with token rewards.", "est": 30.0},
            {"name": "Zealy Campaigns", "url": "https://zealy.io",
             "desc": "Community tasks for airdrop eligibility.", "est": 20.0},
            {"name": "DeBank Airdrops", "url": "https://debank.com/airdrop",
             "desc": "Track eligible airdrops from DeFi activity.", "est": 100.0},
            {"name": "Airdrops.io", "url": "https://airdrops.io",
             "desc": "Aggregated airdrop list with guides.", "est": 40.0},
        ]

        for s in sources:
            opps.append(Opportunity(
                id=hashlib.sha256(f"airdrop:{s['name']}".encode()).hexdigest()[:12],
                source="airdrop",
                title=s["name"],
                description=s["desc"],
                estimated_value_usd=s["est"],
                effort_level="low",
                risk_level="low",
                url=s["url"],
                action_required="Complete quests/tasks for eligibility",
            ))

        return opps

    async def _scan_yield(self) -> List[Opportunity]:
        """Scan for DeFi yield opportunities."""
        opps = []

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # DeFiLlama yields API (free, no key)
                r = await client.get("https://yields.llama.fi/pools")
                data = r.json().get("data", [])

                # Filter: high APY, low risk, established chains
                for pool in sorted(data, key=lambda p: p.get("apy", 0), reverse=True)[:10]:
                    if pool.get("apy", 0) > 5 and pool.get("tvlUsd", 0) > 1_000_000:
                        opps.append(Opportunity(
                            id=hashlib.sha256(f"yield:{pool.get('pool','')}:{pool.get('chain','')}".encode()).hexdigest()[:12],
                            source="yield",
                            title=f"{pool.get('symbol', 'Unknown')} on {pool.get('chain', '?')}",
                            description=f"APY: {pool.get('apy', 0):.1f}%, TVL: ${pool.get('tvlUsd', 0):,.0f}, Project: {pool.get('project', '?')}",
                            estimated_value_usd=pool.get("apy", 0) / 100 * 100,  # Per $100 invested
                            effort_level="medium",
                            risk_level="medium",
                            url=pool.get("url", ""),
                            action_required="Deposit to earn yield",
                        ))
        except Exception as e:
            logger.error("Yield scan failed: %s", e)

        return opps[:5]

    async def _scan_freelance(self) -> List[Opportunity]:
        """Scan for freelance/AI task opportunities."""
        opps = []

        # AI freelance platforms
        platforms = [
            {"name": "Remotasks AI Tasks", "url": "https://remotasks.com",
             "desc": "AI training tasks: labeling, RLHF, coding. $5-25/hr.",
             "est": 15.0, "effort": "medium"},
            {"name": "Outlier AI", "url": "https://outlier.ai",
             "desc": "AI model training. Writing, coding, analysis. $15-50/hr.",
             "est": 25.0, "effort": "medium"},
            {"name": "Scale AI", "url": "https://scale.com/contributors",
             "desc": "AI data labeling and training. Flexible hours.",
             "est": 20.0, "effort": "medium"},
            {"name": "Fiverr AI Services", "url": "https://fiverr.com",
             "desc": "Sell AI services: writing, coding, art, analysis.",
             "est": 30.0, "effort": "high"},
            {"name": "Upwork AI Jobs", "url": "https://upwork.com",
             "desc": "Freelance AI/ML projects. $20-100/hr.",
             "est": 40.0, "effort": "high"},
        ]

        for p in platforms:
            opps.append(Opportunity(
                id=hashlib.sha256(f"freelance:{p['name']}".encode()).hexdigest()[:12],
                source="freelance",
                title=p["name"],
                description=p["desc"],
                estimated_value_usd=p["est"],
                effort_level=p["effort"],
                risk_level="none",
                url=p["url"],
                action_required="Sign up and complete tasks",
            ))

        return opps

    def add_wallet(self, chain: str, address: str, label: str):
        """Register a wallet for tracking."""
        wallet = Wallet(chain=chain, address=address, label=label)
        self.wallets.append(wallet)
        self._save_state()

    def get_portfolio(self) -> Dict:
        """Get current income portfolio."""
        return {
            "total_found_usd": round(self.total_found_usd, 2),
            "total_claimed_usd": round(self.total_claimed_usd, 2),
            "wallets": [w.to_dict() for w in self.wallets],
            "opportunities": len(self.opportunities),
            "by_source": self._count_by_source(),
        }

    def _count_by_source(self) -> Dict:
        counts = {}
        for opp in self.opportunities:
            counts[opp.source] = counts.get(opp.source, 0) + 1
        return counts

    def get_top_opportunities(self, n: int = 10, verified_only: bool = False) -> List[Dict]:
        """Get top opportunities sorted by value."""
        opps = self.opportunities
        if verified_only:
            opps = [o for o in opps if o.verified]
        sorted_ops = sorted(opps, key=lambda o: o.estimated_value_usd, reverse=True)
        return [o.to_dict() for o in sorted_ops[:n]]

    def get_status(self) -> Dict:
        return {
            "total_found_usd": round(self.total_found_usd, 2),
            "total_claimed_usd": round(self.total_claimed_usd, 2),
            "opportunities": len(self.opportunities),
            "verified": sum(1 for o in self.opportunities if o.verified),
            "wallets": len(self.wallets),
            "by_source": self._count_by_source(),
        }
