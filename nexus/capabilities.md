# Nexus Capabilities Map

> Autonomous sidekick status — what we have, what we need, what's in progress.
> Generated: 2026-03-31T18:40Z

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Implemented & functional |
| 🔧 | Partially implemented / needs work |
| 📝 | Stub / scaffold exists |
| ❌ | Missing — needs implementation |
| 💡 | Concept only |

---

## Current Capabilities (Implemented)

### Core Architecture
- ✅ **Provider Router** — Smart routing to best provider per task type (`nexus_core.py`)
- ✅ **Provider Chain** — Fallback chains when providers fail
- ✅ **Multi-Provider Chat** — ChatGPT, Perplexity, OpenClaw Bridge providers
- ✅ **Provider Health Checks** — Error counting, token tracking, status reporting
- ✅ **Base Provider Interface** — Normalized `Message`/`ProviderResponse` across all providers

### Daemon & Runtime
- ✅ **24/7 Daemon** — Background process with periodic cycles (`nexus_daemon.py`)
- ✅ **Signal Handling** — Graceful SIGTERM/SIGINT shutdown
- ✅ **Auto-Recovery** — Cycle failure tracking, auto-restart
- ✅ **State Persistence** — Daemon state saved/restored across restarts

### Memory System
- ✅ **Unified Memory Store** — Provider-agnostic memory across all channels (`memory_store.py`)
- ✅ **Spine Integration** — Append-only JSONL event log for tamper evidence
- ✅ **Daily Logs** — Human-readable markdown daily summaries
- ✅ **Session Memory** — Active conversation context

### Revenue / Income
- ✅ **Income Engine** — Task execution pipeline for revenue generation (`income_engine.py`)
- ✅ **API Server** — Monetized HTTP API for task submission (`api_server.py`)
- ✅ **API Key Management** — Tiered access (free/basic/pro/enterprise)
- ✅ **Rate Limiting** — Per-tier daily task limits
- ✅ **Per-Task Pricing** — research/writing/coding/analysis/trading tiers
- ✅ **Freelancer** — Automated freelance task completion (`freelance.py`)
- ✅ **Revenue Maximizer** — Revenue stream management (`revenue/revenue_maximizer.py`)
- ✅ **Solana Payments** — Crypto payment integration (`revenue/solana_payments.py`)

### Entity System
- ✅ **Entity Spawner** — Generate entities from templates (`revenue/entity_spawner.py`)
- ✅ **Entity Manifest** — 20+ entities tracked in `entities/manifest.json`

### Integrations
- ✅ **Telegram Bot** — Remote task submission and notifications (`telegram_bot.py`)
- ✅ **Cloudflare Workers** — Edge deployment support (`cloudflare/README.md`)

### Content
- ✅ **Content Library** — Pre-built posts for Reddit, Dev.to, HN, Twitter, grants

---

## Missing Capabilities (Needed for "Ultimate Sidekick")

### 1. Web Scraping — ❌ MISSING
**Status:** No scraping module exists.
**Need:** Fetch, parse, and extract structured data from arbitrary URLs.
**Priority:** HIGH — core utility for research, monitoring, price tracking.

### 2. File Management — ❌ MISSING
**Status:** No file manager module.
**Need:** List, read, write, move, organize files across workspace. Bulk operations, search.
**Priority:** HIGH — essential for working with user files.

### 3. Email Integration — ❌ MISSING
**Status:** No email module.
**Need:** Read inbox, send emails, manage labels/filters, extract attachments.
**Priority:** HIGH — autonomous sidekick needs inbox awareness.

### 4. Calendar Awareness — ❌ MISSING
**Status:** No calendar module.
**Need:** Read upcoming events, detect conflicts, proactive reminders, schedule awareness.
**Priority:** HIGH — proactive assistant needs time awareness.

### 5. Code Execution — ❌ MISSING
**Status:** No sandboxed code runner.
**Need:** Execute user code safely (Python/JS/shell), capture output, timeout protection.
**Priority:** HIGH — "do anything" means running code.

### 6. Image Generation — ❌ MISSING
**Status:** No image gen module.
**Need:** Generate images from text prompts via API (DALL-E, Stable Diffusion, etc).
**Priority:** MEDIUM — visual content creation.

### 7. Voice/TTS Integration — ❌ MISSING
**Status:** No TTS module (OpenClaw has native TTS, but nexus doesn't wire it).
**Need:** Text-to-speech output, voice input transcription.
**Priority:** MEDIUM — multimodal interaction.

### 8. Database/Knowledge Base — ❌ MISSING
**Status:** Flat JSON/JSONL only. No proper DB.
**Need:** Structured query, relationships, fast lookup beyond flat files.
**Priority:** MEDIUM — scales better than file-based memory.

### 9. Task Scheduler — ❌ MISSING
**Status:** Daemon has periodic cycles but no user-facing scheduler.
**Need:** Schedule arbitrary tasks at specific times, cron-like behavior, one-shot reminders.
**Priority:** MEDIUM — proactive sidekick scheduling.

### 10. Notification System — ❌ MISSING
**Status:** Only Telegram. No unified notification dispatch.
**Need:** Route alerts to Telegram/email/push/desktop based on urgency.
**Priority:** MEDIUM — multi-channel awareness.

### 11. Plugin/Extension System — ❌ MISSING
**Status:** Providers are hardcoded. No hot-loading.
**need:** Dynamic provider/capability registration without restart.
**Priority:** LOW — extensibility for future growth.

### 12. Web Dashboard — 🔧 PARTIAL
**Status:** `dashboard.html` and `landing.html` exist but are static.
**Need:** Live dashboard showing daemon status, active tasks, revenue, health.
**Priority:** LOW — nice-to-have visibility layer.

---

## Capability Matrix

| Capability | Status | Module |
|---|---|---|
| Provider routing | ✅ | `nexus_core.py` |
| Multi-provider chat | ✅ | `providers/` |
| 24/7 daemon | ✅ | `nexus_daemon.py` |
| Memory system | ✅ | `memory_store.py` |
| Income engine | ✅ | `income_engine.py` |
| API server | ✅ | `api_server.py` |
| Freelancer | ✅ | `freelance.py` |
| Telegram bot | ✅ | `telegram_bot.py` |
| Entity spawner | ✅ | `revenue/entity_spawner.py` |
| Solana payments | ✅ | `revenue/solana_payments.py` |
| Web scraping | ❌ | `capabilities/web_scraper.py` |
| File management | ❌ | `capabilities/file_manager.py` |
| Email integration | ❌ | `capabilities/email_client.py` |
| Calendar awareness | ❌ | `capabilities/calendar.py` |
| Code execution | ❌ | `capabilities/code_runner.py` |
| Image generation | ❌ | `capabilities/image_gen.py` |
| Voice/TTS | ❌ | `capabilities/voice.py` |
| Task scheduler | ❌ | `capabilities/scheduler.py` |
| Notification dispatch | ❌ | `capabilities/notifications.py` |
| Plugin system | ❌ | `capabilities/plugins.py` |
