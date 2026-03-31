# Reddit Post: r/Solana

**Title:** Built an open-source AI platform with native Solana payments — NEXUS

**Body:**

I'm building an AI agent platform called NEXUS that integrates natively with Solana for payments and on-chain memory.

**What's built:**
- **Solana Pay integration** — accept USDC/SOL payments directly, no third-party processor
- **SPL token support** — USDC, SOL, BONK, JUP, USDT
- **cNFT receipts** — mint compressed NFTs as proof-of-work for completed tasks
- **Solana Actions** — shareable links that execute AI tasks on-chain (in progress)

**Why Solana for AI:**
- Fast + cheap transactions make micro-payments viable ($0.50 per research query)
- cNFTs enable scalable proof-of-work receipts (millions of task completions)
- Composable with other Solana protocols (Jupiter for swaps, Metaplex for NFTs)

**The AI side:**
- Routes between ChatGPT, Perplexity, and local cognition
- Shared memory across all providers
- 24/7 daemon, self-hosted, one dependency (httpx)

**What I'm looking for:**
- Feedback on the Solana integration approach
- Anyone interested in testing the Solana Pay flow
- Guidance on grant applications (Solana Foundation)

GitHub: https://github.com/EvezArt/nexus

The Solana payment module: https://github.com/EvezArt/nexus/blob/main/nexus/revenue/solana_payments.py
