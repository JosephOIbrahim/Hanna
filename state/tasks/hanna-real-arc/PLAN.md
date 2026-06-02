# PLAN.md — live line-of-attack structure

**Updated:** 2026-05-25 (REORGANIZE → cycle 2)
**Mode:** ORCHESTRATED TEAM (re-derived; signals unchanged from cycle 1 — see DIGEST.md)
**Effective independent lines (cycle 2):** 3 (B-cont, D, F); G considered, deferred

---

## Cycle 1 → cycle 2 reorganization

| Line | Cycle-1 status | Cycle-2 disposition |
|---|---|---|
| A — L4b Calendar channel | DELIVERED + PROMOTED (champion `arc-cycle1-line-A-a2d64cd`; PASS 36/36) | RETIRED (closed) |
| B — L5 schemas + q002/q007 substrate decisions | PARTIAL: D014 + D015 ratified (q002 + q007 closed); JoeStateSnapshot deferred; Override + Formation deferred | CONTINUE as B-cont (JoeStateSnapshot only) |
| C — Octavius reachability spike | DIED on FORUM; replaced by Joe's free-info reply → D016 ratified | RETIRED (closed; q016 closed; q017 closed-pending-action via D016 + c036) |
| D — L6 mcp_tools (was held) | n/a (held) | OPENED (partial — 9 of 10 tools that don't depend on Octavius; `hanna_formation_request` returns D016's `LockoutResponse`-equivalent stub) |
| F (NEW) — L7 octavius_bridge.py stub per D016 | n/a | OPENED |
| G (CONSIDERED) — q014 secret-storage substrate D-entry for OverrideToken | n/a | CONSIDERED, DEFERRED (q014 is high-leverage but not arc-terminal; defer to cycle 3 unless cycle 2 surfaces a forcing function) |
| E — Integration + Stress + Ship | held | still held (post-D ships + Joe's install step) |

---

## Cycle 2 open lines

### Line B-cont — JoeStateSnapshot schema authoring
**GOAL:** Author `JoeStateSnapshot` frozen dataclass in `src/schemas.py` per the cycle-1 FORUM-surviving spec (R1/R2 mitigations folded in: `extra` field for forward-compat; L1-only verifier acceptable since no consumer yet).
**CONTRACT:** Enables P1 partially (one of the 4 L5 schemas needed for the MCP tool surface).
**VERIFIER:** L0 + L1 (`tests/test_schemas.py` extensions — ≥3 cases per CONVENTIONS §1 + `from_harlo_payload` round-trip).
**Proposal queue (ranked):**
1. Author `JoeStateSnapshot(burnout: str, prediction: dict | None, schedule: dict, ts: str, extra: dict[str, Any] = field(default_factory=dict))` + `from_harlo_payload(d: dict) -> JoeStateSnapshot` classmethod. Tests at `tests/test_schemas.py`.

### Line D — L6 mcp_tools partial (9 of 10 tools)
**GOAL:** Author `python/hanna/mcp_server.py` with the 9 `hanna_*` tools that don't depend on Octavius: `morning_brief` / `midday_check` / `evening_capsule` / `weekly_monday` / `weekly_friday` / `monthly` / `log` / `block` / `unblock`. Each tool wraps its body in `begin_composition()` / `end_composition()` per D015; each is gated by Rule 34 layer-3 returning the D014 `LockoutResponse` JSON on FAMILY_LOCKOUT. `hanna_formation_request` lands with a `{ "octavius_installed": false, ... }` stub per D016.
**CONTRACT:** P1 partial (9 of 10 tools), P3 (hanna_log appends), P5 (LockoutResponse on lockout), P6 partial.
**VERIFIER:** L0 + L1 (mocked FastMCP client invokes each tool; verify return shape) + L2 (Rule 34 gate property: every tool routes through the lockout check).
**Proposal queue (ranked):**
1. Scaffold `python/hanna/__init__.py` + `python/hanna/mcp_server.py` skeleton with FastMCP server + the 9 tool registrations + `_lockout_response(phase, now)` helper per D014.
2. Each tool body: call into the existing composer logic via factored helpers OR a new `src/composer.py` extracted module — pick at worker-time per smallest-correct-change.
3. `hanna_log` / `hanna_block` / `hanna_unblock` use APPEND-ONLY semantics on `data/products/<name>.md` per D007.5.
4. `hanna_formation_request` returns `{ "octavius_installed": false, "install_path_hint": "...", "next_steps": [...] }` until q017's pending-action completes.
5. Tests at `tests/test_mcp_server.py` covering each tool + the lockout gate property.

### Line F (NEW) — L7 octavius_bridge.py stub per D016
**GOAL:** Author `src/octavius_bridge.py` as a stub matching HANNA_BLUEPRINT §9 spawn/poll/harvest contract. Mocked-subprocess tests verify the SHAPE; runtime gates on q017 closure.
**CONTRACT:** P4 partial (stub surface exists).
**VERIFIER:** L0 + L1.
**Proposal queue (ranked):**
1. Scaffold `src/octavius_bridge.py` with `OctaviusBridge` class + `spawn_formation(request) -> str` + `formation_status(id) -> str` + `formation_output(id) -> dict` stubs. Each raises a new `OctaviusNotInstalled` exception with a descriptive message (NOT bare NotImplementedError per cycle-2 critique R1).
2. Tests at `tests/test_octavius_bridge.py` verifying each stub raises cleanly + class structure matches BLUEPRINT §9.

### Line G — CONSIDERED, deferred to cycle 3
q014 secret-storage substrate (Mac keychain vs .env vs env var) → D-entry needed before `OverrideToken` schema. Not arc-terminal — `OverrideToken` only matters when Rule 34 layer-3 override needs to actually validate a token (post-cycle-2). Defer.

---

## Cycle 2 critique-before-build (FORUM standing critiques)

**Line B-cont** — surviving cycle-1 critique stands (R1/R2 baked in). Rating: **3/5**.

**Line D** — adversarial pass on L6 design:
- **R1** Composer logic in scripts/first_hanna_brief.py vs each MCP tool re-importing — refactor risk. Mitigation: extract to `src/composer.py` if duplication exceeds 2 sites; else keep in scripts/. Decide at worker-time. **medium × medium**.
- **R2** FastMCP server lifecycle vs begin_composition / end_composition wrapper — tool errors might leak composition state. Mitigation: try/finally at every tool body. **high × low**.
- **R3** `hanna_formation_request` stub returning `{octavius_installed: false}` — F6-class risk. Mitigation: use D014's `paused: true` shape pattern — `{ available: false, reason: "OCTAVIUS_NOT_INSTALLED", ... }`. **medium × medium**.
- **R4** APPEND-ONLY race when Joe has product file open in editor — last-write-wins risk. Mitigation: read → append → write; document the race as known limitation. **low × low**.

Survives with R1-R4 folded into worker brief. Rating: **5/5**.

**Line F** — adversarial pass on stub design:
- **R1** Bare `NotImplementedError` unhelpful — Mitigation: `OctaviusNotInstalled` exception with descriptive message. **low × medium**.
- **R2** Stub class structure may not match Octavius's actual shape — Mitigation: cite BLUEPRINT §9 as source of truth for stub; real-shape adjustment lands post-q017. **low × low**.

Survives. Rating: **2/5**.

---

## Ranked surviving queue (cycle 2, global)

| Rank | Line | Proposal | Rating | Dispatch path |
|---|---|---|---|---|
| 1 | D | L6 mcp_server.py + 9 tools + LockoutResponse + stub for formation_request | 5/5 | worker (largest cycle-2 dispatch) + critic[verify] |
| 2 | B-cont | JoeStateSnapshot schema + tests | 3/5 | worker (light) + critic[verify] |
| 3 | F | L7 octavius_bridge.py stub + tests | 2/5 | worker (light) + critic[verify] |

Suggested ordering: B-cont + F in parallel (small, disjoint files); D as the largest single dispatch; critic[verify] over all three at the end.

## REORGANIZE triggers (carried)

- Line D produces 3 successive proposals with no champion-score gain → reorganize.
- Joe completes q017 pending-action (Octavius install + traffic share) → REORGANIZE: open Line H (FormationRequest/Output schemas + L7 real implementation upgrade) + open Line G (q014 + OverrideToken).
- Effort budget at 25 of 50 agents → checkpoint review with Joe.

## Mode statement (re-derived at cycle 2 REORGANIZE)

ORCHESTRATED TEAM preserved. Signals: BREADTH=3 (B-cont + D + F); INDEPENDENCE=medium (D + B-cont both touch `src/schemas.py`; D + F both touch `python/hanna/` and `src/`); HORIZON=long; REWORK COST=high; VERIFIER COST=medium. No mode change. HYSTERESIS rule honored.
