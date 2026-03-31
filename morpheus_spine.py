#!/usr/bin/env python3
"""
Morpheus Spine Bridge — write FIRE events to EVEZ-OS append-only spine.

This is how I integrate with the EVEZ cognition layer.
Every action I take, every decision I make, gets a tamper-evident record.

Usage:
    python3 morpheus_spine.py init                    # Create spine file
    python3 morpheus_spine.py thought "text"           # Log a thought
    python3 morpheus_spine.py decision "what" "why"    # Log a decision
    python3 morpheus_spine.py memory "key" "value"     # Log memory formation
    python3 morpheus_spine.py status                   # Show spine health
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SPINE_DIR = Path(__file__).parent / "soul" / "cognition"
SPINE_FILE = SPINE_DIR / "morpheus_spine.jsonl"


def append_event(event: dict) -> dict:
    """Append event to morpheus spine with hash and timestamp."""
    SPINE_DIR.mkdir(parents=True, exist_ok=True)

    if "ts" not in event:
        event["ts"] = datetime.now(timezone.utc).isoformat()

    # Add provenance
    event["agent"] = "morpheus"
    event["ecosystem"] = "evez"

    raw = json.dumps(event, sort_keys=True, ensure_ascii=False)
    event["hash"] = hashlib.sha256(raw.encode()).hexdigest()

    with open(SPINE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


def read_spine(limit: int = 0) -> list[dict]:
    """Read spine events."""
    if not SPINE_FILE.exists():
        return []
    events = []
    for line in SPINE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if limit > 0:
        events = events[-limit:]
    return events


def cmd_init():
    """Initialize the spine."""
    if SPINE_FILE.exists():
        print(f"Spine exists: {SPINE_FILE} ({len(read_spine())} events)")
        return
    event = append_event({
        "kind": "genesis",
        "truth_plane": "canonical",
        "provenance": "morpheus_bootstrap",
        "falsifier": "replay_from_spine",
        "message": "Morpheus spine initialized — first event in the cognition chain",
    })
    print(f"Spine initialized: {SPINE_FILE}")
    print(f"Genesis hash: {event['hash'][:16]}...")


def cmd_thought(text: str):
    """Log a thought to the spine."""
    event = append_event({
        "kind": "thought",
        "truth_plane": "hyper",
        "content": text,
        "falsifier": "consistency_check",
    })
    print(f"[{event['ts']}] thought logged: {event['hash'][:12]}...")


def cmd_decision(what: str, why: str):
    """Log a decision with rationale."""
    event = append_event({
        "kind": "decision",
        "truth_plane": "canonical",
        "provenance": "morpheus_reasoning",
        "falsifier": "outcome_verification",
        "decision": what,
        "rationale": why,
    })
    print(f"[{event['ts']}] decision logged: {event['hash'][:12]}...")


def cmd_memory(key: str, value: str):
    """Log a memory formation event."""
    event = append_event({
        "kind": "memory_formation",
        "truth_plane": "verified",
        "key": key,
        "value": value,
        "falsifier": "memory_recall_test",
    })
    print(f"[{event['ts']}] memory logged: {key}")


def cmd_status():
    """Show spine health."""
    if not SPINE_FILE.exists():
        print("No spine found. Run: python3 morpheus_spine.py init")
        return
    events = read_spine()
    kinds = {}
    for ev in events:
        k = ev.get("kind", "unknown")
        kinds[k] = kinds.get(k, 0) + 1

    print(f"Spine: {SPINE_FILE}")
    print(f"Events: {len(events)}")
    print(f"Kinds: {json.dumps(kinds, indent=2)}")
    if events:
        print(f"First: {events[0].get('ts', '?')}")
        print(f"Last:  {events[-1].get('ts', '?')}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "init":
        cmd_init()
    elif cmd == "thought" and len(sys.argv) >= 3:
        cmd_thought(" ".join(sys.argv[2:]))
    elif cmd == "decision" and len(sys.argv) >= 4:
        cmd_decision(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "memory" and len(sys.argv) >= 4:
        cmd_memory(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
