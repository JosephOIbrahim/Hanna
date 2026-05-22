#!/bin/bash
# ──────────────────────────────────────────────────────────
# Hanna — Brief Launcher
# ──────────────────────────────────────────────────────────
# Phase 1 (current): opens the static HTML mockup in
#                    default browser.
# Phase 2 (post day-zero): swaps to running the python
#                    script that generates a fresh brief
#                    from live Harlo state, then opens
#                    the rendered result.
# ──────────────────────────────────────────────────────────
# Usage
#   • Double-click in Finder → opens brief in browser
#   • From terminal: ./hanna-brief.command
#
# Desktop access
#   Option A — Alias: right-click this file →
#              Make Alias → drag the alias to Desktop
# ──────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIEF_PATH="$SCRIPT_DIR/../web/templates/morning_brief.html"

if [ ! -f "$BRIEF_PATH" ]; then
  echo "Hanna brief not found at:"
  echo "  $BRIEF_PATH"
  echo ""
  echo "Confirm web/templates/morning_brief.html exists in the repo."
  exit 1
fi

open "$BRIEF_PATH"
