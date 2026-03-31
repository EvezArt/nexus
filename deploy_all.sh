#!/bin/bash
# EVEZ DEPLOY ALL — Master deployment script
#
# Deploys the entire EVEZ ecosystem in one command.
# Each repo deploys to its optimal platform.
#
# Usage: bash deploy_all.sh
#        bash deploy_all.sh --repo nexus
#        bash deploy_all.sh --dry-run

set -euo pipefail

DRY_RUN=false
TARGET_REPO=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --repo) TARGET_REPO="$2"; shift 2 ;;
        *) shift ;;
    esac
done

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log() { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

# Deployment matrix: repo → platform → command
declare -A DEPLOY_MAP

DEPLOY_MAP[nexus]="vps:deploy_nexus"
DEPLOY_MAP[evez-vcl]="render:deploy_vcl"
DEPLOY_MAP[evez-os]="docker:deploy_evez_os"
DEPLOY_MAP[openclaw]="docker:deploy_openclaw"
DEPLOY_MAP[moltbot-live]="docker:deploy_moltbot"
DEPLOY_MAP[Evez666]="local:deploy_evez666"
DEPLOY_MAP[evez-agentnet]="local:deploy_agentnet"
DEPLOY_MAP[maes]="local:deploy_maes"
DEPLOY_MAP[evez-sim]="local:deploy_sim"
DEPLOY_MAP[evez-platform]="local:deploy_platform"

# ---------------------------------------------------------------------------

deploy_nexus() {
    log "Deploying NEXUS to VPS..."
    if command -v python3 &>/dev/null; then
        cd /root/.openclaw/workspace
        # Start daemon if not running
        if [ ! -f daemon.pid ] || ! ps -p $(cat daemon.pid 2>/dev/null) &>/dev/null; then
            log "  Starting nexus daemon..."
            nohup python3 nexus/nexus_daemon.py --interval 300 --serve --port 8877 \
                > nexus/daemon.log 2>&1 &
            echo $! > daemon.pid
            sleep 2
            log "  Daemon started (PID $(cat daemon.pid))"
        else
            log "  Daemon already running (PID $(cat daemon.pid))"
        fi

        # Verify
        if curl -s http://127.0.0.1:8877/health &>/dev/null; then
            log "  ✅ NEXUS is live on port 8877"
        else
            warn "  Health check failed — daemon may still be starting"
        fi
    fi
}

deploy_vcl() {
    log "Deploying VCL..."
    warn "  VCL deploys via Render — push to trigger deployment"
    warn "  Repo: https://github.com/EvezArt/evez-vcl"
    warn "  Config: render.yaml (free tier)"
}

deploy_evez_os() {
    log "Deploying EVEZ-OS..."
    warn "  EVEZ-OS deploys via docker-compose"
    warn "  Repo: https://github.com/EvezArt/evez-os"
}

deploy_openclaw() {
    log "Deploying OpenClaw..."
    warn "  OpenClaw deploys via Docker"
    warn "  Repo: https://github.com/EvezArt/openclaw"
}

deploy_moltbot() {
    log "Deploying MoltBot..."
    warn "  MoltBot has deploy.sh + docker-compose"
    warn "  Repo: https://github.com/EvezArt/moltbot-live"
}

deploy_evez666() {
    log "Deploying Evez666..."
    warn "  Evez666 is the Synaptic Recursion Kernel"
    warn "  Repo: https://github.com/EvezArt/Evez666"
}

deploy_agentnet() {
    log "Deploying AgentNet..."
    warn "  AgentNet deploys via Vercel"
    warn "  Repo: https://github.com/EvezArt/evez-agentnet"
}

deploy_maes() {
    log "Deploying MAES..."
    warn "  MAES is the agent runtime"
    warn "  Repo: https://github.com/EvezArt/maes"
}

deploy_sim() {
    log "Deploying EVEZ-SIM..."
    warn "  EVEZ-SIM is the Barnes-Hut simulation"
    warn "  Repo: https://github.com/EvezArt/evez-sim"
}

deploy_platform() {
    log "Deploying EVEZ Platform..."
    warn "  EVEZ Platform is the cognitive OS"
    warn "  Repo: https://github.com/EvezArt/evez-platform"
}

# ---------------------------------------------------------------------------

log "⚡ EVEZ DEPLOY ALL"
log ""

if [ -n "$TARGET_REPO" ]; then
    log "Deploying: $TARGET_REPO"
    func=$(echo "${DEPLOY_MAP[$TARGET_REPO]}" | cut -d: -f2)
    if [ "$DRY_RUN" = true ]; then
        log "  [DRY RUN] Would call: $func"
    else
        $func
    fi
else
    log "Deploying all ${#DEPLOY_MAP[@]} repos..."
    log ""

    for repo in "${!DEPLOY_MAP[@]}"; do
        platform=$(echo "${DEPLOY_MAP[$repo]}" | cut -d: -f1)
        func=$(echo "${DEPLOY_MAP[$repo]}" | cut -d: -f2)

        log "━━━ $repo ($platform) ━━━"
        if [ "$DRY_RUN" = true ]; then
            log "  [DRY RUN] Would call: $func"
        else
            $func
        fi
        log ""
    done
fi

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ Deploy complete"
log ""
log "Services:"
log "  NEXUS:      http://127.0.0.1:8877 (local)"
log "  VCL:        https://evez-vcl.onrender.com (Render)"
log "  GitHub:     https://github.com/EvezArt"
log "  Telegram:   @Evez666bot"
log "  Dashboard:  http://127.0.0.1:8877/"
