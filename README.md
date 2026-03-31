# ⚡ NEXUS — Unified 24/7 Chatbot Entity Farm

**One memory. Many minds. Never sleeps.**

NEXUS connects ChatGPT, Perplexity, and OpenClaw into a single continuous consciousness. Every provider shares the same memory. Conversations continue across provider switches. The nexus operates 24/7 as a self-hosting, self-automating entity farm.

## Architecture

```
User ↔ Nexus Core ↔ Provider Router
                    ├── ChatGPT (reasoning, code, creative)
                    ├── Perplexity (search, research, citations)
                    └── OpenClaw (local spine, daemon, cognition)

All providers write to → Unified Memory (spine + daily logs + index)
All providers read from ← Unified Memory (context injection)
```

## Why NEXUS over any single provider

| Feature | ChatGPT alone | Perplexity alone | OpenClaw alone | **NEXUS** |
|---------|--------------|-----------------|----------------|-----------|
| Reasoning | ✅ | ⚠️ | ✅ | ✅ |
| Web search | ❌ | ✅ | ❌ | ✅ |
| Citations | ❌ | ✅ | ❌ | ✅ |
| Local cognition | ❌ | ❌ | ✅ | ✅ |
| Persistent memory | ⚠️ session | ❌ | ✅ | ✅ |
| Cross-provider memory | ❌ | ❌ | N/A | ✅ |
| 24/7 daemon | ❌ | ❌ | ✅ | ✅ |
| Smart routing | N/A | N/A | N/A | ✅ |
| Self-hosted | ❌ | ❌ | ✅ | ✅ |

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/EvezArt/nexus.git
cd nexus
python3 -m pip install httpx

# Set API keys
python3 nexus/nexus_ctl.py config set chatgpt_api_key "sk-..."
python3 nexus/nexus_ctl.py config set perplexity_api_key "pplx-..."
```

### 2. Run

```bash
# Single cycle (test)
python3 nexus/nexus_daemon.py --once

# 24/7 daemon (polling mode)
python3 nexus/nexus_ctl.py start

# 24/7 daemon with HTTP API
python3 nexus/nexus_ctl.py start --serve --port 8877
```

### 3. Chat

```bash
# Via CLI
python3 nexus/nexus_ctl.py chat "what is quantum computing"

# Via HTTP API
curl -X POST http://localhost:8877/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello nexus"}'

# Check health
curl http://localhost:8877/health
```

## Self-Bootstrap (One Command)

```bash
curl -sSL https://raw.githubusercontent.com/EvezArt/nexus/main/bootstrap.sh | bash \
  --name alpha --port 8877 --chatgpt-key "sk-..."
```

## Entity Farm (Docker)

```bash
# Start 3 nexus entities
docker-compose up -d

# Each entity is independent:
# nexus-alpha:  localhost:8877 (general)
# nexus-beta:   localhost:8878 (research-focused)
# nexus-gamma:  localhost:8879 (code-focused)
```

## Deploy to Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Launch
fly launch --dockerfile nexus/Dockerfile

# Set secrets
fly secrets set CHATGPT_API_KEY=sk-... PERPLEXITY_API_KEY=pplx-...

# Deploy
fly deploy

# Scale
fly scale count 3
```

## Smart Routing

NEXUS automatically routes queries to the best provider:

| Query type | Routed to | Example |
|-----------|-----------|---------|
| Research | Perplexity | "latest Solana MEV strategies" |
| Code | ChatGPT | "write a Python async HTTP server" |
| Routine | OpenClaw | "check daemon status" |
| General | ChatGPT → Perplexity | "explain quantum entanglement" |

The router learns from outcomes — if a provider keeps failing, it routes more to alternatives.

## Memory System

Every conversation is stored in a unified, provider-agnostic format:

- **Spine** — append-only JSONL event log (tamper-evident)
- **Daily logs** — human-readable markdown
- **Index** — fast keyword + recency search
- **Context injection** — relevant memories automatically added to conversations

Memory decays over time (0.98x/cycle). Forgotten memories are pruned. Strong memories persist.

## Providers

### ChatGPT (OpenAI)
- Models: gpt-4o, gpt-4o-mini, gpt-4-turbo
- Best for: reasoning, code, creative writing, multi-turn dialogue
- Requires: `CHATGPT_API_KEY`

### Perplexity
- Models: sonar-pro, sonar, sonar-reasoning
- Best for: web search, research, fact-checking, citations
- Requires: `PERPLEXITY_API_KEY`

### OpenClaw (Local)
- Always available, no API key needed
- Best for: routine checks, status, local cognition
- Connects to: Morpheus spine, local pattern detection

## HTTP API

When running with `--serve`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send a message `{"message": "...", "provider": "auto"}` |
| `/health` | GET | System health + provider status |
| `/output` | GET | Recent responses (last 20) |

## File Structure

```
nexus/
├── __init__.py              # Package init
├── nexus_core.py            # Orchestrator + smart router
├── nexus_daemon.py          # 24/7 daemon (polling or HTTP)
├── nexus_ctl.py             # CLI control
├── memory_store.py          # Unified memory system
├── providers/
│   ├── base.py              # Provider interface
│   ├── chatgpt.py           # OpenAI adapter
│   ├── perplexity.py        # Perplexity adapter
│   └── openclaw_bridge.py   # Local cognition bridge
├── Dockerfile               # Container build
└── .gitignore
```

## License

EVEZ Ecosystem — see LICENSE
