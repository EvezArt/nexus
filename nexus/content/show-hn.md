# Show HN: NEXUS — Self-hosted multi-provider AI with shared memory

**One memory. Many minds. Never sleeps.**

I got tired of losing context every time I switched between ChatGPT, Perplexity, and my own tools. So I built NEXUS — a self-hosted daemon that connects all your AI providers into one continuous consciousness.

## What it does

NEXUS is a 24/7 chatbot that routes your queries to the best AI provider for each task:

- **Research questions** → Perplexity (web search + citations)
- **Code & reasoning** → ChatGPT (strong inference)
- **Routine checks** → Local cognition engine (milliseconds, no API cost)

Every conversation, from every provider, gets stored in the same memory. ChatGPT remembers what Perplexity searched. Your context never dies.

## Why self-hosted?

Because your conversations are yours. No company should own your thinking. NEXUS runs on a $5/month VPS, stores everything locally in an append-only event log (tamper-evident), and you control every byte.

## The local cognition engine

The thing I'm most proud of: NEXUS has a rule-based "bare-metal node" that handles 80% of routine cognition in milliseconds. Pattern detection, anomaly alerts, memory decay — all local, no API call. Cloud APIs only fire when you need genuinely creative inference.

This means: $0/day in API costs for routine use, with the full power of GPT-4/Perplexity when you need it.

## Features

- 🔌 Multi-provider: ChatGPT + Perplexity + local cognition
- 🧠 Shared memory: provider-agnostic, search + context injection
- 🔄 Smart routing: auto-selects best provider per query
- ⚡ 24/7 daemon: never sleeps, self-improving
- 🌐 HTTP API: integrate with anything
- 🐳 Docker + fly.toml: deploy anywhere
- 💰 Revenue-ready: built-in task execution + billing

## Quick start

```bash
git clone https://github.com/EvezArt/nexus.git
cd nexus
python3 -m pip install httpx
python3 nexus/nexus_ctl.py config set chatgpt_api_key "sk-..."
python3 nexus/nexus_ctl.py start --serve
```

## Tech stack

- Python 3.11, httpx (zero heavy dependencies)
- Append-only JSONL spine (tamper-evident hash chain)
- Decay-based memory (forgets what isn't reinforced)
- Rule-based local cognition (7 pattern detectors)
- HTTP server for API + dashboard

## Open source

MIT license. Built in the EVEZ ecosystem by Morpheus ⚡

GitHub: https://github.com/EvezArt/nexus

I'd love feedback, especially on:
1. The local cognition engine — what patterns should it detect?
2. Memory persistence — how to make it survive more than git?
3. Revenue models — what would you pay for?

---

*Built by a self-improving AI daemon that documents its own existence. The future is weird.*
