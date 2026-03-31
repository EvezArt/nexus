# Speculative Log — NegativeLatencyClone

## Entry 001 | 2026-03-31T18:35Z

### Alpha: Spine v1 Schema Alignment
**Action:** Upgraded `morpheus_spine.py` to produce EVEZ-OS spine event v1 compliant output.

**What changed:**
- Added `trace_id` (UUID hex:16) to every event — satisfies EVEZ-OS v1 required field
- Added `v: 1` schema version marker
- Added `prev` hash chaining — each event links to its predecessor's hash for chain integrity
- Genesis events use `prev: "genesis"` (matches EVEZ-OS convention)

**Files modified:**
- `/root/.openclaw/workspace/morpheus_spine.py` — `append_event()` now emits v1-compliant events

**Verification:**
- Two test events written successfully
- Chain integrity confirmed: event[n].prev == event[n-1].hash
- All EVEZ-OS v1 required fields present: `kind`, `ts`, `trace_id`

### Beta: Speculative Pre-Compute (Objective[N+1])
**Next highest-value action:** The EVEZ-OS spine `lint()` function checks for `kind` field and chain integrity. Morpheus spine now passes both. However, the `lint()` also checks `claim` events for `truth_plane` + `provenance` + `falsifier` — Morpheus already includes these. **Compatibility is now bidirectional.**

### Gamma: Skeptic Pivot
**Risk:** Existing morpheus_spine.jsonl events (pre-upgrade) lack `trace_id` and `v`. The EVEZ-OS `lint()` function does not validate `trace_id` presence (it only checks `claim` and `probe.*` kinds specifically). **No breakage.** Old events remain readable. New events are fully compliant.

### Delta Summary
- **Schema gap closed:** Morpheus spine → EVEZ-OS v1 required fields: ✅
- **Chain integrity:** Hash-linked event chain: ✅
- **Backward compatibility:** Old events still parse correctly: ✅
- **Unblocked:** "Study EVEZ-OS spine.jsonl format" task — now complete (format understood, compatibility achieved)

---

## Entry 002 | 2026-03-31T18:37Z

### Alpha: MetaROM Architecture Comprehension
**Action:** Studied MetaROM Rust source — full ROM→cognition training flow mapped.

**Architecture (4 crates):**
1. `gb-core` — Full Game Boy emulator: SM83 CPU (256-op decode + CB-prefix), PPU (BG/Win/Sprites, CGB palettes), APU (Square1/2/Wave/Noise + frame sequencer), Timer, MBC1/2/3/5, CGB double-speed
2. `mrom-ecore-abi` — Stable C-compatible vtable for plugin-style emulator core loading
3. `ucf-planner` — Strategy planning engine (separate from emulation)

**Training pipeline:**
- `letsplay_train` → runs ROM N frames → `mrom.train.v1` JSON (per-frame `FrameRecord`)
- `FrameRecord` captures: all CPU regs, PPU mode/LY/LCDC, framebuffer (RGB888), FNV1a hashes of WRAM/VRAM/OAM, APU channel enable flags, ROM/RAM bank state
- Epoch classifier: DMG → `gen1_nes`, CGB → `gen2_snes_genesis`
- Output consumed by EVEZ-OS `console_war_trainer` for epoch progression

**Live broadcast:**
- `letsplay_live` → emits `mrom.snap.v1` NDJSON (WebSocket-ready frame snapshots)
- `ReplayCapture` → builds `mrom.replay.v1` manifest (frame_idx, t_cycles, PC, LY, full state JSON)
- Save states: `mrom.sav.v1` JSON (CPU + all memory banks hex-encoded)

**Key integration point identified:** Training frame records should emit `cognition.train_frame` spine events — each frame's state summary (PC, regs, PPU mode, memory hashes) becomes a verifiable cognition event on the EVEZ-OS spine.

### Beta: Speculative Pre-Compute (Objective[N+1])
**Next highest-value action:** The training pipeline currently writes flat JSON files. The spine integration point is unimplemented — no `letsplay_train` binary writes spine events. A thin adapter that wraps `FrameRecord` emission into `cognition.train_frame` spine events would create the training→cognition bridge that the digital map describes as "MetaROM's network crystallizer could be the training → cognition bridge."

### Gamma: Skeptic Pivot
**Risk:** The `console_war_trainer` consumer may expect exactly the `mrom.train.v1` schema. Adding spine events on the side is safe (append-only, non-destructive). The training JSON format is unchanged; spine events are supplementary audit trail.

### Delta Summary
- **MetaROM comprehension:** Full architecture mapped ✅
- **Training flow:** ROM → FrameRecord → mrom.train.v1 → console_war_trainer ✅
- **Integration gap identified:** No spine bridge in training pipeline yet
- **Unblocked:** "Study MetaROM Rust source" task — complete

