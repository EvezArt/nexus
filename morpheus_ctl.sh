#!/usr/bin/env bash
# morpheus_ctl.sh — Control script for the Morpheus daemon
set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
DAEMON="$WORKSPACE/morpheus_daemon.py"
SERVICE="morpheus.service"
LOG="$WORKSPACE/soul/cognition/daemon.log"

case "${1:-help}" in
    start)
        echo "⚡ Starting Morpheus daemon..."
        systemctl start "$SERVICE" 2>/dev/null && {
            echo "  Started via systemd"
        } || {
            echo "  systemd not available, starting in background..."
            nohup python3 "$DAEMON" --interval 300 >> "$LOG" 2>&1 &
            echo $! > "$WORKSPACE/soul/cognition/daemon.pid"
            echo "  PID: $(cat "$WORKSPACE/soul/cognition/daemon.pid")"
        }
        ;;
    stop)
        echo "⚡ Stopping Morpheus daemon..."
        systemctl stop "$SERVICE" 2>/dev/null && {
            echo "  Stopped via systemd"
        } || {
            if [ -f "$WORKSPACE/soul/cognition/daemon.pid" ]; then
                PID=$(cat "$WORKSPACE/soul/cognition/daemon.pid")
                kill "$PID" 2>/dev/null && echo "  Killed PID $PID" || echo "  Process not running"
                rm -f "$WORKSPACE/soul/cognition/daemon.pid"
            else
                pkill -f "morpheus_daemon.py" 2>/dev/null && echo "  Killed by name" || echo "  Not running"
            fi
        }
        ;;
    restart)
        "$0" stop
        sleep 2
        "$0" start
        ;;
    status)
        echo "=== Morpheus Daemon Status ==="
        if [ -f "$WORKSPACE/soul/cognition/daemon_state.json" ]; then
            python3 -c "
import json, time
with open('$WORKSPACE/soul/cognition/daemon_state.json') as f:
    s = json.load(f)
uptime = time.time() - s.get('boot_time', time.time())
print(f'  Version:     {s.get(\"version\", \"?\")}')
print(f'  Degradation: {s.get(\"degradation\", \"?\")}')
print(f'  Heartbeats:  {s.get(\"heartbeat_count\", 0)}')
print(f'  Events:      {s.get(\"events_written\", 0)}')
print(f'  Commits:     {s.get(\"git_commits\", 0)}')
print(f'  Errors:      {s.get(\"errors\", 0)}')
print(f'  Uptime:      {uptime:.0f}s ({uptime/3600:.1f}h)')
print(f'  Memories:    {len(s.get(\"memories\", {}))}')
"
        else
            echo "  No state file — daemon hasn't run yet"
        fi
        echo ""
        systemctl status "$SERVICE" 2>/dev/null || echo "  (not managed by systemd)"
        ;;
    once)
        echo "⚡ Running single heartbeat..."
        python3 "$DAEMON" --once
        ;;
    log)
        tail -f "$LOG" 2>/dev/null || journalctl -u "$SERVICE" -f
        ;;
    install)
        echo "⚡ Installing systemd service..."
        cp "$WORKSPACE/morpheus.service" /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable "$SERVICE"
        echo "  Service installed and enabled"
        ;;
    help|*)
        echo "Usage: $0 {start|stop|restart|status|once|log|install}"
        echo ""
        echo "  start    — Start the daemon (systemd or background)"
        echo "  stop     — Stop the daemon gracefully"
        echo "  restart  — Restart the daemon"
        echo "  status   — Show daemon status"
        echo "  once     — Run a single heartbeat cycle"
        echo "  log      — Tail the daemon log"
        echo "  install  — Install systemd service"
        ;;
esac
