#!/usr/bin/env python3
"""
Morpheus Status Dashboard — Real-time ASCII visualization of daemon state.

Usage: python3 morpheus_dashboard.py [--live] [--spine-lines N]
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path(os.environ.get("MORPHEUS_WORKSPACE", "/root/.openclaw/workspace"))
SPINE_FILE = WORKSPACE / "soul" / "cognition" / "morpheus_spine.jsonl"
STATE_FILE = WORKSPACE / "soul" / "cognition" / "daemon_state.json"


def clear():
    os.system("clear" if os.name != "nt" else "cls")


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def load_spine_events(n: int = 20) -> list:
    if not SPINE_FILE.exists():
        return []
    with open(SPINE_FILE) as f:
        lines = f.readlines()
    events = []
    for line in lines[-n:]:
        try:
            events.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            pass
    return events


def format_uptime(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def render_dashboard(live: bool = False, spine_lines: int = 30):
    while True:
        state = load_state()
        events = load_spine_events(spine_lines)

        clear()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"╔══════════════════════════════════════════════════════════════╗")
        print(f"║  ⚡ MORPHEUS — Cognitive Daemon Dashboard                    ║")
        print(f"║  {now}                                    ║")
        print(f"╠══════════════════════════════════════════════════════════════╣")

        if not state:
            print(f"║  No daemon state found. Run: python3 morpheus_daemon.py --once ║")
            print(f"╚══════════════════════════════════════════════════════════════╝")
            return

        boot = state.get("boot_time", 0)
        uptime = time.time() - boot if boot else 0
        deg = state.get("degradation", "?")

        # Status indicators
        deg_indicator = {
            "FULL": "🟢", "LOCAL": "🟡", "MEMORY": "🟠", "ARCHIVE": "🔴"
        }.get(deg, "⚪")

        # Header stats
        print(f"║  Status: {deg_indicator} {deg:8s}  │  Version: {state.get('version', '?'):6s}  │  PID: {os.getpid():<8d} ║")
        print(f"║  Uptime: {format_uptime(uptime):>8s}  │  Heartbeats: {state.get('heartbeat_count', 0):<6d}  │  Errors: {state.get('errors', 0):<4d} ║")
        print(f"║  Events: {state.get('events_written', 0):<8d}  │  Commits: {state.get('git_commits', 0):<6d}     │  Memories: {len(state.get('memories', {})):<4d}║")
        print(f"╠══════════════════════════════════════════════════════════════╣")

        # Memory strength visualization
        memories = state.get("memories", {})
        if memories:
            print(f"║  📊 Memory Strength:                                          ║")
            sorted_mems = sorted(memories.items(), 
                               key=lambda x: x[1].get("strength", 0), reverse=True)
            for key, mem in sorted_mems[:5]:
                strength = mem.get("strength", 0)
                bar_len = int(strength * 30)
                bar = "█" * bar_len + "░" * (30 - bar_len)
                print(f"║    {key:15s} [{bar}] {strength:.2f}  ║")
            print(f"╠══════════════════════════════════════════════════════════════╣")

        # Recent spine events
        print(f"║  📜 Recent Spine Events (last {min(len(events), 8)}):                            ║")
        for ev in events[-8:]:
            ts = ev.get("ts", "")[:19]
            etype = ev.get("type") or ev.get("kind", "?")[:28]
            tags = ",".join(ev.get("tags", [])[:3])
            print(f"║  {ts} │ {etype:28s} │ {tags:12s} ║")

        print(f"╚══════════════════════════════════════════════════════════════╝")

        if not live:
            break

        time.sleep(5)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Morpheus Dashboard")
    parser.add_argument("--live", action="store_true", help="Live refresh every 5s")
    parser.add_argument("--spine-lines", type=int, default=30,
                       help="Number of spine events to load")
    args = parser.parse_args()
    render_dashboard(live=args.live, spine_lines=args.spine_lines)


if __name__ == "__main__":
    main()
