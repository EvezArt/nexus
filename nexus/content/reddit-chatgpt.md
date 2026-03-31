# Reddit Post: r/ChatGPT

**Title:** I built an open-source tool that connects ChatGPT + Perplexity with shared memory (self-hosted)

**Body:**

Ever lose context when switching between ChatGPT and Perplexity? I built NEXUS — a self-hosted daemon that connects them into one continuous consciousness.

**Key features:**
- **Smart routing**: Research queries auto-route to Perplexity (web search + citations), code goes to ChatGPT, routine stuff runs locally in milliseconds
- **Shared memory**: Every conversation from every provider gets stored in the same memory. Switch mid-conversation — it remembers.
- **Local cognition**: 80% of tasks handled by a rule-based engine without any API call. Pattern detection, anomaly alerts — $0 cost.
- **24/7 operation**: Runs as a daemon that never sleeps, maintains continuity across restarts

**No heavy dependencies** — just Python + httpx. Runs on a $5/month VPS.

```
git clone https://github.com/EvezArt/nexus.git
cd nexus && pip install httpx
python3 nexus/nexus_ctl.py start --serve
```

It also has a built-in API server with billing if you want to offer it as a service.

GitHub: https://github.com/EvezArt/nexus

Would love feedback from the community. What other providers should I integrate?
