#!/usr/bin/env python3
"""
NEXUS TRAFFIC MESH — The inside-out infrastructure layer.

Captures, filters, and processes web traffic through the EVEZ ecosystem.
Every request becomes a cognition event. Every response feeds the spine.

Architecture:
  Internet Traffic → Nexus Proxy → Filter Chain → Processing
                                        ├── Spine (event log)
                                        ├── Memory (context)
                                        ├── Router (best provider)
                                        └── Revenue (monetize)

The mesh grows from the inside out:
  GitHub repos → Active nodes → Traffic capture → Pattern recognition → Revenue

Layer model:
  L1: Capture (proxy, scraper, webhook receiver)
  L2: Filter (classify, deduplicate, prioritize)  
  L3: Process (AI inference, pattern detection)
  L4: Output (actions, notifications, revenue)
  L5: Feedback (learn from outcomes, improve routing)
"""

from __future__ import annotations

import asyncio
import json
import hashlib
import time
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict

import httpx


WORKSPACE = Path("/root/.openclaw/workspace")
MESH_DIR = WORKSPACE / "nexus" / "mesh"
CAPTURE_LOG = MESH_DIR / "capture.jsonl"
FILTER_LOG = MESH_DIR / "filter.jsonl"
PATTERN_LOG = MESH_DIR / "patterns.jsonl"


# ---------------------------------------------------------------------------
# Layer 1: Capture — ingest web traffic
# ---------------------------------------------------------------------------

