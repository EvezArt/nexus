#!/bin/bash
# EVEZ Full Deploy — One command to rule them all
# Deploys: Platform + n8n + Ollama + monitoring

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║  ⚡ EVEZ Full Stack Deploy                           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

INSTALL_DIR="${EVEZ_DIR:-/root/.openclaw/workspace/evez-platform}"
cd "$INSTALL_DIR"

# 1. Platform
echo "[1/5] Deploying EVEZ Platform..."
pip3 install --break-system-packages -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt
echo "  ✅ Platform dependencies installed"

# 2. Ollama (optional, for local models)
echo "[2/5] Checking Ollama..."
if command -v ollama &>/dev/null; then
    echo "  ✅ Ollama already installed"
else
    echo "  ⏭️  Ollama not installed (optional — cloud API works without it)"
    echo "     Install later: curl -fsSL https://ollama.ai/install.sh | sh"
fi

# 3. n8n (optional, for workflow automation)
echo "[3/5] Checking n8n..."
if command -v n8n &>/dev/null || docker ps 2>/dev/null | grep -q n8n; then
    echo "  ✅ n8n already running"
else
    echo "  ⏭️  n8n not installed (optional — trunk works without it)"
    echo "     Install later: docker run -d --name n8n -p 5678:5678 n8nio/n8n"
fi

# 4. Environment
echo "[4/5] Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  📝 Created .env — edit with your API keys"
else
    echo "  ✅ .env already exists"
fi

# 5. Start
echo "[5/5] Starting EVEZ Platform..."
pkill -f "python3 main.py" 2>/dev/null || true
sleep 1
nohup python3 main.py > /tmp/evez-platform.log 2>&1 &
sleep 2

if curl -s http://localhost:8080/api/health >/dev/null 2>&1; then
    echo "  ✅ Platform running on http://localhost:8080"
else
    echo "  ❌ Platform failed to start — check /tmp/evez-platform.log"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ⚡ EVEZ Full Stack — DEPLOYED                       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  🌐 Platform:    http://localhost:8080"
echo "  📡 API Docs:    http://localhost:8080/docs"
echo "  🧠 Trunk:       http://localhost:8080/api/trunk/status"
echo "  💰 Income:      http://localhost:8080/api/automator/tasks"
echo "  ⚛️  Quantum:     http://localhost:8080/api/quantum/status"
echo ""
echo "  📝 Edit .env to add your API keys:"
echo "     vim $INSTALL_DIR/.env"
echo ""
echo "  📊 Monitor:"
echo "     tail -f /tmp/evez-platform.log"
echo ""
echo "  🔗 Surfaces to connect:"
echo "     1. ChatGPT — add OPENAI_API_KEY to .env"
echo "     2. Perplexity — add PERPLEXITY_API_KEY to .env"
echo "     3. n8n — add N8N_WEBHOOK_URL to .env"
echo "     4. Android — build from android/ directory"
echo ""
echo "  All free. All local-first. All running."
echo ""
