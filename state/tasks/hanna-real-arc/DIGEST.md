# DIGEST.md — compressed snapshot, SKETCH→DELIBERATE handoff

**Updated:** 2026-05-25 (SKETCH gate)
**Cycle:** 0 (the gate-handoff cycle; no proposals executed yet)
**Replaced at every cycle boundary; this is the cycle-1 INPUT.**

---

## The sketch (maximally lossy end-to-end shape)

```
Joe's Mac
├── launchd (5 .plist) ──▶ bin/hanna-brief.command ──▶ scripts/first_hanna_brief.py
│                                                            │
│                                          ┌─────────────────┴─────────────────┐
│                                          ▼                                   ▼
│                              src/harlo_bridge.py                  data/products/*.md
│                                  (D001/D005)                          (D007)
│                                          │                                   │
│                                          └─────────────────┬─────────────────┘
│                                                            ▼
│                                                _compose_brief() → BriefPayload
│                                                  (D010 anchor; D012 brief_id)
│                                                            │
│                                          ┌─────────────────┴────────────────┐
│                                          ▼                                  ▼
│                              _persist() (SQLite WAL)            src/channels/calendar.py
│                                (D012 idempotency)                      publish()
│                                                                       (D006/D011)
│                                                                            │
│                                                                            ▼
│                                                              Calendar.app via osascript
│                                                                "Hanna" iCloud calendar
│
└── Claude Code session (Joe interactive)
    └── python/hanna/mcp_server.py (FastMCP stdio)
        ├── hanna_morning_brief / midday / evening / weekly_monday / weekly_friday / monthly
        │     └── compose + publish (re-uses scripts/first_hanna_brief.py composer)
        ├── hanna_log / block / unblock
        │     └── APPEND-ONLY edit to data/products/<name>.md
        ├── hanna_formation_request
        │     └── src/octavius_bridge.py ──▶ subprocess(octavius mcp)
        └── every tool: Rule 34 layer-3 gate → LockoutResponse JSON on lockout
```

## Load-bearing components + riskiest unknown

| # | Component | Riskiest unknown |
|---|---|---|
| 1 | `src/channels/calendar.py` (L4b) | macOS osascript permissions stability across upgrades (F2) |
| 2 | `python/hanna/mcp_server.py` (L6) | Claude Code MCP-client compatibility with FastMCP-stdio (F1) |
| 3 | `src/octavius_bridge.py` + Octavius binary (L7) | Octavius existence + runnable contract (F3) |
| 4 | 5 launchd `.plist`s | macOS sleep/wake anchor-time misses (F5) |
| 5 | L5 schemas — esp. `OverrideToken` | secret-storage substrate (keychain? env? .env file?) |

## Dependency graph (predicted; not measured)

```
Line A (L4b code) ──── shares src/schemas.py ────┐
                                                 │
Line B (L5 schemas + q002/q007 D-entries) ───────┼── docs/DECISIONS.md (write-contention)
                                                 │
Line C (Octavius reachability spike) ────────────┘
                              │
                              ▼
                       Line D (L6 mcp_tools)
                              │
                              ▼
                       Line E (Integration + Stress + Ship)
```

**Predicted independent lines at start:** 4 (A, B, C, plus the held D, E).
**Effective independent lines (contention-discounted):** **3** (A, B, C). D + E are held by dependency.

## CONTENTION PROBE — skipped

The harness allows skipping the probe when mode is plausibly obvious. Here: HORIZON=long (clear); BREADTH≥2 with shared-write contention (docs/DECISIONS.md, src/schemas.py, LOG.md) that's manageable by claim/lock — not a true mode-flipping uncertainty. Skipping the probe trades observed contention for graph prediction; flagging it explicitly per the harness's HONESTY CONSTRAINT.

## Mode (initial; re-derived at every REORGANIZE)

**ORCHESTRATED TEAM** — explicit per the Complexity Gate's signals:

| Signal | Reading |
|---|---|
| BREADTH | high (3 effective independent lines initially; opens to 4 if D unblocks earlier) |
| INDEPENDENCE | medium (graph-predicted; shared-write contention on `docs/DECISIONS.md`, `src/schemas.py`, `LOG.md` exists but is claim/lock-tractable) |
| HORIZON | long (multi-cycle arc; ~50-agent budget; 7-day Mac trial is the terminal verifier) |
| REWORK COST | high (D-entries are append-only-with-supersede; schema changes cascade into tests) |
| VERIFIER COST | medium (pytest fast; CI ~13s; real-Mac trial is expensive but only at the end) |

**Decision:** ≥4 effective lines (after Lines D/E open) + long horizon + expensive rework + external launcher available → ORCHESTRATED. Initially 3 lines open → still ORCHESTRATED (the harness threshold is 4+ but the long horizon + rework cost justify orchestrated dispatching even at 3; hysteresis policy: hold orchestrated until a sustained 1-line cycle).