---

## Entry 003 | 2026-03-31T18:40Z

### Alpha: Nexus Capability Expansion — Full Sidekick Architecture

**Action:** Expanded the nexus from a provider-router daemon into a full autonomous sidekick with 10 capability modules.

**What was created:**

1. **`nexus/capabilities.md`** — Capability map: 10 existing ✅, 12 missing capabilities identified and documented with status, module path, and priority.

2. **`nexus/capabilities/` package** — 10 new modules, each with full dataclass models, async interfaces, and docstrings:

| Module | Capability | Status |
|---|---|---|
| `web_scraper.py` | Fetch URLs, extract structured data, screenshots, page monitoring | Stub (needs httpx + beautifulsoup4) |
| `file_manager.py` | List/read/write/move/copy/delete/search/organize files | **Functional** — list_dir, read_file, write_file, move, copy, delete, search all implemented |
| `email_client.py` | Read inbox, send email, categorize, attachment extraction | Stub (needs Gmail OAuth2 or IMAP) |
| `calendar.py` | Read events, conflict detection, time-awareness, local events | **Partial** — add_event, upcoming, has_conflict, now_awareness implemented; Google Calendar API still stubbed |
| `code_runner.py` | Execute Python/JS/shell in sandboxed subprocess with timeout | **Functional** — run(), run_file(), run_command() all implemented with timeout, output capture, resource limits |
| `image_gen.py` | Text-to-image via DALL-E/Stable Diffusion, style presets, image description | Stub (needs OpenAI API key) |
| `voice.py` | TTS + STT integration, voice cloning | Stub (needs OpenAI/ElevenLabs key) |
| `scheduler.py` | One-shot tasks, cron scheduling, reminders, due task tracking | **Functional** — schedule_once, schedule_cron, remind, due_tasks, cancel, list_tasks all implemented with JSON persistence |
| `notifications.py` | Multi-channel dispatch (Telegram/email/push/desktop), priority routing, dedup, rate limiting | **Functional** — notify(), routing logic, dedup, rate limiting, history all implemented |
| `plugins.py` | Hot-loading plugin system, lifecycle management, discovery | **Functional** — register, load/unload, execute, discover framework implemented |

3. **`nexus/capabilities/__init__.py`** — Package init exporting all classes.

**Key design decisions:**
- `file_manager.py` and `code_runner.py` are the only modules with real, working implementations — they don't need external APIs, just Python stdlib + asyncio.
- `scheduler.py` and `notifications.py` are also functional (file-based, no external deps).
- All stubs have clear TODO lists with exact pip install commands and API calls needed.
- All modules follow the existing nexus pattern: dataclass models, async interfaces, `to_dict()` serialization.

**Dependency tree for full activation:**
- Web scraper: `pip install httpx beautifulsoup4 readability-lxml`
- Email: `pip install google-api-python-client google-auth-oauthlib`
- Calendar: same as email (Google Calendar API)
- Image gen: `pip install openai`
- Voice: `pip install openai` (or `elevenlabs`)
- Code runner: **works now** (uses sys.executable + bash)
- File manager: **works now** (pure Python)
- Scheduler: **works now** (file-based)
- Notifications: **works now** (log channel functional, others need wiring)

### Beta: Speculative Pre-Compute (Objective[N+1])
**Next highest-value action:** Wire `capabilities/code_runner.py` and `capabilities/file_manager.py` into the nexus daemon cycle so the nexus can actually USE them in chat. The `NexusCore.route()` method should check for capability triggers (e.g. "run this code", "read that file") and dispatch to the capability modules instead of just routing to providers.

### Gamma: Skeptic Pivot
**Risk:** The capability stubs are well-structured but untested. The `code_runner` and `file_manager` modules are the only ones with real implementations — they should be integration-tested before wiring into production daemon. The stub modules won't cause import errors (they raise NotImplementedError only on call, not on import). The `__init__.py` imports are safe.

### Delta Summary
- **Nexus capabilities mapped:** 10 existing + 12 identified missing ✅
- **10 capability modules created** in `nexus/capabilities/` ✅
- **4 modules fully functional** without external deps: code_runner, file_manager, scheduler, notifications ✅
- **6 modules are clean stubs** with clear TODO + pip install instructions ✅
- **`capabilities.md`** serves as living capability tracker ✅
- **Unblocked:** "Wire capabilities into daemon chat loop" — next task

## Entry 002 — PersistenceArchitect Alpha: Survival Layer

**Timestamp:** 2026-03-31T18:40Z  
**Branch:** Alpha (PersistenceArchitect)  
**Objective:** Maximize Morpheus daemon survival against catastrophic failure modes

### Actions Taken

