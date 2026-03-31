# Changelog

## v0.1.0 (2026-03-31) — Initial Release

### Core
- Multi-provider AI routing (ChatGPT, Perplexity, local cognition)
- Smart query classification and provider selection
- Unified memory system with decay
- 24/7 daemon with heartbeat loop
- HTTP API server with billing
- CLI control tool (`nexus_ctl.py`)
- Real-time monitoring dashboard

### Providers
- ChatGPT adapter (OpenAI API, httpx)
- Perplexity adapter (search + citations)
- OpenClaw bridge (local spine + cognition)

### Memory
- Provider-agnostic memory store
- Keyword + recency search
- Context injection for conversations
- Decay-based pruning (0.98x/cycle)
- Append-only spine with hash chain

### Revenue
- Income engine with task execution
- Monetized API server (Bearer auth, rate limiting)
- Freelance automation
- Solana Pay integration (USDC/SOL)
- Revenue maximizer (grants, bounties, affiliates)

### Deploy
- One-command VPS deployment
- Docker + docker-compose (entity farm)
- Fly.io configuration
- Bootstrap script

### Content
- Show HN post
- Twitter launch thread
- Reddit posts (3 subreddits)
- Dev.to article
- Gitcoin grant application
- Solana Foundation grant application