@dataclass
class TrafficEvent:
    """A single captured traffic event."""
    id: str
    timestamp: str
    source: str  # "proxy", "scraper", "webhook", "api", "browser"
    method: str  # GET, POST, etc.
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    response_code: int = 0
    response_body: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrafficCapture:
    """Layer 1: Capture web traffic from multiple sources."""

    def __init__(self):
        MESH_DIR.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.capture_count = 0

    async def capture_url(self, url: str, method: str = "GET",
                          headers: dict = None, body: str = "") -> TrafficEvent:
        """Capture a single HTTP request/response."""
        start = time.time()
        event_id = hashlib.sha256(
            f"{method}:{url}:{time.time()}".encode()
        ).hexdigest()[:12]

        try:
            resp = await self.client.request(
                method, url,
                headers=headers or {},
                content=body.encode() if body else None,
            )
            event = TrafficEvent(
                id=event_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                source="scraper",
                method=method,
                url=url,
                headers=dict(resp.headers),
                body=body,
                response_code=resp.status_code,
                response_body=resp.text[:10000],  # Cap at 10KB
                metadata={
                    "latency_ms": (time.time() - start) * 1000,
                    "content_type": resp.headers.get("content-type", ""),
                    "content_length": len(resp.text),
                },
            )
        except Exception as e:
            event = TrafficEvent(
                id=event_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                source="scraper",
                method=method,
                url=url,
                body=body,
                metadata={"error": str(e)},
            )

        self.capture_count += 1
        self._log_event(event)
        return event

    async def capture_batch(self, urls: List[str], method: str = "GET",
                            concurrency: int = 5) -> List[TrafficEvent]:
        """Capture multiple URLs concurrently."""
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_capture(url):
            async with semaphore:
                return await self.capture_url(url, method)

        tasks = [bounded_capture(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def capture_github_repo(self, owner: str, repo: str) -> TrafficEvent:
        """Capture GitHub repo metadata."""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        return await self.capture_url(url, headers={
            "Accept": "application/vnd.github.v3+json",
        })

    async def capture_github_activity(self, owner: str) -> List[TrafficEvent]:
        """Capture recent activity for a GitHub user."""
        events_url = f"https://api.github.com/users/{owner}/events/public"
        return [await self.capture_url(events_url)]

    def _log_event(self, event: TrafficEvent):
        """Log captured event to file."""
        with open(CAPTURE_LOG, "a") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    async def close(self):
        await self.client.aclose()


# ---------------------------------------------------------------------------
# Layer 2: Filter — classify and prioritize traffic
# ---------------------------------------------------------------------------

class TrafficFilter:
    """Layer 2: Filter, classify, and prioritize captured traffic."""

    # Classification patterns
    PATTERNS = {
        "opportunity": [
            r"bounty", r"grant", r"funding", r"hiring", r"freelance",
            r"earn", r"reward", r"prize", r"bug.*report", r"security",
        ],
        "signal": [
            r"launch", r"release", r"announce", r"update", r"new",
            r"trending", r"popular", r"viral", r"breaking",
        ],
        "threat": [
            r"vulnerability", r"exploit", r"breach", r"leak", r"hack",
            r"compromised", r"attack", r"malware",
        ],
        "revenue": [
            r"price", r"market", r"trading", r"invest", r"revenue",
            r"payment", r"subscription", r"api.*pricing",
        ],
        "intelligence": [
            r"research", r"paper", r"study", r"analysis", r"data",
            r"benchmark", r"comparison", r"review",
        ],
    }

    def __init__(self):
        MESH_DIR.mkdir(parents=True, exist_ok=True)

    def classify(self, event: TrafficEvent) -> dict:
        """Classify a traffic event into categories."""
        text = f"{event.url} {event.response_body[:1000]}".lower()

        scores = {}
        matched_patterns = {}

        for category, patterns in self.PATTERNS.items():
            score = 0
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text)
                if found:
                    score += len(found)
                    matches.extend(found)
            scores[category] = score
            if matches:
                matched_patterns[category] = matches

        primary = max(scores, key=scores.get) if any(scores.values()) else "uncategorized"

        result = {
            "event_id": event.id,
            "primary_category": primary,
            "scores": scores,
            "matched_patterns": matched_patterns,
            "priority": self._calculate_priority(scores, event),
            "actionable": scores.get("opportunity", 0) > 0 or scores.get("revenue", 0) > 0,
        }

        self._log_filter(result)
        return result

    def _calculate_priority(self, scores: dict, event: TrafficEvent) -> str:
        """Calculate priority level."""
        total = sum(scores.values())
        if total >= 5 or scores.get("opportunity", 0) >= 2:
            return "HIGH"
        elif total >= 2 or scores.get("signal", 0) >= 1:
            return "MEDIUM"
        return "LOW"

    def _log_filter(self, result: dict):
        """Log filter result."""
        with open(FILTER_LOG, "a") as f:
            f.write(json.dumps(result) + "\n")


# ---------------------------------------------------------------------------
# Layer 3: Process — AI inference and pattern detection
# ---------------------------------------------------------------------------

class TrafficProcessor:
    """Layer 3: Process filtered traffic through AI cognition."""

    def __init__(self):
        MESH_DIR.mkdir(parents=True, exist_ok=True)

    def detect_patterns(self, events: List[dict]) -> List[dict]:
        """Detect patterns across multiple filtered events."""
        patterns = []

        # Category frequency
        categories = {}
        for e in events:
            cat = e.get("primary_category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in categories.items():
            if count >= 3:
                patterns.append({
                    "type": "category_surge",
                    "category": cat,
                    "count": count,
                    "significance": "high" if count >= 5 else "medium",
                })

        # Priority distribution
        high_priority = sum(1 for e in events if e.get("priority") == "HIGH")
        if high_priority >= 3:
            patterns.append({
                "type": "high_priority_cluster",
                "count": high_priority,
                "significance": "high",
            })

        # Actionable items
        actionable = [e for e in events if e.get("actionable")]
        if actionable:
            patterns.append({
                "type": "actionable_items",
                "count": len(actionable),
                "event_ids": [e["event_id"] for e in actionable[:10]],
                "significance": "high",
            })

        # Log patterns
        for p in patterns:
            with open(PATTERN_LOG, "a") as f:
                f.write(json.dumps({
                    **p,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }) + "\n")

        return patterns


# ---------------------------------------------------------------------------
# Layer 4: Output — actions, notifications, revenue
# ---------------------------------------------------------------------------

class TrafficOutput:
    """Layer 4: Route processed traffic to actions."""

    def __init__(self):
        self.actions_taken = []

    async def dispatch(self, event: TrafficEvent, classification: dict,
                       processor_result: dict = None) -> dict:
        """Dispatch a classified event to appropriate action."""
        actions = []

        primary = classification.get("primary_category", "uncategorized")
        priority = classification.get("priority", "LOW")

        if primary == "opportunity" and priority == "HIGH":
            actions.append({
                "type": "alert",
                "channel": "telegram",
                "message": f"🎯 Opportunity detected: {event.url[:80]}",
            })

        if primary == "revenue":
            actions.append({
                "type": "log",
                "file": "revenue_signals.jsonl",
                "data": {"url": event.url, "classification": classification},
            })

        if primary == "threat":
            actions.append({
                "type": "alert",
                "channel": "telegram",
                "message": f"⚠️ Threat signal: {event.url[:80]}",
            })

        if classification.get("actionable"):
            actions.append({
                "type": "spine_event",
                "kind": "observation",
                "content": f"Actionable traffic: {primary} — {event.url[:100]}",
            })

        self.actions_taken.extend(actions)
        return {"event_id": event.id, "actions": actions}


# ---------------------------------------------------------------------------
# The Mesh — orchestrates all layers
# ---------------------------------------------------------------------------

class TrafficMesh:
    """The traffic mesh: capture → filter → process → output."""

    def __init__(self):
        self.capture = TrafficCapture()
        self.filter = TrafficFilter()
        self.processor = TrafficProcessor()
        self.output = TrafficOutput()

    async def ingest_url(self, url: str) -> dict:
        """Full pipeline: capture → filter → process → output."""
        # Layer 1: Capture
        event = await self.capture.capture_url(url)

        # Layer 2: Filter
        classification = self.filter.classify(event)

        # Layer 3: Process (single event — pattern detection needs batch)
        # Skip for single events

        # Layer 4: Output
        result = await self.output.dispatch(event, classification)

        return {
            "event_id": event.id,
            "url": url,
            "status_code": event.response_code,
            "classification": classification,
            "actions": result.get("actions", []),
        }

    async def ingest_batch(self, urls: List[str]) -> dict:
        """Batch pipeline with pattern detection."""
        # Layer 1: Capture
        events = await self.capture.capture_batch(urls)

        # Layer 2: Filter
        classifications = [self.filter.classify(e) for e in events
                          if isinstance(e, TrafficEvent)]

        # Layer 3: Process
        patterns = self.processor.detect_patterns(classifications)

        # Layer 4: Output
        results = []
        for event, classification in zip(
            [e for e in events if isinstance(e, TrafficEvent)],
            classifications
        ):
            result = await self.output.dispatch(event, classification)
            results.append(result)

        return {
            "events_captured": len(events),
            "patterns_detected": len(patterns),
            "actions_taken": len(self.output.actions_taken),
            "patterns": patterns,
            "high_priority": [
                c for c in classifications if c.get("priority") == "HIGH"
            ],
        }

    async def scan_evez_network(self) -> dict:
        """Scan the entire EVEZ GitHub network for signals."""
        urls = [
            "https://api.github.com/repos/EvezArt/nexus",
            "https://api.github.com/repos/EvezArt/evez-os",
            "https://api.github.com/repos/EvezArt/Evez666",
            "https://api.github.com/repos/EvezArt/evez-agentnet",
            "https://api.github.com/repos/EvezArt/openclaw",
            "https://api.github.com/repos/EvezArt/maes",
            "https://api.github.com/repos/EvezArt/moltbot-live",
            "https://api.github.com/repos/EvezArt/evez-sim",
            "https://api.github.com/repos/EvezArt/metarom",
            "https://api.github.com/repos/EvezArt/evez-platform",
            "https://api.github.com/users/EvezArt/events/public",
            "https://api.github.com/users/EvezArt/starred",
        ]

        return await self.ingest_batch(urls)

    async def close(self):
        await self.capture.close()


async def main():
    import sys

    mesh = TrafficMesh()

    if len(sys.argv) < 2:
        print("Usage: python3 traffic_mesh.py <command>")
        print("Commands:")
        print("  scan URL...      — Scan specific URLs")
        print("  network          — Scan EVEZ GitHub network")
        print("  patterns         — Show detected patterns")
        return

    cmd = sys.argv[1]

    if cmd == "scan" and len(sys.argv) >= 3:
        urls = sys.argv[2:]
        result = await mesh.ingest_batch(urls)
        print(json.dumps(result, indent=2))

    elif cmd == "network":
        print("⚡ Scanning EVEZ network...")
        result = await mesh.scan_evez_network()
        print(json.dumps(result, indent=2))

    elif cmd == "patterns":
        pattern_file = MESH_DIR / "patterns.jsonl"
        if pattern_file.exists():
            patterns = [json.loads(l) for l in pattern_file.read_text().splitlines() if l.strip()]
            print(f"Total patterns: {len(patterns)}")
            for p in patterns[-10:]:
                print(f"  [{p.get('timestamp', '?')[:16]}] {p.get('type')}: {p.get('significance')}")
        else:
            print("No patterns detected yet")

    await mesh.close()


if __name__ == "__main__":
    asyncio.run(main())
