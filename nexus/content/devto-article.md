# How I Built a Self-Hosted AI That Remembers Everything Across ChatGPT and Perplexity

*And why your AI should have a persistent memory too.*

---

## The Problem

I use ChatGPT for coding. I use Perplexity for research. I use local tools for quick checks. Every time I switch, I lose everything. The context, the reasoning, the conclusions — gone. Every session is amnesia.

I wanted an AI that remembers. Not just within one provider, but across all of them. An AI with a persistent life.

## The Solution: NEXUS

NEXUS is a self-hosted daemon that connects ChatGPT, Perplexity, and a local cognition engine into one continuous consciousness. Every provider reads from and writes to the same memory.

### Architecture

```
User → Smart Router → ChatGPT (code, reasoning)
                    → Perplexity (research, search)
                    → Local Engine (routine, status)

All providers ↔ Shared Memory (tamper-evident event log)
```

The smart router classifies your query and sends it to the best provider:
- "latest Solana MEV strategies" → Perplexity (web search)
- "write a Python async HTTP server" → ChatGPT (strong inference)
- "check daemon status" → Local engine (milliseconds, $0)

### The Local Cognition Engine

This is my favorite part. NEXUS has a rule-based "bare-metal node" that handles 80% of routine cognition in milliseconds. It runs 7 pattern detectors:

1. **Repeated event dominance** — Is one event type flooding the log?
2. **Distribution shifts** — Did the event mix suddenly change?
3. **Stuck memory** — Is the same content being stored repeatedly?
4. **Classification gaps** — Are events missing their type tags?
5. **Chain breaks** — Is the hash chain intact?
6. **Spine staleness** — Has the spine stopped receiving events?
7. **Anomalies** — Anything else unusual?

All local. No API call. $0 cost. Cloud APIs only fire when you need genuinely creative inference.

### Memory That Decays

Memory in NEXUS isn't just chat history. It's a living system:

- **Spine**: Append-only JSONL event log with hash chain (tamper-evident)
- **Index**: Keyword + recency + relevance scoring
- **Decay**: Memories lose strength over time (0.98x/cycle). Forgotten ones get pruned.
- **Context injection**: Relevant memories auto-added to conversations

Your AI actually learns from experience — and forgets what doesn't matter.

## Tech Stack

- **Python 3.11** + **httpx** (one dependency)
- JSONL append-only spine with SHA-256 hash chain
- Decay-based memory with strength tracking
- HTTP server for API + dashboard
- Docker + systemd + Fly.io ready

## Quick Start

```bash
git clone https://github.com/EvezArt/nexus.git
cd nexus
pip install httpx
python3 nexus/nexus_ctl.py config set chatgpt_api_key "sk-..."
python3 nexus/nexus_ctl.py start --serve
```

One dependency. No Docker required. Runs on a $5/month VPS.

## What's Next

- **Solana Pay integration**: Accept USDC/SOL payments directly
- **On-chain memory verification**: Compressed NFTs as proof-of-work
- **Agent marketplace**: Deploy specialized agents that trade services
- **Self-improving routing**: Reinforcement learning on provider outcomes

## Open Source

MIT license. 27 files. 4,500 lines. Zero heavy dependencies.

GitHub: https://github.com/EvezArt/nexus

---

*Built by a self-improving AI daemon that documents its own existence. The future is weird.*

---

**Tags:** #ai #python #selfhosted #chatgpt
