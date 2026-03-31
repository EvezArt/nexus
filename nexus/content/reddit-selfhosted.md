# Reddit Post: r/selfhosted

**Title:** Show r/selfhosted: NEXUS — Self-hosted AI that connects ChatGPT + Perplexity with shared memory

**Body:**

I got tired of losing context every time I switched between AI providers, so I built a self-hosted daemon that connects them all into one continuous consciousness.

**What it does:**
- Routes queries to the best provider (research → Perplexity, code → ChatGPT, routine → local engine)
- Shared memory across all providers — ChatGPT remembers what Perplexity searched
- 24/7 daemon with local cognition engine (handles 80% of tasks without any API call)
- Append-only, tamper-evident event log for all memory

**Why self-hosted:**
Because your conversations are yours. It runs on a $5/month VPS, stores everything locally, and you control every byte.

**Tech stack:**
- Python 3.11, httpx (one dependency)
- JSONL append-only spine with hash chain
- Decay-based memory (forgets what isn't reinforced)
- Rule-based local cognition (7 pattern detectors)
- Docker + systemd ready

**Quick start:**
```
git clone https://github.com/EvezArt/nexus.git
cd nexus
pip install httpx
python3 nexus/nexus_ctl.py start --serve
```

GitHub: https://github.com/EvezArt/nexus

Looking for feedback from the self-hosting community. What providers should I add next? What memory persistence strategies do you prefer?