**Honesty constraint:** Claude Code's Agent tool IS an external launcher (verified by the prior cycle's 7-parallel-scout dispatch). Single-context-narrating-parallel is honest here because real parallel dispatch happens through the tool.

## Confidence per SPEC predicate (0–1)

| P | Predicate (one-line) | Confidence we CAN ship it given this arc | Rationale |
|---|---|---|---|
| P1 | 10 hanna_* tools callable from session | **0.75** | L6 lane is sized; Joe's Mac required for real-render; F1 risk |
| P2 | Calendar publish at anchor; idempotent | **0.80** | D010/D012 ratified + plumbing done; osascript path is well-known macOS; F2 is the only unknown |
| P3 | hanna_log appends to product file | **0.85** | APPEND-ONLY pattern is well-defined; D007 input surface unchanged |
| P4 | Octavius spawn/poll/harvest | **0.40** | F3 is large; Octavius existence unverified |
| P5 | LockoutResponse on lockout | **0.80** | q002 ratification (D014) is in the line queue; once shape ratified, code is straightforward |
| P6 | Reconciliation invariant | **0.75** | L4b + L6 needed; column additions to briefs are mechanical |
| P7 | ≥200 tests | **0.85** | extrapolation conservative; the lanes typically over-deliver per CONVENTIONS §1 |
| P8 | CI compliance matrix passes | **0.95** | Phase 3 hardened this; no regression expected |
| P9 | Restart survival | **0.65** | SQLite WAL + busy_timeout landed; launchd sleep/wake (F5) is the unknown |
| P10 | 7-day real-Mac trial | **0.55** | most expensive; depends on F2 (osascript perms), F5 (sleep/wake), F4 (idempotency collision in practice) |

**Champion score at start:** ~0.27 (per CHAMPION.md).
**Mean confidence we ship:** **0.74** (arithmetic mean across P1–P10; weighted-by-leverage would tilt up since P7+P8 are highest-confidence).
**Riskiest predicate:** P4 (Octavius) at 0.40 — Line C (the spike) is the rational risk-burn.
**Most-stochastic predicate:** P10 (7-day trial) at 0.55 — replication required per the harness's noise-aware promotion rule.

## Open questions (carried into DELIBERATE cycle 1)

- **q002** `LockoutResponse` shape — will close inside Line B as D014 (was "high; gates L6"; now in-arc).
- **q007** brief composition boundary — will close inside Line B as D015 (was "high; gates L6"; now in-arc).
- **q011** DECISIONS.md template — explicit rejected-alternatives block? Adopting the harness's pattern would close this; defer.
- **q012** L5 schema split — one D-entry or four? Pick at Line B kickoff; default = one D-entry per schema if the rationale is distinct, else bundle.
- **q014 (new)** Secret-storage substrate for `OverrideToken` — Mac keychain via `python-keychain`? .env file? environment variable? blocks `OverrideToken` semantics → file in open_questions.md alongside Line B.
- **q015 (new)** `OverrideToken` HMAC key rotation — single static key (v1) vs rotating (v2)? defer to v1 = single static, document the limitation.

## Effort budget posture

- 50 agents ratified for the whole arc (SPEC §"Effort budget").
- Cycle 1 (lines A + B + C kickoff): estimate 8–12 agents.
- Cycle 2 (after Line C reports; Lines A + B continue; D opens): estimate 10–15 agents.
- Cycle 3 (D + integration): estimate 12–18 agents.
- Cycle 4 (STRESS + SHIP + 7-day trial dispatching): 5–10 agents.
- Margin: ~10–20 agents for REORGANIZE, retries, and adversarial passes.

## What the next cycle (cycle 1 = DELIBERATE) consumes

- This DIGEST (replaces the FRAME-time `<no DIGEST>`).
- The seed CHAMPION (`seed-2118024`).
- The 3 open lines in PLAN.md (A, B, C; D and E held).
- An empty LOG / FORUM / DEADENDS / TRACE (no attempts yet).
- An empty LEDGER (cross-GOAL; will accumulate skills).

## Cycle-1 entry posture

The next gate is **DELIBERATE** (the core loop's left half). Analyst + Critic open:
- Cross-check each line's top proposal against DEADENDS (empty — no dead ends to consult yet).
- Critic FORUM critique: each Line A / B / C top-proposal gets adversarial review BEFORE any execute cost. Weak proposals die there.
- Open the queue per line; build the proposal-rank justification (Operating Principle 5).
- Query LEDGER for recipes matching queued proposals (empty — no recipes yet).

DELIBERATE then HANDS OFF to EXECUTE; the loop runs until reorganization or arc termination.
