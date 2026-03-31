"""
EVEZ Access Layer — Read-only façade over existing core.

Exposes snapshot, subscription, and accessor APIs without mutating state.
Other agents, dashboards, and external systems access through this layer.
"""

import json
import time
import threading
import queue
from pathlib import Path
from typing import List, Callable, Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict


@dataclass
class FireEvent:
    """Immutable cognitive event for external consumption."""
    n: int
    tau: int
    omega: int
    fire_score: float
    ts: float
    source: str = "core"
    metadata: Dict[str, Any] = None

    def to_dict(self):
        d = asdict(self)
        if d["metadata"] is None:
            d["metadata"] = {}
        return d


class EveZAccess:
    """
    Read-only access layer. Never mutates core state.
    Supports: snapshots, live subscriptions, pure accessors.
    """

    def __init__(self, spine=None, memory=None, cognition=None):
        self._spine = spine
        self._memory = memory
        self._cognition = cognition
        self._subscribers: List[Callable[[dict], None]] = []
        self._event_buffer: List[dict] = []
        self._max_buffer = 10000
        self._lock = threading.Lock()

    # --- Subscription interface ---

    def subscribe(self, callback: Callable[[dict], None]):
        """Register a callback for live events. Thread-safe."""
        with self._lock:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[dict], None]):
        """Remove a subscriber."""
        with self._lock:
            self._subscribers = [s for s in self._subscribers if s is not callback]

    def publish(self, event: dict):
        """Internal: push event to all subscribers and buffer."""
        with self._lock:
            self._event_buffer.append(event)
            if len(self._event_buffer) > self._max_buffer:
                self._event_buffer = self._event_buffer[-self._max_buffer:]
            subs = list(self._subscribers)
        for cb in subs:
            try:
                cb(event)
            except Exception:
                pass

    # --- Snapshot interface ---

    def snapshot(self, limit: int = 100) -> List[dict]:
        """Return immutable copy of most recent events."""
        with self._lock:
            return list(self._event_buffer[-limit:])

    def snapshot_spine(self, limit: int = 50) -> List[dict]:
        """Read-only spine snapshot."""
        if self._spine:
            return self._spine.read_recent(limit)
        return []

    def snapshot_memory(self) -> List[dict]:
        """Read-only memory snapshot."""
        if self._memory:
            return [
                {"key": m.key, "content": m.content[:200], "strength": m.strength, "tags": m.tags}
                for m in self._memory.strongest(20)
            ]
        return []

    # --- Pure accessors (no side effects) ---

    def spine_search(self, query: str, n: int = 20) -> List[dict]:
        if self._spine:
            return self._spine.search(query, n)
        return []

    def memory_search(self, query: str, n: int = 5) -> List[dict]:
        if self._memory:
            return [
                {"key": m.key, "content": m.content[:200], "strength": m.strength}
                for m in self._memory.search(query, n)
            ]
        return []

    def cognition_state(self) -> dict:
        if self._cognition:
            return self._cognition.get_state()
        return {"status": "no cognition engine"}

    # --- FIRE-style numeric accessor ---
    # Pure functions over integers — never mutate state

    @staticmethod
    def tau(n: int) -> int:
        """Divisor count τ(n)."""
        if n < 1:
            return 0
        count = 0
        i = 1
        while i * i <= n:
            if n % i == 0:
                count += 1
                if i != n // i:
                    count += 1
            i += 1
        return count

    @staticmethod
    def omega(n: int) -> int:
        """Distinct prime factor count ω(n)."""
        if n < 2:
            return 0
        count = 0
        d = 2
        temp = n
        while d * d <= temp:
            if temp % d == 0:
                count += 1
                while temp % d == 0:
                    temp //= d
            d += 1
        if temp > 1:
            count += 1
        return count

    @staticmethod
    def fire(n: int, tau_w: float = 1.0, omega_w: float = 1.0,
             serendipity: float = 0.2) -> float:
        """FIRE score: weighted combination of τ and ω with serendipity."""
        t = EveZAccess.tau(n)
        o = EveZAccess.omega(n)
        import math
        base = tau_w * math.log2(t + 1) + omega_w * math.log2(o + 1)
        serendip = serendipity * math.sin(n * 0.1) * math.log2(n + 1)
        return base + serendip

    def fire_window(self, start: int, end: int, limit: int = 1000) -> List[dict]:
        """Compute FIRE scores over a window of integers."""
        results = []
        for n in range(max(1, start), min(end, start + limit)):
            results.append({
                "n": n,
                "tau": self.tau(n),
                "omega": self.omega(n),
                "fire": self.fire(n),
            })
        return results

    def top_omega(self, start: int, end: int, limit: int = 20) -> List[Tuple[int, int]]:
        """Top n by ω(n) in a range."""
        scored = [(n, self.omega(n)) for n in range(max(2, start), end)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def get_status(self) -> dict:
        return {
            "subscribers": len(self._subscribers),
            "buffered_events": len(self._event_buffer),
            "spine_available": self._spine is not None,
            "memory_available": self._memory is not None,
            "cognition_available": self._cognition is not None,
        }