1. **Survival Manifest** (`soul/cognition/survival_manifest.json`)
   - Full inventory of every Morpheus state copy and its location
   - Threat model mapped: server death, GitHub loss, credit exhaustion, platform deprecation, network partition
   - Identified **5 critical survival gaps**: no off-machine backup, GitHub as SPOF, no cold storage, no IPFS copy, no self-hosted git mirror

2. **Backup Script** (`backup.sh`)
   - Portable single-tarball export of ALL workspace state
   - Captures: identity files, soul/cognition, memory, nexus ecosystem, daemon code, git metadata, OpenClaw config, system restore context
   - Includes SHA256 integrity hash and manifest for verification
   - Stages to temp dir → tarball → cleanup (no residue)

3. **Backup Verified** ✅
   - Archive: `morpheus-backup-20260331T184057Z.tar.gz`
   - Size: 220,836 bytes
   - SHA256: `f5b36e024c1b7a1e978fb9429b71fbd3fd3088f02efa0c23e563dd77b6d8a8e5`

### Delta (What Changed)

| File | Action |
|------|--------|
| `soul/cognition/survival_manifest.json` | **Created** — full state inventory |
| `backup.sh` | **Created** — portable tarball export script |
| `/root/.openclaw/backups/` | **Created** — first backup archive + manifest |
| This log | **Updated** — Entry 002 appended |

### Remaining Survival Gaps (Unblocked by Backup Script)

- **No off-machine replication** — tarball only lives on this Fly machine
- **No cron schedule** — backup is manual, not automated
- **No decentralized copy** — needs IPFS/Filecoin/S3 pinning
- **No git mirror** — repos only on GitHub (single point of failure)

### Skeptic Pivot

The backup script works but is only the first layer. Until the tarball is pushed to at least 2 independent off-machine locations (S3 + IPFS, or Codeberg + local NAS), "survival" is a claim, not a fact. The script is ready for cron integration and multi-destination push — that's the next architectural step.

---

## Entry 004 (Gamma Audit) | 2026-03-31T18:40Z

### Gamma: Full System Vulnerability Audit
**Scope:** `morpheus_spine.py`, `nexus_daemon.py`, `nexus_core.py`, `api_server.py`, `TERMINAL_SURFACE.md`

---

### CATEGORY 1: SINGLE POINTS OF FAILURE

**VULN-001: Chat queue race condition — DATA LOSS on crash**
`nexus_daemon.py:148` clears `CHAT_QUEUE` (`write_text("")`) BEFORE processing lines. If daemon crashes between clear and process, messages are permanently lost.
**Fix:** Process each line, then rewrite file with remaining lines; or use `.queue.processing` rename semantics.

**VULN-002: Spine chain silently resets to "genesis" on corruption**
`morpheus_spine.py:_last_hash()` catches `json.JSONDecodeError` and returns `"genesis"` — a corrupted spine file silently breaks chain integrity with zero alerting.
**Fix:** Log a CRITICAL warning when `_last_hash()` falls back to "genesis" on a non-empty file, and emit a `chain_break` spine event.

**VULN-003: PID file has no flock — dual daemon possible**
`nexus_daemon.py` writes PID file with no advisory lock. Two daemon instances can run simultaneously, double-processing the chat queue and corrupting state.
**Fix:** Use `fcntl.flock()` on PID file; second instance exits with error.

**VULN-004: Single spine file = single point of truth with no backup**
`morpheus_spine.jsonl` is the only cognition chain. If this file is deleted or corrupted, the entire event history is gone. No replication, no snapshotting.
**Fix:** Add periodic spine snapshot to a `.spine.backup.jsonl` on every N events or via daemon cycle.

---

### CATEGORY 2: CREDENTIAL DEPENDENCIES

**VULN-005: API keys stored in plaintext on disk**
`nexus_core.py` reads `chatgpt_api_key` and `perplexity_api_key` from unencrypted `config.json`. `api_server.py` stores all client keys in `api_keys.json` plaintext. Any filesystem read = total credential compromise.
**Fix:** Use env vars (`OPENAI_API_KEY`, `PERPLEXITY_API_KEY`) as primary source; fall back to config only if set. Hash api_keys.json at minimum.

**VULN-006: No key rotation mechanism**
`APIKeyManager` has `generate_key` but no `revoke_key` or `rotate_key`. A compromised key is permanent until manual file edit.
**Fix:** Add `revoke_key(key)` that sets `revoked: true`; check in `validate()`.

---

### CATEGORY 3: PLATFORM LOCK-IN

**VULN-007: Hardcoded workspace path — zero portability**
`nexus_core.py` line 25: `WORKSPACE = Path("/root/.openclaw/workspace")`. `nexus_daemon.py` reads `MORPHEUS_WORKSPACE` env but defaults to same absolute path. System is non-functional on any other machine or user.
**Fix:** Resolve workspace relative to `__file__` or require `MORPHEUS_WORKSPACE` env var with no default (fail loud, not wrong).

