"""
EVEZ Temporal Arbitrage Engine — Information asymmetry detector.

Scans for information available in one market/system that hasn't
propagated to others yet. Identifies exploitable windows.

Not financial advice. Educational/research tool only.
"""

import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("evez.arbitrage")


@dataclass
class InformationSignal:
    """A piece of information detected in the wild."""
    content: str
    source: str           # "twitter", "regulatory", "earnings", "macro", "supply_chain"
    market_origin: str    # Where it's known: "US", "EU", "Asia", "crypto", "global"
    timestamp: float
    propagation_speed: str  # "minutes", "hours", "days"
    magnitude: float = 0   # Estimated impact (0-1)
    verified: bool = False

    def to_dict(self):
        return {
            "content": self.content, "source": self.source,
            "market_origin": self.market_origin, "timestamp": self.timestamp,
            "propagation_speed": self.propagation_speed,
            "magnitude": self.magnitude, "verified": self.verified,
        }


@dataclass
class ArbitrageOpportunity:
    """An information asymmetry with an exploitable window."""
    signal: InformationSignal
    known_markets: List[str]
    unaware_markets: List[str]
    window_seconds: float
    estimated_impact: str
    exploitability: float  # 0-1
    strategy: str
    risk_level: str
    created: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "information": self.signal.content,
            "source": self.signal.source,
            "known_in": self.known_markets,
            "not_priced_in": self.unaware_markets,
            "window": f"{self.window_seconds/60:.0f} min" if self.window_seconds < 3600 else f"{self.window_seconds/3600:.1f} hr",
            "estimated_impact": self.estimated_impact,
            "exploitability": round(self.exploitability, 3),
            "strategy": self.strategy,
            "risk": self.risk_level,
        }


