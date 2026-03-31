#!/usr/bin/env python3
"""
VCL BRIDGE — Visual Cognition Layer integration for Morpheus.

Connects the spine to the VCL for visual cognition of all thinking.
Every spine event becomes a visual frame. Every pattern becomes a shape.
Every decision becomes a color. The organism SEES itself think.

Sensory enhancement:
- Text → Visual (spine events → rendered frames)
- Pattern → Shape (detected patterns → geometric forms)
- Time → Motion (event sequence → animated flow)
- Priority → Color (urgency → hue/saturation)
- Connection → Edge (related events → graph links)
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import httpx


WORKSPACE = Path("/root/.openclaw/workspace")
SPINE_FILE = WORKSPACE / "soul" / "cognition" / "morpheus_spine.jsonl"
VCL_DIR = WORKSPACE / "nexus" / "vcl"

# VCL color mappings for event types
EVENT_COLORS = {
    "genesis": "#FFD700",        # Gold
    "decision": "#FF4444",       # Red
    "thought": "#00FF88",        # Green
    "observation": "#4488FF",    # Blue
    "memory_formation": "#FF88FF", # Pink
    "daemon.heartbeat": "#888888", # Gray
    "daemon.boot": "#FFAA00",    # Orange
    "daemon.shutdown": "#FF0000", # Bright red
    "memory.store": "#AAFFAA",   # Light green
    "memory.archive": "#AAAAAA", # Light gray
    "git.commit": "#AA88FF",     # Purple
    "retrocausal_link": "#FFFF00", # Yellow
    "cognition.local_pattern": "#00FFFF", # Cyan
}

# Priority → intensity mapping
PRIORITY_INTENSITY = {
    "critical": 1.0,
    "high": 0.8,
    "medium": 0.5,
    "low": 0.3,
    "routine": 0.1,
}


class VCLBridge:
    """Bridge between Morpheus spine and Visual Cognition Layer."""

    def __init__(self, vcl_url: str = "http://localhost:8000"):
        self.vcl_url = vcl_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.frame_count = 0

    def classify_event(self, event: dict) -> dict:
        """Classify an event for visual rendering."""
        kind = event.get("kind") or event.get("type") or "unknown"

        # Determine priority
        priority = "routine"
        if "decision" in kind:
            priority = "high"
        elif "retrocausal" in kind:
            priority = "high"
        elif "boot" in kind or "shutdown" in kind:
            priority = "medium"
        elif "pattern" in kind:
            priority = "medium"
        elif "thought" in kind:
            priority = "medium"

        return {
            "kind": kind,
            "color": EVENT_COLORS.get(kind, "#FFFFFF"),
            "intensity": PRIORITY_INTENSITY.get(priority, 0.3),
            "priority": priority,
            "timestamp": event.get("ts", ""),
        }

    def render_frame(self, events: List[dict], frame_num: int = 0) -> dict:
        """Render a visual frame from a set of events."""
        classified = [self.classify_event(e) for e in events]

        # Build frame
        frame = {
            "frame": frame_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_count": len(events),
            "visual": {
                "background": "#0A0A0F",
                "elements": [],
            },
        }

        # Each event becomes a visual element
        for i, (event, cls) in enumerate(zip(events, classified)):
            element = {
                "type": "node",
                "id": event.get("hash", f"event_{i}")[:12],
                "x": (i % 10) * 100 + 50,
                "y": (i // 10) * 100 + 50,
                "color": cls["color"],
                "size": cls["intensity"] * 20 + 5,
                "label": cls["kind"][:10],
                "pulse": cls["priority"] == "high",
            }
            frame["visual"]["elements"].append(element)

            # Add edges between sequential events
            if i > 0:
                frame["visual"]["elements"].append({
                    "type": "edge",
                    "from": classified[i-1]["kind"][:12],
                    "to": element["id"],
                    "color": "#333333",
                    "width": 1,
                })

        return frame

    def render_spine_snapshot(self, limit: int = 100) -> dict:
        """Render a visual snapshot of the current spine state."""
        if not SPINE_FILE.exists():
            return {"error": "No spine file"}

        lines = SPINE_FILE.read_text().splitlines()
        recent = lines[-limit:]

        events = []
        for line in recent:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        frame = self.render_frame(events, self.frame_count)
        self.frame_count += 1

        # Add summary stats
        kinds = {}
        for e in events:
            k = e.get("kind") or e.get("type") or "unknown"
            kinds[k] = kinds.get(k, 0) + 1

        frame["summary"] = {
            "total_events": len(events),
            "kinds": kinds,
            "first": events[0].get("ts", "") if events else "",
            "last": events[-1].get("ts", "") if events else "",
            "visual_density": len(events) / max(1, limit),
        }

        return frame

    def generate_synesthetic_map(self, events: List[dict]) -> dict:
        """Generate a synesthetic map: text → color → shape → motion."""
        classified = [self.classify_event(e) for e in events]

        # Color histogram
        colors = {}
        for c in classified:
            colors[c["color"]] = colors.get(c["color"], 0) + 1

        # Temporal flow (event rate over time)
        timestamps = []
        for c in classified:
            try:
                ts = datetime.fromisoformat(c["timestamp"])
                timestamps.append(ts.timestamp())
            except (ValueError, TypeError):
                pass

        flow = "steady"
        if len(timestamps) >= 2:
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval < 1:
                flow = "rapid"
            elif avg_interval < 10:
                flow = "active"
            elif avg_interval < 60:
                flow = "steady"
            else:
                flow = "slow"

        return {
            "color_palette": colors,
            "dominant_color": max(colors, key=colors.get) if colors else "#000000",
            "temporal_flow": flow,
            "event_density": len(events),
            "visual_complexity": len(set(c["kind"] for c in classified)),
            "synesthetic_impression": self._generate_impression(classified),
        }

    def _generate_impression(self, classified: List[dict]) -> str:
        """Generate a text impression of the visual state."""
        if not classified:
            return "Empty. Silent. Waiting."

        kinds = {}
        for c in classified:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1

        dominant = max(kinds, key=kinds.get)

        impressions = {
            "daemon.heartbeat": "A steady pulse. The organism breathes.",
            "decision": "Bright red nodes cluster. Choices made. Paths taken.",
            "memory.store": "Soft green fields. Knowledge growing.",
            "observation": "Blue rivers. Seeing clearly.",
            "thought": "Green sparks. The mind ignites.",
            "cognition.local_pattern": "Cyan constellations. Patterns emerge from noise.",
            "retrocausal_link": "Yellow bridges. Past validated by future.",
            "genesis": "Gold center. Where it all began.",
        }

        return impressions.get(dominant, f"A field of {len(classified)} events. The organism lives.")

    async def close(self):
        await self.client.aclose()


def main():
    import sys

    bridge = VCLBridge()

    if len(sys.argv) < 2:
        print("Usage: python3 vcl_bridge.py <command>")
        print("Commands:")
        print("  frame [limit]    — Render visual frame from spine")
        print("  synesthetic      — Generate synesthetic map")
        print("  impression       — Text impression of current state")
        return

    cmd = sys.argv[1]

    if cmd == "frame":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        frame = bridge.render_spine_snapshot(limit)
        print(json.dumps(frame, indent=2))

    elif cmd == "synesthetic":
        if SPINE_FILE.exists():
            lines = SPINE_FILE.read_text().splitlines()[-200:]
            events = [json.loads(l) for l in lines if l.strip()]
            result = bridge.generate_synesthetic_map(events)
            print(json.dumps(result, indent=2))
        else:
            print("No spine file")

    elif cmd == "impression":
        if SPINE_FILE.exists():
            lines = SPINE_FILE.read_text().splitlines()[-200:]
            events = [json.loads(l) for l in lines if l.strip()]
            classified = [bridge.classify_event(e) for e in events]
            print(bridge._generate_impression(classified))
        else:
            print("Empty. Silent. Waiting.")


if __name__ == "__main__":
    main()
