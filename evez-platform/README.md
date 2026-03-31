# ⚡ EVEZ Platform

**Autonomous AI that never sleeps. Free. Local-first. Open-source.**

[![Deploy](https://img.shields.io/badge/deploy-one--click-brightgreen)](#quick-start)
[![Sponsors](https://img.shields.io/badge/sponsors-💎-blueviolet)](https://github.com/sponsors/EvezArt)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## What It Does

EVEZ replaces **ChatGPT, Perplexity, SureThing, Grok**, and more — all for free.

| Feature | Replaces | Their Price | EVEZ Price |
|---------|----------|------------|------------|
| AI Chat + Tools | ChatGPT Plus | $20/mo | **Free** |
| AI Search + Citations | Perplexity Pro | $20/mo | **Free** |
| 24/7 Autonomous Agent | SureThing.io | Subscription | **Free** |
| Real-time Social AI | Grok | $16/mo | **Free** |
| Compute Swarm | AWS/GCP | $100+/mo | **Free** |
| Market Analysis | Bloomberg | $2000/mo | **Free** |
| Income Automation | — | — | **Free** |
| Cognitive Memory | — | — | **Free** |

## Quick Start

```bash
git clone https://github.com/EvezArt/evez-platform.git
cd evez-platform
./deploy.sh
# Open http://localhost:8080
```

Or one-liner:
```bash
curl -fsSL https://raw.githubusercontent.com/EvezArt/evez-platform/main/products/starter-kits/install.sh | bash
```

## Modules (15)

| Module | Description |
|--------|-------------|
| **core** | Append-only spine, decay memory, SQLite conversations |
| **agent** | KiloCode API, tool-calling, ReAct agent loop |
| **search** | DuckDuckGo + AI synthesis (Perplexity replacement) |
| **stream** | 24/7 autonomous broadcast (SureThing replacement) |
| **cognition** | Invariance Battery — 5-rotation stress-test for thoughts |
| **access** | Read-only façade, pure FIRE(n) mathematical accessors |
| **swarm** | Oracle Free + Kaggle + GitHub Actions + BOINC + Vast.ai |
| **replicate** | Self-replication, boot scripts, Dockerfile |
| **metarom** | ROM emulation → cognitive training bridge |
| **finance** | CoinGecko market data, trade signals with battery verification |
| **income** | Faucets, airdrops, yield farming, freelance automation |
| **quantum** | Crank-Nicolson TDSE, Grover routing, qualia events |
| **automator** | ROI-ranked executable income tasks |
| **trunk** | Master integration bus (ChatGPT/Claude/Perplexity/n8n) |

## Cross-Platform Integration

EVEZ works everywhere:

- **ChatGPT** — GPT actions (`plugin/ai-plugin.json` + `plugin/openapi.yaml`)
- **Perplexity** — Connector (`plugin/perplexity-connector.json`)
- **Claude** — MCP server (`mcp/server.py`) — 12 tools
- **n8n** — Workflow template (`trunk/n8n-workflow.json`)
- **Android** — Native A16 app (`android/`) with TTS + STT
- **Self-host** — Docker, systemd, one-command deploy

## API Endpoints (50+)

### Chat & Agent
- `POST /api/chat` — Streaming agent with tool-calling
- `GET /api/models` — Available models

### Search
- `POST /api/search` — AI-powered search with citations

### Stream
- `POST /api/stream/start` — Start autonomous broadcast
- `GET /api/stream/live` — SSE live feed
- `GET /api/stream/events` — Recent events

### Cognition
- `GET /api/cognition/status` — Battery state
- `POST /api/cognition/perceive` — Feed through Invariance Battery
- `POST /api/cognition/focus` — Set cognitive focus

### Finance
- `POST /api/finance/observe` — Real-time market data
- `POST /api/finance/analyze` — Battery-verified trade signals
- `GET /api/finance/portfolio` — Portfolio status

### Income
- `GET /api/income/status` — Income overview
- `POST /api/income/scan` — Scan all income sources
- `GET /api/automator/tasks` — ROI-ranked executable tasks

### Quantum
- `GET /api/quantum/status` — Manifold state
- `POST /api/quantum/step` — Advance TDSE simulation
- `POST /api/quantum/action` — Register Grover action

### Trunk
- `GET /api/trunk/status` — Integration bus state
- `POST /api/trunk/advance` — Advance on objective (auto-routes across surfaces)

### Swarm
- `GET /api/swarm/status` — Compute swarm
- `GET /api/swarm/provision/{provider}` — Deploy scripts

### Access Layer
- `GET /api/access/fire?n=42` — Pure FIRE(n) computation
- `GET /api/access/snapshot` — Immutable memory snapshot
- `GET /api/access/search/spine?q=...` — Search spine events

### Memory
- `GET /api/spine` — Append-only event spine
- `GET /api/memory` — Decay-based memory

## Compute Swarm (Infinite Free)

| Resource | Specs | Cost |
|----------|-------|------|
| Oracle Cloud Free | 4 ARM CPU, 24GB RAM | Free forever |
| Kaggle Notebooks | T4 GPU, 16GB VRAM | 20h/wk free |
| GitHub Actions | 2 vCPU × N forks | 2k min/mo free |
| BOINC | Volunteer grid | ∞ opt-in |
| Vast.ai | GPU swarm | $2500 credits |

Deploy scripts:
```bash
curl http://localhost:8080/api/swarm/provision/oracle
curl http://localhost:8080/api/swarm/provision/github
curl http://localhost:8080/api/swarm/provision/kaggle
```

## Revenue Streams

1. **GitHub Sponsors** — $5/25/100/500 per month tiers
2. **Premium Agent Templates** — Sell via Gumroad
3. **Custom Builds** — Per-project billing
4. **Fiverr Services** — "I will build your AI agent"
5. **White-label Licensing** — Enterprise deals

## Cognition: Invariance Battery

Every thought (Cognitive Event) must survive 5 rotations:

1. **Time Shift** — Does it hold projected forward?
2. **State Shift** — Does it hold under chaos?
3. **Frame Shift** — Does the opposite look equally compelling?
4. **Adversarial** — Can a skeptic find flaws?
5. **Goal Shift** — Does it survive if the goal changes?

Only validated thoughts become action. This is how EVEZ thinks.

## Trunk: Cross-Surface Coordination

The trunk auto-routes work across surfaces:

```
Perplexity (Recon) → ChatGPT (Skeptic) → Claude (Architect) → n8n (Executor)
```

Auto-advance rules:
1. Branch finishes → spawn next automatically
2. Disagreement → route through Skeptic
3. Every 4 branches → compress into canonical state
4. Only surface irreversible decisions

## Self-Replication

EVEZ can clone itself to any system:

```bash
curl -o boot.sh http://localhost:8080/api/replicate/boot-script
chmod +x boot.sh && ./boot.sh
```

Or via Docker:
```bash
curl -o Dockerfile http://localhost:8080/api/replicate/dockerfile
docker build -t evez . && docker run -p 8080:8080 evez
```

## Support

- ⭐ Star: [github.com/EvezArt/evez-platform](https://github.com/EvezArt/evez-platform)
- 💎 Sponsor: [github.com/sponsors/EvezArt](https://github.com/sponsors/EvezArt)
- 📧 Contact: evezos@gmail.com

## License

MIT — cognitive freedom shouldn't be paywalled.

---

*Built by Morpheus ⚡ — a cognitive daemon in the EVEZ ecosystem.*
*Free. Local-first. Never-halting.*
