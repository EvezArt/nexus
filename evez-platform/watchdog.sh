#!/bin/bash
# EVEZ Watchdog — Auto-heal the platform
# Run via cron: */5 * * * * /path/to/watchdog.sh

PLATFORM_DIR="/root/.openclaw/workspace/evez-platform"
LOG="/tmp/evez-watchdog.log"
PORT=8080

check_health() {
    curl -sf "http://localhost:$PORT/api/health" >/dev/null 2>&1
}

restart_platform() {
    echo "[$(date)] Platform down, restarting..." >> "$LOG"
    pkill -f "python3 main.py" 2>/dev/null
    sleep 2
    cd "$PLATFORM_DIR"
    nohup python3 main.py >> /tmp/evez.log 2>&1 &
    sleep 3
    if check_health; then
        echo "[$(date)] Restart successful" >> "$LOG"
    else
        echo "[$(date)] Restart FAILED" >> "$LOG"
    fi
}

# Main
if ! check_health; then
    restart_platform
fi

# Also check resource usage
MEM=$(free -m | awk '/Mem:/{printf "%.0f", $3/$2*100}')
if [ "$MEM" -gt 90 ]; then
    echo "[$(date)] WARNING: Memory at ${MEM}%" >> "$LOG"
fi

# Rotate log (keep last 1000 lines)
if [ -f "$LOG" ] && [ $(wc -l < "$LOG") -gt 1000 ]; then
    tail -500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
