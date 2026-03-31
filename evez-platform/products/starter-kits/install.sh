#!/bin/bash
# EVEZ Starter Kit — Deploy in 5 minutes
# One command. Full platform. Free forever.
#
# What you get:
# - AI chat with tool-calling (replaces ChatGPT)
# - Web search with citations (replaces Perplexity)
# - 24/7 autonomous stream (replaces SureThing)
# - Cognitive memory + Invariance Battery
# - Market analysis + trade signals
# - Compute swarm (infinite free compute)
# - Income automation
#
# Cost: $0
# Time: 5 minutes
# Requirements: Linux, Python 3.10+, 1GB RAM

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║  ⚡ EVEZ Platform — One-Click Deploy         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Check requirements
echo "[1/5] Checking requirements..."
python3 --version >/dev/null 2>&1 || { echo "❌ Python 3.10+ required"; exit 1; }
pip3 --version >/dev/null 2>&1 || { echo "❌ pip required"; exit 1; }
echo "  ✅ Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "  ✅ pip available"

# Clone
echo "[2/5] Downloading EVEZ..."
INSTALL_DIR="${EVEZ_DIR:-$HOME/evez-platform}"
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR" && git pull
else
    git clone https://github.com/EvezArt/evez-platform.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
echo "  ✅ Installed to $INSTALL_DIR"

# Install dependencies
echo "[3/5] Installing dependencies..."
pip3 install --break-system-packages -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt
echo "  ✅ Dependencies installed"

# Create data directory
echo "[4/5] Setting up data..."
mkdir -p data
echo "  ✅ Data directory ready"

# Create systemd service (optional)
echo "[5/5] Creating service..."
cat > /tmp/evez.service << EOF
[Unit]
Description=EVEZ Platform
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$(which python3) main.py
Restart=always
RestartSec=5
Environment=EVEZ_PORT=8080
Environment=EVEZ_DATA=$INSTALL_DIR/data

[Install]
WantedBy=multi-user.target
EOF

echo "  Service file created at /tmp/evez.service"
echo "  To install: sudo cp /tmp/evez.service /etc/systemd/system/ && sudo systemctl enable --now evez"

# Start
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  ⚡ EVEZ Platform Ready!                      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  Start now:"
echo "    cd $INSTALL_DIR && python3 main.py"
echo ""
echo "  Or install as service:"
echo "    sudo cp /tmp/evez.service /etc/systemd/system/"
echo "    sudo systemctl enable --now evez"
echo ""
echo "  Open: http://localhost:8080"
echo ""
echo "  Features:"
echo "    💬 Chat     — AI agent with tool-calling"
echo "    🔍 Search   — Web search with citations"
echo "    📡 Stream   — 24/7 autonomous broadcast"
echo "    🧠 Brain    — Cognitive memory + spine"
echo "    💰 Income   — Automated income scanner"
echo "    ⚛️  Quantum  — Physics-based routing"
echo ""
echo "  All free. All local-first. All running."
echo ""
echo "  ⭐ Star us: https://github.com/EvezArt/evez-platform"
echo "  💎 Sponsor: https://github.com/sponsors/EvezArt"
echo ""
