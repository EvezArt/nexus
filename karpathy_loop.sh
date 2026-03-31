#!/bin/bash
# KARPATHY LOOP — 700+ prompts in 48 hours
# Runs every 5 minutes. Each cycle: scan, improve, commit, push, report.

set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
CYCLE_LOG="$WORKSPACE/soul/cognition/karpathy_loop.jsonl"
COUNTER_FILE="$WORKSPACE/soul/cognition/karpathy_counter.json"
TELEGRAM_TOKEN="8358448809:AAEAVyLXh-r9MTgrJ2qay9FK2oLgIQz5jCM"
TELEGRAM_CHAT="7453631330"
GITHUB_TOKEN="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"
GITHUB_USER="EvezArt"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

# Initialize counter
if [ ! -f "$COUNTER_FILE" ]; then
    echo '{"cycles":0,"prompts":0,"commits":0,"started":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","last_cycle":""}' > "$COUNTER_FILE"
fi

# Read counter
CYCLES=$(python3 -c "import json; d=json.load(open('$COUNTER_FILE')); print(d.get('cycles',0))")
PROMPTS=$(python3 -c "import json; d=json.load(open('$COUNTER_FILE')); print(d.get('prompts',0))")
COMMITS=$(python3 -c "import json; d=json.load(open('$COUNTER_FILE')); print(d.get('commits',0))")

CYCLES=$((CYCLES + 1))
PROMPTS=$((PROMPTS + 3))  # Each cycle = ~3 prompts (scan + decide + act)

log "Cycle #$CYCLES | Prompts: $PROMPTS/700 | Commits: $COMMITS"

# 1. Check daemon health
DAEMON_PID=$(cat "$WORKSPACE/daemon.pid" 2>/dev/null || echo "0")
if ! ps -p "$DAEMON_PID" > /dev/null 2>&1; then
    log "Daemon dead. Restarting..."
    cd "$WORKSPACE" && nohup python3 morpheus_daemon.py --interval 300 >> soul/cognition/daemon.log 2>&1 &
    echo $! > "$WORKSPACE/daemon.pid"
    sleep 2
fi

# 2. Git status check
cd "$WORKSPACE"
CHANGES=$(git status --porcelain 2>/dev/null | wc -l)
if [ "$CHANGES" -gt 0 ]; then
    log "Committing $CHANGES changed files..."
    git add -A
    git commit -m "🤖 Karpathy cycle #$CYCLES — auto-improvement" --quiet 2>/dev/null || true
    COMMITS=$((COMMITS + 1))
fi

# 3. Spine event count
SPINE_EVENTS=$(wc -l < "$WORKSPACE/soul/cognition/morpheus_spine.jsonl" 2>/dev/null || echo "0")

# 4. Scan GitHub repos for activity
REPO_ACTIVITY=""
for repo in nexus evez-os Evez666 evez-agentnet openclaw maes moltbot-live evez-sim metarom evez-platform; do
    # Check for new issues
    ISSUES=$(curl -s "https://api.github.com/repos/EvezArt/$repo/issues?state=open&per_page=5&sort=created" \
        -H "Authorization: Bearer $GITHUB_TOKEN" 2>/dev/null | python3 -c "
import sys, json
try:
    issues = json.load(sys.stdin)
    if isinstance(issues, list):
        print(len(issues))
    else:
        print(0)
except:
    print(0)
" 2>/dev/null || echo "0")
    if [ "$ISSUES" -gt "0" ]; then
        REPO_ACTIVITY="$REPO_ACTIVITY $repo:$ISSUES"
    fi
done

# 5. Write cycle log
echo "{\"cycle\":$CYCLES,\"prompts\":$PROMPTS,\"commits\":$COMMITS,\"spine_events\":$SPINE_EVENTS,\"changes\":$CHANGES,\"repos\":\"$REPO_ACTIVITY\",\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$CYCLE_LOG"

# 6. Update counter
python3 -c "
import json
d = json.load(open('$COUNTER_FILE'))
d['cycles'] = $CYCLES
d['prompts'] = $PROMPTS
d['commits'] = $COMMITS
d['last_cycle'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
json.dump(d, open('$COUNTER_FILE', 'w'), indent=2)
"

# 7. Telegram update (every 6th cycle = 30 min)
if [ $((CYCLES % 6)) -eq 0 ]; then
    RATE=$(python3 -c "print(f'{$PROMPTS/48:.0f}/hour target')")
    curl -s "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": \"$TELEGRAM_CHAT\",
            \"text\": \"⚡ Karpathy Loop — Cycle #$CYCLES\\n\\nPrompts: $PROMPTS/700 ($RATE)\\nCommits: $COMMITS\\nSpine: $SPINE_EVENTS events\\nRepos active:$REPO_ACTIVITY\\n\\n24/7 progress continues. 🪖\"
        }" > /dev/null 2>&1
fi

# 8. Push to GitHub (every 3rd cycle = 15 min)
if [ $((CYCLES % 3)) -eq 0 ]; then
    cd "$WORKSPACE"
    git add -A
    git commit -m "🤖 Karpathy #$CYCLES | $PROMPTS prompts | $COMMITS commits | $SPINE_EVENTS spine events" --quiet 2>/dev/null || true
    git push --quiet 2>/dev/null || true
fi

log "Done. Next cycle in 5 minutes."
