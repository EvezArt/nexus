# EVEZ Platform — The Cognitive Species

**Free. Local-first. Never-halting.**

A unified platform that replaces ChatGPT, Perplexity, OpenClaw, and SureThing.io.
Built on the EVEZ cognitive architecture — not an assistant, but a living system.

## What It Does

| Feature | Replaces | Their Price | EVEZ Price |
|---------|----------|------------|------------|
| AI Chat (multi-model) | ChatGPT Plus | $20/mo | **Free** |
| AI Search + Citations | Perplexity Pro | $20/mo | **Free** |
| Autonomous Agent | OpenClaw | API costs | **Free** |
| 24/7 Streaming | SureThing.io | Subscription | **Free** |
| Real-time Social | Grok | $16/mo | **Free** |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EVEZ PLATFORM                         │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │   CHAT   │  │  SEARCH  │  │  AGENT   │  │ STREAM │ │
│  │          │  │          │  │          │  │        │ │
│  │ Multi-   │  │ Web      │  │ Tools,   │  │ 24/7   │ │
│  │ model    │  │ search,  │  │ cron,    │  │ auto-  │ │
│  │ conver-  │  │ scrape,  │  │ daemon,  │  │ broad- │ │
│  │ sation   │  │ cite     │  │ memory   │  │ cast   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │              │             │      │
│  ┌────▼──────────────▼──────────────▼─────────────▼──┐  │
│  │                  EVEZ CORE                         │  │
│  │  Spine (append-only) │ Memory (decay) │ Identity  │  │
│  └──────────────────────┴────────────────┴───────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              MODEL LAYER                          │   │
│  │  Ollama (local) ← → Cloud APIs (KiloCode, etc)  │   │
│  │  Free tier fallback chain, never blocks           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
cd evez-platform
pip install -r requirements.txt
python main.py
# Open http://localhost:8080
```

## Install Ollama (for free local models)

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2
ollama pull codellama
```

## Free Model Strategy

1. **Ollama local** — llama3.2, codellama, mistral (zero cost, your hardware)
2. **KiloCode free tier** — via OpenClaw's existing API key
3. **Fallback chain** — local first, cloud when needed, never fail

## License

MIT — because cognitive freedom shouldn't be paywalled.
