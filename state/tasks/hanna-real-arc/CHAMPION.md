# CHAMPION.md — current best artifact

**Updated:** 2026-05-25 (DELIBERATE/EXECUTE cycle 1 — Line A promoted)
**Champion-id:** `arc-cycle1-line-A-a2d64cd` (supersedes `seed-2118024`)
**Promotion rule (per harness OP6):** strict increase ≥1 predicate; no regression on others; stochastic gains require replication.

## What it is

The current champion is the result of cycle-1 Line A landing — commit `a2d64cd` on `claude/hanna-mcp-review-ZsorY`. L4b's Calendar channel (`src/channels/calendar.py`) is shipped with all R1–R5 mitigations from the FORUM critique; SQLite gains reconciliation columns; 4 sibling launchd `.plist`s author the full D010 anchor schedule; 22 new tests cover the publish/archive surface and the reconciliation invariant.

## Reproduction recipe

```bash
git clone https://github.com/JosephOIbrahim/Hanna
cd Hanna
git checkout claude/hanna-mcp-review-ZsorY
git rev-parse HEAD                                       # → a2d64cd…
python3 -m pip install -e ".[dev]"
python3 -m pytest tests/ -q                              # → 139 passed
python3 -c "from src.channels.calendar import publish, archive, HannaCalendarNotAvailable, HannaCalendarNotFound, HannaCalendarPermissionRequired, HannaCalendarPublishFailed; print('OK')"
PYTHONPATH=. python3 scripts/first_hanna_brief.py        # exits 0 on Linux (unpublished_reason="non_macos") or "Hanna paused" on lockout
```

## Predicate score (delta vs `seed-2118024`)

| P | Predicate | Before | After | Δ | Rationale |
|---|---|---|---|---|---|
| P1 | 10 MCP tools callable from session | 0.00 | 0.00 | — | L6 lane untouched |
| P2 | calendar publish + idempotency | 0.40 | **0.85** | +0.45 | publish+archive code lands; L1+L2 verifiers green; L3+L4 require Joe's Mac |
| P3 | hanna_log appends to product file | 0.10 | 0.10 | — | L6 lane untouched |
| P4 | Octavius spawn/poll/harvest | 0.00 | 0.00 | — | held pending q017 close |
| P5 | LockoutResponse on lockout | 0.20 | **0.50** | +0.30 | D014 ratified (shape decided); L6 implementation pending |
| P6 | reconciliation invariant | 0.10 | **0.70** | +0.60 | columns + XOR invariant tests pass at L2 |
| P7 | ≥200 tests | 0.59 | **0.70** | +0.11 | 139/200 = 0.70 |
| P8 | CI grep matrix passes | 1.00 | 1.00 | — | preserved |
| P9 | restart survival | 0.30 | **0.50** | +0.20 | 4 sibling .plists land; sleep/wake still untested |
| P10 | 7-day real-Mac trial | 0.00 | 0.00 | — | requires Joe's hardware |

**Champion score:** 0.27 → **0.435** (43.5% of full SPEC). 

## What's now true that wasn't on `seed-2118024`

- L4b ships: `src/channels/calendar.py` with D006/D010/D011/D012/D014 contracts honored end-to-end on the L1+L2 verifier surface.
- 4 sibling launchd `.plist`s extend Phase 5's MORNING demonstrator to the full D010 anchor schedule.
- `briefs` SQLite gains `calendar_event_uid` + `unpublished_reason` columns via idempotent ALTER migration.
- D014 ratifies LockoutResponse shape (q002 closed).
- D015 ratifies composition boundary (q007 closed).
- D016 records Octavius reachability finding (q016 closed; q017 raised).
- bin/README.md documents the macOS permission grant + the manual Hanna/Hanna · Archive calendar creation + the .plist install commands.

## Promotion provenance

- Line A worker → 11 files changed, +1,595/−17 lines, 22 new tests, all R1–R5 mitigations baked in.
- critic[verify] PASS 36/36 against the FORUM-rated acceptance criteria.
- 3 RECOMMENDED-CHANGES surfaced (cosmetic; deferred to parked.md):
  1. `json` import scope (cosmetic only)
  2. AppleScript date constructor locale dependency (English-only `%A`/`%B`)
  3. `_RECONCILIATION_MIGRATIONS` runs on every persist (silently absorbs duplicate-column error; cheap but tidier with PRAGMA table_info precheck)

## What the champion still lacks (gap to "Hanna is real")

- `python/hanna/mcp_server.py` + 10 `hanna_*` tools (L6).
- `OverrideToken` schema (q014 secret-storage substrate must close first).
- `FormationRequest`/`FormationOutput` schemas (q017 contract surfacing must close).
- `src/octavius_bridge.py` (stub form acceptable per D016; runtime gates on q017).
- L6's reconciliation worker — closes the loop on P6 (now at 0.70).
- 7-day real-Mac trial (P10; Joe's hardware).