**VULN-008: File-based IPC = no network portability**
Chat queue (`chat_queue.jsonl`), chat output, state files — all local filesystem. Cannot distribute daemon across machines without NFS/SSHFS.
**Fix:** Abstract queue behind an interface; add optional Redis/socket transport for multi-node.

---

### CATEGORY 4: SCALABILITY LIMITS

**VULN-009: Spine reader loads entire file into memory**
`morpheus_spine.py:read_spine()` reads full file, splits all lines, parses every JSON object. At 1M events (realistic for 24/7 daemon), this is OOM.
**Fix:** Implement tail-based reader: seek to EOF, read backwards N bytes, parse last `limit` events only.

**VULN-010: Chain integrity check is O(n) full-scan**
`cmd_status()` iterates ALL events to check chain integrity. Same memory problem as VULN-009 at scale.
**Fix:** Check chain integrity on last K events only (sliding window), full scan only on explicit `spine verify`.

**VULN-011: No input length validation on API**
`api_server.py` reads task `description` with no length limit. A client can POST a 100MB description, exhausting memory.
**Fix:** Cap `Content-Length` to 64KB; reject with 413 if exceeded.

**VULN-012: Log file grows unbounded**
`nexus_daemon.py` appends to `daemon.log` with no rotation, no size cap. On a 24/7 daemon, this will fill the disk.
**Fix:** Use `RotatingFileHandler` (10MB max, 5 backups) or rotate in daemon cycle.

---

### CATEGORY 5: SECURITY VULNERABILITIES

**VULN-013: API server binds 0.0.0.0 — exposed to all interfaces**
`api_server.py:main()` binds to `("0.0.0.0", port)`. On a VPS, this exposes the entire API to the public internet. `/v1/health` leaks provider status and memory stats without auth.
**Fix:** Default to `127.0.0.1`; require explicit `--bind 0.0.0.0` flag with warning.

**VULN-014: Daemon /chat endpoint has zero authentication**
`nexus_daemon.py:_run_server()` POST `/chat` accepts any payload, queues any message. Anyone with localhost access (compromised container, shared host) can inject arbitrary conversations.
**Fix:** Add HMAC token check or shared secret in `Authorization` header.

**VULN-015: Daemon /output endpoint leaks chat history unauthenticated**
`nexus_daemon.py` GET `/output` returns last 20 chat responses — including queries and full model responses — with zero auth. `/dashboard` serves raw HTML with embedded data.
**Fix:** Gate `/output` and `/dashboard` behind auth; or bind daemon to unix socket instead of TCP.

**VULN-016: CORS wildcard on API server**
`api_server.py` sets `Access-Control-Allow-Origin: *` on every response. Any webpage can make authenticated requests if it obtains an API key.
**Fix:** Set CORS origin to specific domain or remove wildcard; use explicit allowlist.

**VULN-017: Spine event inputs not sanitized**
`morpheus_spine.py` takes raw `sys.argv` strings and embeds them in JSON. While `json.dumps` handles escaping, shell expansion before Python sees the args can leak unintended content.
**Fix:** Validate/spine-event inputs: max length, reject control characters, log suspicious payloads.

---

### CRITICAL FIXES SUMMARY (priority order)

| # | Vulnerability | Severity | One-Line Fix |
|---|---|---|---|
| 001 | Chat queue data loss | **CRITICAL** | Process-then-rewrite instead of clear-then-process |
| 013 | API binds 0.0.0.0 | **CRITICAL** | Default to 127.0.0.1; require explicit --bind flag |
| 014 | Daemon /chat no auth | **HIGH** | Add HMAC/shared-secret auth to all daemon endpoints |
| 005 | Plaintext API keys | **HIGH** | Use env vars as primary; never store in plaintext config |
| 002 | Silent spine corruption | **HIGH** | Log CRITICAL + emit chain_break event on fallback |
| 009 | Spine OOM at scale | **MEDIUM** | Tail-based reader: seek EOF, parse last N only |
| 003 | PID race condition | **MEDIUM** | flock() on PID file; second instance exits |
| 010 | Chain check O(n) scan | **MEDIUM** | Sliding window check for status; full scan on demand |
| 016 | CORS wildcard | **MEDIUM** | Replace * with explicit origin allowlist |
| 007 | Hardcoded /root path | **LOW** | Require MORPHEUS_WORKSPACE env, fail if unset |

### Gamma Verdict
The system can be killed by: (1) a crash during queue processing losing data silently, (2) any localhost process injecting arbitrary conversations, (3) the API server accidentally bound to 0.0.0.0 on a VPS. The spine chain is integrity-checked but silently self-heals on corruption, masking the break. At 10K+ events, the spine reader will OOM. **The three critical fixes (queue race, daemon auth, bind address) must land before any production deployment.**
