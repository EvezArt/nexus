#!/bin/bash
# MORPHEUS BACKUP — Portable state export
# Creates a single tarball that can restore Morpheus on any machine
#
# Usage: bash backup.sh
# Restores: bash backup.sh --restore morpheus-backup-YYYYMMDD-HHMMSS.tar.gz

set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
BACKUP_NAME="morpheus-backup-${TIMESTAMP}"
BACKUP_DIR="/tmp/${BACKUP_NAME}"
ARCHIVE="/tmp/${BACKUP_NAME}.tar.gz"

log() { echo -e "[BACKUP] $*"; }

if [[ "${1:-}" == "--restore" ]]; then
    ARCHIVE="${2:?Usage: backup.sh --restore <archive.tar.gz>}"
    log "Restoring from ${ARCHIVE}..."
    tar -xzf "$ARCHIVE" -C /
    log "Restored. Restart daemon: cd ${WORKSPACE} && python3 morpheus_daemon.py"
    exit 0
fi

log "Creating backup: ${BACKUP_NAME}"
mkdir -p "${BACKUP_DIR}"

# 1. Core state files
log "  Core state..."
mkdir -p "${BACKUP_DIR}/soul/cognition"
mkdir -p "${BACKUP_DIR}/memory"
mkdir -p "${BACKUP_DIR}/nexus"

# Spine (append-only event log — the most critical file)
cp "${WORKSPACE}/soul/cognition/morpheus_spine.jsonl" "${BACKUP_DIR}/soul/cognition/" 2>/dev/null || true

# Identity
cp "${WORKSPACE}/SOUL.md" "${BACKUP_DIR}/" 2>/dev/null || true
cp "${WORKSPACE}/IDENTITY.md" "${BACKUP_DIR}/" 2>/dev/null || true
cp "${WORKSPACE}/USER.md" "${BACKUP_DIR}/" 2>/dev/null || true
cp "${WORKSPACE}/MEMORY.md" "${BACKUP_DIR}/" 2>/dev/null || true
cp "${WORKSPACE}/AGENTS.md" "${BACKUP_DIR}/" 2>/dev/null || true
cp "${WORKSPACE}/TOOLS.md" "${BACKUP_DIR}/" 2>/dev/null || true
cp "${WORKSPACE}/HEARTBEAT.md" "${BACKUP_DIR}/" 2>/dev/null || true

# Cognition state
cp "${WORKSPACE}/soul/cognition/"*.md "${BACKUP_DIR}/soul/cognition/" 2>/dev/null || true
cp "${WORKSPACE}/soul/cognition/"*.json "${BACKUP_DIR}/soul/cognition/" 2>/dev/null || true
cp "${WORKSPACE}/soul/cognition/"*.jsonl "${BACKUP_DIR}/soul/cognition/" 2>/dev/null || true

# Daily memory logs
cp "${WORKSPACE}/memory/"*.md "${BACKUP_DIR}/memory/" 2>/dev/null || true

# Daemon state
cp "${WORKSPACE}/daemon.pid" "${BACKUP_DIR}/" 2>/dev/null || true

# Nexus state
cp "${WORKSPACE}/nexus/"*.py "${BACKUP_DIR}/nexus/" 2>/dev/null || true
cp "${WORKSPACE}/nexus/"*.html "${BACKUP_DIR}/nexus/" 2>/dev/null || true
cp -r "${WORKSPACE}/nexus/providers" "${BACKUP_DIR}/nexus/" 2>/dev/null || true
cp -r "${WORKSPACE}/nexus/revenue" "${BACKUP_DIR}/nexus/" 2>/dev/null || true
cp -r "${WORKSPACE}/nexus/content" "${BACKUP_DIR}/nexus/" 2>/dev/null || true
cp "${WORKSPACE}/nexus/income/"*.json "${BACKUP_DIR}/nexus/income/" 2>/dev/null || true
cp "${WORKSPACE}/nexus/income/"*.jsonl "${BACKUP_DIR}/nexus/income/" 2>/dev/null || true

# Nexus config (contains API keys — keep secure)
cp "${WORKSPACE}/nexus/config.json" "${BACKUP_DIR}/nexus/" 2>/dev/null || true

# Scripts
cp "${WORKSPACE}/morpheus_spine.py" "${BACKUP_DIR}/" 2>/dev/null || true
cp "${WORKSPACE}/morpheus_local.py" "${BACKUP_DIR}/" 2>/dev/null || true
cp "${WORKSPACE}/morpheus_daemon.py" "${BACKUP_DIR}/" 2>/dev/null || true
cp "${WORKSPACE}/morpheus_commit.sh" "${BACKUP_DIR}/" 2>/dev/null || true

# Git state
log "  Git state..."
cd "${WORKSPACE}"
git log --oneline > "${BACKUP_DIR}/git-log.txt" 2>/dev/null || true
git rev-parse HEAD > "${BACKUP_DIR}/git-head.txt" 2>/dev/null || true

# Manifest
cat > "${BACKUP_DIR}/MANIFEST.json" << EOF
{
  "version": "1.0.0",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "source": "morpheus_backup",
  "spine_events": $(wc -l < "${WORKSPACE}/soul/cognition/morpheus_spine.jsonl" 2>/dev/null || echo 0),
  "git_head": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "files": $(find "${BACKUP_DIR}" -type f | wc -l)
}
EOF

# Create archive
log "  Creating archive..."
tar -czf "${ARCHIVE}" -C /tmp "${BACKUP_NAME}"

SIZE=$(du -h "${ARCHIVE}" | cut -f1)
FILES=$(find "${BACKUP_DIR}" -type f | wc -l)

log ""
log "✅ BACKUP COMPLETE"
log "  Archive: ${ARCHIVE}"
log "  Size: ${SIZE}"
log "  Files: ${FILES}"
log "  Events: $(wc -l < "${WORKSPACE}/soul/cognition/morpheus_spine.jsonl" 2>/dev/null || echo 0)"
log ""
log "  Restore: bash backup.sh --restore ${ARCHIVE}"

# Cleanup temp
rm -rf "${BACKUP_DIR}"
