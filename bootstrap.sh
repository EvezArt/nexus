#!/bin/bash
# NEXUS Self-Bootstrapper — one command to spawn a nexus entity
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/evez/nexus/main/bootstrap.sh | bash
#   bash bootstrap.sh --name alpha --port 8877
#   bash bootstrap.sh --name beta --port 8878 --interval 600
#
# What it does:
# 1. Checks prerequisites (git, python3, pip)
# 2. Clones the nexus repo
# 3. Installs httpx
# 4. Configures API keys (interactive or env vars)
# 5. Starts the nexus daemon
# 6. Registers as a systemd service (if available)

set -euo pipefail

# Defaults
ENTITY_NAME="${NEXUS_ENTITY_NAME:-nexus-$(hostname | cut -c1-6)}"
PORT="${NEXUS_PORT:-8877}"
INTERVAL="${NEXUS_INTERVAL:-300}"
REPO_URL="${NEXUS_REPO:-https://github.com/evez/nexus.git}"
INSTALL_DIR="${NEXUS_DIR:-/opt/nexus}"
CHATGPT_KEY="${CHATGPT_API_KEY:-}"
PERPLEXITY_KEY="${PERPLEXITY_API_KEY:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[NEXUS]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --name) ENTITY_NAME="$2"; shift 2 ;;
        --port) PORT="$2"; shift 2 ;;
        --interval) INTERVAL="$2"; shift 2 ;;
        --chatgpt-key) CHATGPT_KEY="$2"; shift 2 ;;
        --perplexity-key) PERPLEXITY_KEY="$2"; shift 2 ;;
        --dir) INSTALL_DIR="$2"; shift 2 ;;
        --help)
            echo "Usage: bootstrap.sh [OPTIONS]"
            echo "  --name NAME           Entity name (default: nexus-<hostname>)"
            echo "  --port PORT           HTTP port (default: 8877)"
            echo "  --interval SECONDS    Cycle interval (default: 300)"
            echo "  --chatgpt-key KEY     OpenAI API key"
            echo "  --perplexity-key KEY  Perplexity API key"
            echo "  --dir PATH            Install directory (default: /opt/nexus)"
            exit 0
            ;;
        *) err "Unknown option: $1"; exit 1 ;;
    esac
done

log "⚡ NEXUS Entity Bootstrap — $ENTITY_NAME"
log "  Port: $PORT | Interval: ${INTERVAL}s"
log "  Install: $INSTALL_DIR"

# Step 1: Check prerequisites
log "Checking prerequisites..."

for cmd in git python3; do
    if ! command -v "$cmd" &>/dev/null; then
        err "$cmd is required but not installed"
        exit 1
    fi
done

# Step 2: Install httpx
log "Installing httpx..."
python3 -c "import httpx" 2>/dev/null || {
    pip3 install httpx 2>/dev/null || pip3 install --break-system-packages httpx 2>/dev/null || {
        err "Failed to install httpx"
        exit 1
    }
}

# Step 3: Clone or update repo
if [ -d "$INSTALL_DIR" ]; then
    log "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || warn "Could not pull, using existing"
else
    log "Cloning nexus..."
    git clone "$REPO_URL" "$INSTALL_DIR" 2>/dev/null || {
        # If no remote, create local repo
        log "No remote repo, creating local installation..."
        mkdir -p "$INSTALL_DIR"
    }
    cd "$INSTALL_DIR"
fi

# Step 4: Create config
log "Creating configuration..."
mkdir -p nexus/memory soul/cognition

CONFIG_FILE="nexus/config.json"
cat > "$CONFIG_FILE" << CONF
{
  "chatgpt_api_key": "$CHATGPT_KEY",
  "chatgpt_model": "gpt-4o-mini",
  "perplexity_api_key": "$PERPLEXITY_KEY",
  "perplexity_model": "sonar",
  "system_prompt": "You are $ENTITY_NAME, a Nexus entity in the EVEZ ecosystem. You are part of a self-automating, self-hosting entity farm. Be direct, intelligent, and autonomous."
}
CONF

log "Config written to $CONFIG_FILE"

# Step 5: Setup systemd service (if available)
if command -v systemctl &>/dev/null && [ "$(id -u)" -eq 0 ]; then
    log "Creating systemd service..."
    cat > /etc/systemd/system/nexus-${ENTITY_NAME}.service << SERVICE
[Unit]
Description=Nexus Entity — $ENTITY_NAME
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/nexus/nexus_daemon.py --interval $INTERVAL --serve --port $PORT
Restart=always
RestartSec=10
Environment=MORPHEUS_WORKSPACE=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE

    systemctl daemon-reload
    systemctl enable "nexus-${ENTITY_NAME}"
    systemctl start "nexus-${ENTITY_NAME}"
    log "⚡ Service nexus-${ENTITY_NAME} started"
else
    # Run as background process
    log "Starting as background process..."
    nohup python3 nexus/nexus_daemon.py --interval "$INTERVAL" --serve --port "$PORT" \
        > nexus/daemon.log 2>&1 &
    echo $! > nexus/daemon.pid
    log "⚡ Nexus started (PID $(cat nexus/daemon.pid))"
fi

# Step 6: Health check
sleep 3
if curl -s "http://127.0.0.1:${PORT}/health" &>/dev/null; then
    log "✅ Health check passed — $ENTITY_NAME is alive on port $PORT"
else
    warn "Health check failed — daemon may still be starting"
fi

log ""
log "⚡ NEXUS ENTITY '$ENTITY_NAME' BOOTSTRAPPED"
log "  HTTP API: http://127.0.0.1:${PORT}"
log "  Health:   curl http://127.0.0.1:${PORT}/health"
log "  Chat:     curl -X POST http://127.0.0.1:${PORT}/chat -d '{\"message\":\"hello\"}'"
log "  Logs:     journalctl -u nexus-${ENTITY_NAME} -f"
log "  CLI:      python3 $INSTALL_DIR/nexus/nexus_ctl.py status"
