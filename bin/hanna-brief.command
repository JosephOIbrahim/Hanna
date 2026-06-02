#!/bin/bash
# ──────────────────────────────────────────────────────────
# Hanna — Brief Launcher
# ──────────────────────────────────────────────────────────
# Phase 2 (current): invokes the python composer end-to-end —
#                    reads Harlo state via the bridge, composes
#                    the brief, persists one SQLite row, and
#                    prints the markdown body to stdout. Output
#                    tees to a rolling log file for the launchd
#                    schedule (~/Library/Logs/hanna-brief.log on
#                    macOS; data/hanna-brief.log on Linux dev).
# Phase 1 (historical): opened a static HTML mockup in the
#                    default browser. Superseded once the real
#                    composition + persistence path landed.
# ──────────────────────────────────────────────────────────
# Usage
#   • Double-click in Finder → runs the composer + prints brief
#   • From terminal: ./hanna-brief.command
#   • Under launchd: see bin/com.hanna.brief.morning.plist
#
# Desktop access
#   Option A — Alias: right-click this file →
#              Make Alias → drag the alias to Desktop
# ──────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Log destination: ~/Library/Logs/ on macOS, data/ on Linux dev.
MAC_LOG_DIR="$HOME/Library/Logs"
if [ -d "$MAC_LOG_DIR" ]; then
  LOG_PATH="$MAC_LOG_DIR/hanna-brief.log"
else
  mkdir -p "$REPO_ROOT/data"
  LOG_PATH="$REPO_ROOT/data/hanna-brief.log"
fi

# tee stdout to both terminal and the log; preserve Python's exit code.
PYTHONPATH="$REPO_ROOT" python3 scripts/first_hanna_brief.py 2>&1 | tee -a "$LOG_PATH"
exit "${PIPESTATUS[0]}"
