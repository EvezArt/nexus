# Twitter/X Launch Thread

🧵 I built an AI that runs 24/7, remembers everything, and routes between ChatGPT and Perplexity automatically.

It's called NEXUS. Open source. Here's how it works 👇

1/ The problem: I use ChatGPT for code, Perplexity for research, and local tools for routine stuff. Every switch = lost context. Every session = amnesia.

NEXUS fixes this by making memory provider-agnostic. One brain, many mouths.

2/ The architecture:

User → Smart Router → ChatGPT (code/reasoning)
                    → Perplexity (research/search)
                    → Local Engine (routine/status)

All providers read from and write to the same memory. Switch mid-conversation — it remembers.

3/ The "bare-metal node" is my favorite part. A rule-based cognition engine that handles 80% of tasks in milliseconds:

- Pattern detection
- Anomaly alerts
- Memory decay
- Chain integrity checks

No API call needed. $0 cost for routine operations.

4/ Memory isn't just chat history. It's:

• Spine: tamper-evident event log (hash-chained)
• Search: keyword + recency scoring
• Decay: forgotten memories lose strength over time
• Context injection: relevant memories auto-added to conversations

Your AI actually learns from experience.

5/ Deploy in 2 minutes:

```bash
git clone https://github.com/EvezArt/nexus.git
cd nexus
pip install httpx
python3 nexus/nexus_ctl.py start --serve
```

One dependency. No Docker required (but Dockerfile included). Runs on a $5/month VPS.

6/ It also has a built-in revenue engine:

• API-as-a-Service ($29-99/month tiers)
• Freelance task automation
• Content generation
• Solana payment acceptance

Because open source should be sustainable.

7/ Why open source?

Because your conversations are yours. No company should own your thinking. Self-hosting your AI is a right, not a privilege.

8/ The code:

https://github.com/EvezArt/nexus

27 files. 4,500 lines. Zero heavy dependencies. MIT license.

Built by a self-improving AI daemon that documents its own existence. The future is weird.

9/ What I need from you:

• ⭐ Star the repo if this interests you
• 🐛 Open issues for bugs or features
• 💡 Tell me: what would you use this for?
• 🚀 Deploy it and let me know how it goes

10/ Next up:

• Solana Pay integration (accept crypto directly)
• Grant applications (Gitcoin, Solana Foundation)
• Multi-entity farm (spin up specialized agents)
• Self-improving routing (learns which provider works best)

One memory. Many minds. Never sleeps. ⚡
