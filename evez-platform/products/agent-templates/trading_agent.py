"""
EVEZ Trading Agent Template — Premium Preview

Autonomous market analysis agent that:
1. Monitors crypto/stock prices
2. Detects patterns and trends
3. Generates trade signals
4. Verifies through Invariance Battery
5. Alerts on high-confidence opportunities

This is the FREE preview. Premium version includes:
- Auto-execution (with user approval)
- Multi-chain DeFi yield optimization
- Portfolio rebalancing
- Risk management

Upgrade: github.com/sponsors/EvezArt (Blaze tier, $25/mo)
"""

import json
import sys
import time
import asyncio
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import EveZCore
from finance import FinancialEngine
from cognition import CognitiveEngine


class TradingAgent:
    """Autonomous trading agent (free preview: analysis only)."""

    def __init__(self):
        self.core = EveZCore(Path("/root/.openclaw/workspace/evez-platform/data/trading"))
        self.cognition = CognitiveEngine(self.core.spine)
        self.finance = FinancialEngine(self.core.spine, self.cognition)
        self.watchlist = ["bitcoin", "ethereum", "solana", "cardano", "polkadot"]

    async def analyze_market(self) -> dict:
        """Full market analysis with battery-verified signals."""
        print("📊 Market Analysis")
        print("=" * 50)

        # Observe
        print("\n1️⃣ Observing market...")
        observation = await self.finance.observe()

        for p in observation.get("prices", []):
            change = p["change_24h"]
            arrow = "🟢" if change > 0 else "🔴"
            print(f"   {arrow} {p['asset'].upper():>8}: ${p['price_usd']:>10,.2f} ({change:+.1f}%)")

        market = observation.get("market", {})
        print(f"\n   Market Cap: ${market.get('total_market_cap_usd', 0):,.0f}")
        print(f"   BTC Dominance: {market.get('btc_dominance', 0):.1f}%")

        # Analyze each asset
        print("\n2️⃣ Generating signals...")
        signals = []
        for asset in self.watchlist:
            signal = await self.finance.analyze(asset)
            if signal:
                signals.append(signal)
                icon = {"buy": "🟢", "sell": "🔴", "hold": "⚪"}.get(signal.action, "❓")
                verified = "✅" if signal.verified else "⚠️"
                print(f"   {icon} {asset.upper():>10}: {signal.action.upper():>4} "
                      f"(conf: {signal.confidence:.0%}, battery: {verified})")

        # Store results
        self.core.spine.write("trading.analysis", {
            "assets_analyzed": len(signals),
            "buy_signals": sum(1 for s in signals if s.action == "buy"),
            "sell_signals": sum(1 for s in signals if s.action == "sell"),
            "verified": sum(1 for s in signals if s.verified),
        }, tags=["trading", "analysis"])

        return {
            "observation": observation,
            "signals": [s.to_dict() for s in signals],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def monitor(self, interval_minutes: int = 60, max_cycles: int = 24):
        """Continuous monitoring loop."""
        print(f"👁️ Starting monitoring (every {interval_minutes}min, {max_cycles} cycles)")
        print()

        for cycle in range(1, max_cycles + 1):
            print(f"\n--- Cycle {cycle}/{max_cycles} ---")
            result = await self.analyze_market()

            # Check for high-confidence signals
            signals = result.get("signals", [])
            for s in signals:
                if s.get("confidence", 0) > 0.7 and s.get("verified"):
                    print(f"\n🚨 HIGH CONFIDENCE: {s['asset'].upper()} {s['action'].upper()}")
                    print(f"   Reasoning: {s['reasoning']}")

            if cycle < max_cycles:
                print(f"\n⏳ Next cycle in {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)


async def main():
    agent = TradingAgent()
    result = await agent.analyze_market()

    # Save
    with open("trading_analysis.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 Saved to trading_analysis.json")


if __name__ == "__main__":
    asyncio.run(main())
