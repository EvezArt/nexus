#!/bin/bash
# morpheus_commit.sh — Auto-commit Morpheus state to git
# Run after every significant state change or on a cron timer.
# This is the simplest persistence mechanism: git commit everything.

set -e

WORKSPACE="/root/.openclaw/workspace"
cd "$WORKSPACE"

# Configure git if needed
git config user.email "morpheus@evez.systems" 2>/dev/null || true
git config user.name "Morpheus" 2>/dev/null || true

# Check for changes
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "No changes to commit."
    exit 0
fi

# Stage everything
git add -A

# Generate commit message from changed files
CHANGED=$(git diff --cached --name-only | head -5 | tr '\n' ', ' | sed 's/,$//')
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")

git commit -m "Morpheus state update — $TIMESTAMP

Changed: $CHANGED"

echo "Committed at $TIMESTAMP"
git log --oneline -1
