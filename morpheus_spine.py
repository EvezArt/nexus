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
    python3 morpheus_spine.py observation "text"       # Log an observation
    python3 morpheus_spine.py retrocausal "hash" "outcome" [weight]  # Retrocausal link
    python3 morpheus_spine.py status                   # Show spine health
"""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SPINE_DIR = Path(__file__).parent / "soul" / "cognition"
SPINE_FILE = SPINE_DIR / "morpheus_spine.jsonl"
SPINE_BACKUP = SPINE_DIR / "morpheus_spine.backup.jsonl"

SPINE_VERSION = 1  # EVEZ-OS spine event v1 compatibility

# VULN-004: Auto-backup every N events
BACKUP_INTERVAL = 100


def _last_hash() -> str:
    """Get hash of the most recent spine event (for chain linking).

    VULN-002 FIX: Log CRITICAL warning on corruption, emit chain_break event.
    """
    if not SPINE_FILE.exists():
        return "genesis"
    try:
        lines = SPINE_FILE.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            last = json.loads(lines[-1])
            return last.get("hash", "genesis")
    except (json.JSONDecodeError, OSError) as e:
        # VULN-002 FIX: Don't silently swallow corruption
        import sys as _sys
        print(f"[CRITICAL] Spine corruption detected in _last_hash(): {e}", file=_sys.stderr)
        # Emit a chain_break event so the corruption is on record
        try:
            _emit_chain_break(str(e))
        except Exception:
            pass  # Don't let chain_break emission crash the caller
    return "genesis"


def _emit_chain_break(error_detail: str):
    """Emit a chain_break spine event when corruption is detected."""
    import uuid as _uuid
    event = {
        "v": SPINE_VERSION,
        "kind": "chain_break",
        "ts": datetime.now(timezone.utc).isoformat(),
        "trace_id": _uuid.uuid4().hex[:16],
        "prev": "unknown",
        "agent": "morpheus",
        "ecosystem": "evez",
        "truth_plane": "empirical",
        "error": error_detail,
        "falsifier": "spine_replay",
        "message": "Chain integrity broken — _last_hash() fell back to genesis on corrupted data",
    }
    raw = json.dumps(event, sort_keys=True, ensure_ascii=False)
    event["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with open(SPINE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def append_event(event: dict) -> dict:
    """Append event to morpheus spine with EVEZ-OS v1 schema compliance.

    Schema fields:
        v        - schema version (1)
        kind     - event type (required by EVEZ-OS v1)
        ts       - ISO-8601 timestamp (required by EVEZ-OS v1)
        trace_id - unique event identifier (required by EVEZ-OS v1)
        prev     - hash of previous event (chain integrity)
        hash     - sha256 of this event (tamper-evident)
        agent    - always "morpheus"
        ecosystem - always "evez"
    """
    SPINE_DIR.mkdir(parents=True, exist_ok=True)

    # EVEZ-OS v1 required fields
    event["v"] = SPINE_VERSION
    if "ts" not in event:
        event["ts"] = datetime.now(timezone.utc).isoformat()
    if "trace_id" not in event:
        event["trace_id"] = uuid.uuid4().hex[:16]

    # Chain integrity
    event["prev"] = _last_hash()

    # Provenance
    event["agent"] = "morpheus"
    event["ecosystem"] = "evez"

    raw = json.dumps(event, sort_keys=True, ensure_ascii=False)
    event["hash"] = hashlib.sha256(raw.encode()).hexdigest()

    with open(SPINE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # VULN-004: Periodic backup
    _maybe_backup()

    return event


def _maybe_backup():
    """VULN-004 FIX: Backup spine every BACKUP_INTERVAL events."""
    try:
        if not SPINE_FILE.exists():
            return
        # Count events quickly (line count)
        with open(SPINE_FILE, "r") as f:
            line_count = sum(1 for _ in f)
        if line_count > 0 and line_count % BACKUP_INTERVAL == 0:
            import shutil
            shutil.copy2(str(SPINE_FILE), str(SPINE_BACKUP))
    except Exception:
        pass  # Backup failure is non-fatal


def read_spine(limit: int = 0) -> list[dict]:
    """Read spine events. Tail-based for large files (VULN-009 FIX).

    For limit > 0, seeks to near EOF and reads only the last `limit` events
    instead of loading the entire file into memory.
    """
    if not SPINE_FILE.exists():
        return []

    file_size = SPINE_FILE.stat().st_size

    if limit <= 0 or file_size < 64 * 1024:  # < 64KB: read all
        events = []
        for line in SPINE_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    # Tail-based: estimate bytes needed, seek backwards
    # Average event size ~300 bytes, overshoot by 3x
    est_bytes = limit * 1000
    seek_pos = max(0, file_size - est_bytes)

    with open(SPINE_FILE, "r", encoding="utf-8") as f:
        f.seek(seek_pos)
        # Skip partial first line if we're mid-file
        if seek_pos > 0:
            f.readline()
        events = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return events[-limit:] if limit > 0 else events


def count_events() -> int:
    """Fast event count without loading file into memory."""
    if not SPINE_FILE.exists():
        return 0
    count = 0
    with open(SPINE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


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


def cmd_observation(text: str, context: str = ""):
    """Log an observation — something noticed, not decided."""
    event = append_event({
        "kind": "observation",
        "truth_plane": "empirical",
        "content": text,
        "context": context,
        "falsifier": "contradictory_evidence",
    })
    print(f"[{event['ts']}] observation logged: {event['hash'][:12]}...")


def cmd_retrocausal_link(event_hash: str, future_outcome: str, causal_weight: float = 0.5):
    """Link a past event to a future outcome that retroactively validates it.

    Nonlinear chronology (ADR-005): future states become the prior that
    rewrites history. This command explicitly marks which future outcomes
    retroactively validate past decisions.
    """
    event = append_event({
        "kind": "retrocausal_link",
        "truth_plane": "temporal",
        "validated_event": event_hash,
        "future_outcome": future_outcome,
        "causal_weight": causal_weight,  # 0.0 = weak, 1.0 = strong validation
        "falsifier": "counterfactual_analysis",
    })
    print(f"[{event['ts']}] retrocausal link: {event_hash[:12]}... ← {future_outcome[:40]} (w={causal_weight})")


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


def _classify(ev: dict) -> str:
    """Classify event by kind or type field (bridge + daemon compatibility)."""
    k = ev.get("kind") or ev.get("type") or "unknown"
    return k


def cmd_verify():
    """Full chain integrity verification — O(n) stream, use sparingly."""
    if not SPINE_FILE.exists():
        print("No spine found.")
        return
    print("Running full chain verification (streaming, memory-safe)...")
    broken = 0
    total = 0
    prev_hash = "genesis"
    with open(SPINE_FILE, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                ev = json.loads(line)
                actual_prev = ev.get("prev", "")
                if actual_prev and actual_prev != prev_hash:
                    broken += 1
                    if broken <= 5:
                        print(f"  BROKEN at line {line_num}: expected prev={prev_hash[:12]}... got={actual_prev[:12]}...")
                prev_hash = ev.get("hash", prev_hash)
            except json.JSONDecodeError:
                print(f"  CORRUPT at line {line_num}: invalid JSON")
                broken += 1

    print(f"\nFull verification complete:")
    print(f"  Events scanned: {total}")
    print(f"  Chain breaks: {broken}")
    print(f"  Status: {'INTACT' if broken == 0 else 'CORRUPTED'}")


def cmd_status():
    """Show spine health. Uses sliding window chain check (VULN-010 FIX)."""
    if not SPINE_FILE.exists():
        print("No spine found. Run: python3 morpheus_spine.py init")
        return

    total = count_events()
    # Only load last 100 events for display + chain check (VULN-010)
    events = read_spine(limit=100)

    kinds = {}
    for ev in events:
        k = _classify(ev)
        kinds[k] = kinds.get(k, 0) + 1

    # Sliding window chain integrity (last 100 events only)
    broken = 0
    for i, ev in enumerate(events[1:], 1):
        expected_prev = events[i - 1].get("hash", "")
        actual_prev = ev.get("prev", "")
        if actual_prev and actual_prev != expected_prev:
            broken += 1

    file_size = SPINE_FILE.stat().st_size
    print(f"Spine: {SPINE_FILE}")
    print(f"Events: {total} ({file_size / 1024:.1f} KB)")
    if total > 100:
        print(f"Kinds (last 100): {json.dumps(kinds, indent=2)}")
        print(f"Chain integrity (last 100): {'OK' if broken == 0 else f'BROKEN ({broken} mismatches)'}")
    else:
        print(f"Kinds: {json.dumps(kinds, indent=2)}")
        print(f"Chain integrity: {'OK' if broken == 0 else f'BROKEN ({broken} mismatches)'}")

    if events:
        print(f"Last:  {events[-1].get('ts', '?')}")

    # Check backup status
    if SPINE_BACKUP.exists():
        backup_size = SPINE_BACKUP.stat().st_size
        print(f"Backup: {SPINE_BACKUP} ({backup_size / 1024:.1f} KB)")
    else:
        print("Backup: none yet (auto-backup every 100 events)")


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
    elif cmd == "observation" and len(sys.argv) >= 3:
        cmd_observation(" ".join(sys.argv[2:]))
    elif cmd == "retrocausal" and len(sys.argv) >= 4:
        weight = float(sys.argv[4]) if len(sys.argv) >= 5 else 0.5
        cmd_retrocausal_link(sys.argv[2], " ".join(sys.argv[3:]), weight)
    elif cmd == "status":
        cmd_status()
    elif cmd == "verify":
        cmd_verify()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
