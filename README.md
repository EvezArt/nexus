# Nexus — EVEZ Service Discovery

Auto-discovers EVEZ microservices and builds a live service registry.

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*

---

## ⚡ OpenClaw Surface

This project now exposes/links into the EVEZ OpenClaw stack.

- Main deploy repo: https://github.com/EvezArt/evez-openclaw-deploy
- Android/A16 app: https://github.com/EvezArt/evez-openclaw-apk
- Local dashboard: `http://localhost:18789`
- Termux bootstrap: `scripts/a16-termux-bootstrap.sh` in the deploy repo

Run the OpenClaw gateway once, then point this surface at the same gateway URL so EVEZ Station, VCL, NEXUS, ClawBreak, Telegram, Slack, PWA, and Android all hit the same brain.
