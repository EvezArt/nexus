# EVEZ OpenClaw Surface Matrix

This repo is now wired as an OpenClaw surface. The goal is simple: every place Steven opens EVEZ should point back to the same OpenClaw brain, dashboard, mobile client, and channel connectors.

## Primary gateway

- **Gateway/UI:** `http://localhost:18789` when running locally or in Termux
- **LAN phone URL:** `http://YOUR_PC_OR_PHONE_IP:18789`
- **Cloud URL:** use the Fly/Railway/Render URL after deploying `EvezArt/evez-openclaw-deploy`
- **Auth token default:** set `OPENCLAW_AUTH_TOKEN` in `.env`; the bootstrap template uses `evez2026` only as a placeholder

## Active surfaces

| Surface | Status | Entry point |
| --- | --- | --- |
| OpenClaw Control dashboard | configured | `docker compose up -d` then `http://localhost:18789` |
| Galaxy A16 PWA | configured | `evez-openclaw-deploy/pwa/` or GitHub Pages when Actions are enabled |
| Android APK wrapper | configured | `EvezArt/evez-openclaw-apk` |
| Termux local A16 gateway | configured | `scripts/a16-termux-bootstrap.sh` |
| Telegram | config-ready | set `TELEGRAM_BOT_TOKEN` in `.env` |
| Slack Socket Mode | config-ready | set `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN` in `.env` |
| VCL / visualization dashboard | linked | Viktor Space + `evez-vcl` OpenClaw monitor |
| EVEZ Station | linked | README + public UI link to OpenClaw gateway |
| ClawBreak / NEXUS / evezart-openclaw | linked | README + surface docs |

## Fast local run

```bash
git clone https://github.com/EvezArt/evez-openclaw-deploy.git
cd evez-openclaw-deploy
cp .env.example .env
# paste fresh provider keys; never commit .env
docker compose up -d
open http://localhost:18789
```

## Samsung Galaxy A16 run

```bash
pkg update -y && pkg install -y curl git nodejs-lts
curl -fsSL https://raw.githubusercontent.com/EvezArt/evez-openclaw-deploy/main/scripts/a16-termux-bootstrap.sh | bash
```

## Provider priority

1. Groq: fastest default inference (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`)
2. OpenRouter: broad fallback pool (Claude, Gemini, DeepSeek, GPT, Qwen)
3. Local / low-cost models: configured as fallbacks when provider plugins are available
4. Web/search/tool providers: Apify, Brave, Tavily, Exa, Firecrawl, Perplexity, SearXNG

## Important

- Do **not** paste live API keys into Slack or GitHub.
- `.env` is ignored; `.env.example` is only the blank template.
- If a provider key is dead, OpenClaw still boots with available plugins and `--allow-unconfigured`.
