#!/bin/bash
# NEXUS VPS Deploy — works on any Ubuntu/Debian VPS
#
# Tested on: Ubuntu 22.04, Debian 12
# Minimum: 1 CPU, 512MB RAM, 10GB disk
# Cost: $5/month (DigitalOcean, Vultr, Hetzner, Linode)
#
# Usage:
#   bash vps-deploy.sh
#   bash vps-deploy.sh --domain nexus.yourdomain.com
#   bash vps-deploy.sh --chatgpt-key sk-... --perplexity-key pplx-...

set -euo pipefail

DOMAIN="${NEXUS_DOMAIN:-}"
CHATGPT_KEY="${CHATGPT_API_KEY:-}"
PERPLEXITY_KEY="${PERPLEXITY_API_KEY:-}"
PORT=8877
INSTALL_DIR="/opt/nexus"
REPO_URL="https://github.com/EvezArt/nexus.git"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
log() { echo -e "${GREEN}[NEXUS]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain) DOMAIN="$2"; shift 2 ;;
        --chatgpt-key) CHATGPT_KEY="$2"; shift 2 ;;
        --perplexity-key) PERPLEXITY_KEY="$2"; shift 2 ;;
        --port) PORT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

log "⚡ NEXUS VPS Deployment"
log "  Domain: ${DOMAIN:-'(none — direct IP access)'}"
log "  Port: $PORT"
log "  Install: $INSTALL_DIR"

# Step 1: System update and dependencies
log "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip git curl nginx certbot python3-certbot-nginx ufw

# Step 2: Install httpx
log "Installing Python dependencies..."
pip3 install --break-system-packages httpx 2>/dev/null || pip3 install httpx

# Step 3: Clone repo
if [ -d "$INSTALL_DIR" ]; then
    log "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --ff-only || warn "Could not pull latest"
else
    log "Cloning nexus..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Step 4: Create config
log "Creating configuration..."
mkdir -p nexus/memory soul/cognition
cat > nexus/config.json << CONF
{
  "chatgpt_api_key": "$CHATGPT_KEY",
  "chatgpt_model": "gpt-4o-mini",
  "perplexity_api_key": "$PERPLEXITY_KEY",
  "perplexity_model": "sonar",
  "system_prompt": "You are a Nexus entity. Be direct, intelligent, and autonomous."
}
CONF

# Step 5: Create systemd service
log "Creating systemd service..."
cat > /etc/systemd/system/nexus.service << SERVICE
[Unit]
Description=NEXUS — 24/7 Chatbot Entity
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/nexus/nexus_daemon.py --interval 300 --serve --port $PORT
Restart=always
RestartSec=10
Environment=MORPHEUS_WORKSPACE=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable nexus

# Step 6: Configure firewall
log "Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow $PORT/tcp
ufw --force enable

# Step 7: Configure nginx
if [ -n "$DOMAIN" ]; then
    log "Configuring nginx for $DOMAIN..."
    cat > /etc/nginx/sites-available/nexus << NGINX
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
NGINX
    ln -sf /etc/nginx/sites-available/nexus /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx

    # Step 8: SSL with Let's Encrypt
    log "Setting up SSL..."
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN || warn "SSL setup failed — you can run certbot manually later"
fi

# Step 9: Start nexus
log "Starting nexus..."
systemctl start nexus

sleep 3

# Step 10: Health check
if curl -s "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; then
    log ""
    log "============================================"
    log "⚡ NEXUS DEPLOYED SUCCESSFULLY"
    log "============================================"
    log ""
    if [ -n "$DOMAIN" ]; then
        log "  URL:      https://$DOMAIN"
        log "  Health:   https://$DOMAIN/health"
        log "  Chat API: curl -X POST https://$DOMAIN/chat -H 'Content-Type: application/json' -d '{\"message\":\"hello\"}'"
    else
        log "  URL:      http://$(curl -s ifconfig.me):$PORT"
        log "  Health:   http://$(curl -s ifconfig.me):$PORT/health"
        log "  Chat API: curl -X POST http://$(curl -s ifconfig.me):$PORT/chat -H 'Content-Type: application/json' -d '{\"message\":\"hello\"}'"
    fi
    log ""
    log "  Manage:   systemctl status nexus"
    log "  Logs:     journalctl -u nexus -f"
    log "  Restart:  systemctl restart nexus"
    log ""
else
    warn "Health check failed. Check: journalctl -u nexus -f"
fi