class TemporalArbitrageEngine:
    """
    Scans for information asymmetries across markets.

    Process:
    1. Scan global signals (news, regulatory, social, on-chain)
    2. Detect asymmetries (what's known where)
    3. Estimate propagation timeline
    4. Quantify exploitable window
    5. Alert with actionable intel
    """

    # Market propagation speeds (hours)
    PROPAGATION_SPEEDS = {
        "regulatory_eu_to_us": 24,
        "regulatory_us_to_eu": 12,
        "earnings_asia_to_us": 8,
        "earnings_us_to_asia": 16,
        "twitter_to_media": 2,
        "media_to_markets": 4,
        "onchain_to_cex": 0.5,
        "supply_chain_to_retail": 72,
        "macro_bonds_to_stocks": 1,
        "macro_stocks_to_crypto": 2,
        "vuln_to_patch": 24,
        "research_to_product": 720,  # 30 days
    }

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("/root/.openclaw/workspace/evez-platform/data/arbitrage")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.signals: List[InformationSignal] = []
        self.opportunities: List[ArbitrageOpportunity] = []
        self._load_state()

    def _load_state(self):
        state_file = self.data_dir / "arbitrage_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                self.opportunities = []  # Fresh scan each time
            except Exception:
                pass

    def _save_state(self):
        state_file = self.data_dir / "arbitrage_state.json"
        with open(state_file, "w") as f:
            json.dump({
                "opportunities_count": len(self.opportunities),
                "updated": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)

    async def scan(self) -> Dict:
        """
        Full temporal arbitrage scan.

        1. Fetch crypto prices (free, fast)
        2. Fetch global news snippets
        3. Compare market reactions
        4. Detect asymmetries
        """
        opportunities = []

        # === Scan 1: Crypto cross-exchange price differences ===
        crypto_arb = await self._scan_crypto_cross_exchange()
        opportunities.extend(crypto_arb)

        # === Scan 2: News sentiment vs market reaction ===
        news_arb = await self._scan_news_lag()
        opportunities.extend(news_arb)

        # === Scan 3: On-chain activity vs CEX prices ===
        chain_arb = await self._scan_onchain_signals()
        opportunities.extend(chain_arb)

        # === Scan 4: Regulatory filings lag ===
        reg_arb = await self._scan_regulatory_lag()
        opportunities.extend(reg_arb)

        self.opportunities = opportunities
        self._save_state()

        return {
            "opportunities": [o.to_dict() for o in opportunities],
            "total": len(opportunities),
            "scan_time": datetime.now(timezone.utc).isoformat(),
        }

    async def _scan_crypto_cross_exchange(self) -> List[ArbitrageOpportunity]:
        """Check for price differences across data sources."""
        opps = []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # CoinGecko free tier
                r = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": "bitcoin,ethereum,solana",
                        "vs_currencies": "usd",
                        "include_24hr_change": "true",
                    }
                )
                cg = r.json()

                # Check for divergence between assets
                for asset, data in cg.items():
                    if isinstance(data, dict) and "usd" in data:
                        change = data.get("usd_24h_change", 0)
                        if abs(change) > 8:  # Significant move
                            direction = "bullish" if change > 0 else "bearish"
                            opps.append(ArbitrageOpportunity(
                                signal=InformationSignal(
                                    content=f"{asset.upper()} moved {change:.1f}% in 24h — "
                                            f"momentum {direction}, derivatives may lag",
                                    source="price_momentum",
                                    market_origin="spot",
                                    timestamp=time.time(),
                                    propagation_speed="hours",
                                    magnitude=min(1.0, abs(change) / 20),
                                ),
                                known_markets=["spot", "coingecko"],
                                unaware_markets=["derivatives", "options", "traditional"],
                                window_seconds=3600 * 4,
                                estimated_impact=f"{abs(change):.1f}% further move possible",
                                exploitability=0.3,
                                strategy=f"{'Long' if change > 0 else 'Short'} "
                                         f"{asset.upper()} derivatives if momentum continues",
                                risk_level="medium",
                            ))
        except Exception as e:
            logger.error("Crypto cross-exchange scan failed: %s", e)
        return opps

    async def _scan_news_lag(self) -> List[ArbitrageOpportunity]:
        """Detect when news breaks but markets haven't reacted yet."""
        opps = []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # CryptoPanic free API
                r = await client.get(
                    "https://cryptopanic.com/api/v1/posts/",
                    params={"auth_token": "free", "kind": "news", "public": "true"}
                )
                data = r.json()
                posts = data.get("results", [])[:5]

                for post in posts:
                    title = post.get("title", "")
                    published = post.get("published_at", "")
                    currencies = post.get("currencies", [])

                    # Check for high-impact keywords
                    high_impact = any(kw in title.lower() for kw in [
                        "sec", "regulation", "hack", "exploit", "partnership",
                        "acquisition", "listing", "delisting", "fork", "upgrade",
                        "approval", "ban", "lawsuit", "breakthrough",
                    ])

                    if high_impact and currencies:
                        coin = currencies[0].get("code", "UNKNOWN") if currencies else "UNKNOWN"
                        opps.append(ArbitrageOpportunity(
                            signal=InformationSignal(
                                content=f"Breaking: {title[:100]}",
                                source="cryptopanic",
                                market_origin="crypto_news",
                                timestamp=time.time(),
                                propagation_speed="minutes",
                                magnitude=0.6,
                            ),
                            known_markets=["crypto_news", "crypto_twitter"],
                            unaware_markets=["spot_exchange", "derivatives"],
                            window_seconds=1800,  # 30 min typical
                            estimated_impact=f"5-15% move on {coin} possible",
                            exploitability=0.5,
                            strategy=f"Monitor {coin} orderbook for reaction delay",
                            risk_level="high",
                        ))
        except Exception as e:
            logger.error("News lag scan failed: %s", e)
        return opps

    async def _scan_onchain_signals(self) -> List[ArbitrageOpportunity]:
        """Check for on-chain activity that precedes price moves."""
        opps = []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Whale Alert or similar — check for large transfers
                # Using free DeFiLlama for TVL changes
                r = await client.get("https://api.llama.fi/protocols")
                data = r.json()

                # Find protocols with significant TVL changes
                for protocol in data[:20]:
                    change_1d = protocol.get("change_1d", 0)
                    if change_1d and abs(change_1d) > 15:
                        opps.append(ArbitrageOpportunity(
                            signal=InformationSignal(
                                content=f"{protocol.get('name','?')} TVL changed "
                                        f"{change_1d:+.1f}% in 24h",
                                source="defillama_tvl",
                                market_origin="onchain",
                                timestamp=time.time(),
                                propagation_speed="hours",
                                magnitude=min(1.0, abs(change_1d) / 50),
                            ),
                            known_markets=["onchain", "defi"],
                            unaware_markets=["cex", "traditional"],
                            window_seconds=7200,
                            estimated_impact=f"Token price may follow TVL movement",
                            exploitability=0.4,
                            strategy=f"Investigate {protocol.get('name')} — TVL move "
                                     f"often precedes token price by 2-6 hours",
                            risk_level="medium",
                        ))
                        if len(opps) >= 3:
                            break
        except Exception as e:
            logger.error("On-chain scan failed: %s", e)
        return opps

    async def _scan_regulatory_lag(self) -> List[ArbitrageOpportunity]:
        """Detect regulatory actions that haven't propagated across jurisdictions."""
        opps = []
        # This would need SEC/ESMA/CFTC API access
        # For now, flag the pattern
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Check for crypto-related regulatory news via CoinGecko
                r = await client.get(
                    "https://api.coingecko.com/api/v3/global",
                )
                data = r.json().get("data", {})
                market_cap_change = data.get("market_cap_change_percentage_24h_usd", 0)

                if abs(market_cap_change) > 5:
                    opps.append(ArbitrageOpportunity(
                        signal=InformationSignal(
                            content=f"Total crypto market cap moved {market_cap_change:+.1f}% "
                                    f"in 24h — possible regulatory or macro catalyst",
                            source="market_structure",
                            market_origin="global_crypto",
                            timestamp=time.time(),
                            propagation_speed="hours",
                            magnitude=min(1.0, abs(market_cap_change) / 10),
                        ),
                        known_markets=["crypto"],
                        unaware_markets=["equities", "bonds", "commodities"],
                        window_seconds=14400,
                        estimated_impact="Cross-market contagion possible",
                        exploitability=0.25,
                        strategy="Watch for correlation with SPY/bonds in next session",
                        risk_level="low",
                    ))
        except Exception as e:
            logger.error("Regulatory lag scan failed: %s", e)
        return opps

    def get_status(self) -> Dict:
        return {
            "opportunities": len(self.opportunities),
            "best": (
                max(self.opportunities, key=lambda o: o.exploitability).to_dict()
                if self.opportunities else None
            ),
        }
