# CHAMPION.md — current best artifact

**Updated:** 2026-05-25 (SKETCH gate — seed champion declared)
**Champion-id:** `seed-2118024`

## What it is

The seed champion is the current HEAD of `claude/hanna-mcp-review-ZsorY` at commit `2118024` — the merged result of PR #1 (L1–L4a + L3b shipped) plus the orchestrator install (D009) plus the first-principles improvement cycle (D010–D013 + Phases 0–6). This is the substrate the arc starts from. A weak champion is still the bar.

## Reproduction recipe

```bash
git clone https://github.com/JosephOIbrahim/Hanna
cd Hanna
git checkout claude/hanna-mcp-review-ZsorY     # PR #2 head
git rev-parse HEAD                             # → 2118024…
python3 -m pip install -e ".[dev]"
python3 -m pytest tests/ -q                    # → 117 passed
```

## Predicate score (how the champion measures against SPEC)

| Predicate | Status today | Score contribution |
|---|---|---|
| P1 (10 MCP tools callable from session) | 0 of 10 tools exist (L6 queued) | 0.0 |
| P2 (calendar publish at anchor; idempotent) | publish path absent (L4b queued); anchor + idempotency code IS landed (D010 + D012 + 0/1 PRAGMA-hardened SQLite) | 0.4 (plumbing done; publisher missing) |
| P3 (hanna_log appends to product file) | MCP layer absent (L6); product-file read path landed; append-only contract specified in D007 but not coded | 0.1 |
| P4 (octavius spawn/poll/harvest) | `src/octavius_bridge.py` absent (L7); Octavius repo existence unverified (F3 risk) | 0.0 |
| P5 (LockoutResponse on lockout) | shape unratified (q002 open); FAMILY_LOCKOUT layer 1 lives in `compute_producer_phase` | 0.2 (gate exists; structured response does not) |
| P6 (reconciliation invariant) | `briefs` SQLite has `brief_id UNIQUE`; no `calendar_event_uid` column yet; no reconciliation code | 0.1 |
| P7 (≥200 tests) | **117 / 200** | 0.59 |
| P8 (CI grep matrix passes) | yes — round-3 hardening landed + Phase 3 added enumerated bridge surface + Rule 37 commit-message grep + 32 D008.7 annotations | 1.0 |
| P9 (restart survival) | SQLite WAL + busy_timeout landed (Phase 5); launchd not yet deployed; orphan-process check untested | 0.3 |
| P10 (7-day real-Mac trial) | no operational schedule; trial cannot run | 0.0 |

**Champion score:** ~**0.27 / 1.00** (2.7 of 10 predicates substantively met).

## What ships green on this champion (the inheritance)

- D001 → D013 ratified; `docs/DECISIONS.md` footer at D014.
- 117/117 tests; CI green on the new compliance matrix.
- Belief layer at c001–c030; question layer at q001–q013 (q003–q006, q009, q010, q013 closed).
- ORCHESTRATOR.md installed + amended (§7 sanctions per-GOAL runtime state files).
- `.claude/agents/{planner,worker,critic,integrator}.md` formalize D002 roles as Claude Code primitives.
- D010 rhythm-anchor, D011 macOS-only stance, D012 idempotency, D013 MONTHLY-beats-WEEKLY precedence — all coded + tested.
- Structured logging across `src/` + `scripts/`; `python3 -m src status` JSON probe; `HarloBridge.last_stderr()` surfaced at 14 failure sites.
- SQLite PRAGMA hardening (WAL + busy_timeout + foreign_keys + synchronous=NORMAL).
- launchd MORNING .plist demonstrator (Phase 5); siblings not yet authored.
- ProductFile.parse Rule-36 faithful-surface (Phase 6).

## What the champion lacks (the gap to "Hanna is real")

- `src/channels/__init__.py` + `src/channels/calendar.py` — L4b.
- `CalendarEventId` NewType in `src/schemas.py` — L4b.
- 4 additional .plist files (MIDDAY / EVENING / WEEKLY_MONDAY / WEEKLY_FRIDAY) — L4b + Phase 5 follow-on.
- `OverrideToken`, `JoeStateSnapshot`, `FormationRequest`, `FormationOutput` schemas — L5.
- `LockoutResponse` shape ratification — q002 (in-arc decision).
- Brief composition boundary definition — q007 (in-arc decision).
- `python/hanna/mcp_server.py` + 10 `hanna_*` tools — L6.
- `src/octavius_bridge.py` + Octavius-reachability spike outcome — L7 (depends on F3).
- Reconciliation code: `briefs.calendar_event_uid` + sync invariant — L4b + L6.
- 7-day real-Mac trial — P10 (Joe's hardware).

## Promotion rule (per harness Operating Principle 6)

A new artifact promotes to champion only by **strictly increasing the predicate score** on at least one predicate **without regressing any other predicate**. Stochastic gains (P2, P4, P10) require replication on a fresh run before promotion.
