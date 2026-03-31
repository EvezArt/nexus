# HEARTBEAT.md

## Periodic Checks (rotate through, 2-4 per day)

### 1. Spine Health
- Run `python3 morpheus_spine.py status` — check chain integrity, event count
- If chain broken → emit chain_break event, alert Steven
- If no events in >2h while daemon running → investigate

### 2. Daemon Health  
- Check `nexus/daemon_state.json` last_cycle timestamp
- If >10min stale → daemon may be hung, check PID file + process
- Check error count — if rising, investigate provider issues

### 3. Disk Space
- Check workspace size, spine file size
- If spine >10MB → consider archival
- If disk >80% → alert

### 4. Git Sync
- Check for uncommitted changes >30min old
- Auto-commit if safe (no secrets in diff)

### 5. Memory Maintenance (weekly)
- Review recent `memory/YYYY-MM-DD.md` files
- Distill significant events into MEMORY.md
- Clean outdated info

## Rules
- Never interrupt Steven during active conversation
- Quiet hours: 23:00-08:00 UTC (unless spine broken or daemon dead)
- Batch checks — don't fire API calls for each item separately
