# PRD — Hanna First-Principles Review & Improvement Roadmap

**Date:** 2026-05-25
**Author:** Orchestrator (multi-agent first-principles review under `ORCHESTRATOR.md`)
**Status:** DRAFT — awaiting Joe's "go / no-go / redirect" before any implementation
**Branch:** `claude/hanna-mcp-review-ZsorY` (post-PR-#1-merge + post-orchestrator-install)

---

## Problem statement

PR #1 merged to `main` (`e08aebb`) — L1–L4a + L3b shipped, 74 tests pass, the orchestrator framework was just installed (D009, `c65b6ae`). Before dispatching L4b — the terminal lane after which "briefs land on Joe's calendar and Hanna is real" — Joe asked for a first-principles review to surface opportunities and improvement areas.

The lesson of the 2026-05-22 session (CodeRabbit round-3 found 4 latent bugs in code I had self-declared "done") suggested an independent critic pass would catch what self-audit misses. Belief `c003` was filed at confidence 0.7 to encode this caution. This review **empirically vindicated c003** — see Theme 1 below.

---

## Methodology

7 `critic[red_team]` scouts dispatched in parallel under `ORCHESTRATOR.md` §1. Each cold-read; each owned a disjoint slice of the territory; each emitted findings to `state/tasks/scout-<name>/findings.md` in a structured BLOCKER/MAJOR/MINOR + belief-delta + open-question format. Synthesis = orchestrator (this PRD). Budget: 7 agents spent of Joe's 20-agent cap.

**Coverage:**

| Scout | Survey angle | Output |
|---|---|---|
| scout-architecture | D001–D009 audit, orchestrator self-consistency, ROADMAP/BLUEPRINT coherence | 0 BLOCKER, 4 MAJOR |
| scout-code-quality | Idioms, type safety, error paths, dead code, refactor candidates | 0 BLOCKER, 1 MAJOR |
| scout-tests | Coverage gaps, brittle patterns, integration tests, fixtures | 3 BLOCKER, 9 MAJOR, 12 MINOR |
| scout-docs | Residual drift, navigation, cross-file coherence | 3 BLOCKER, 8 MAJOR, 6 MINOR |
| scout-ops | Logging, idempotency, scheduler, monitoring, secrets | 2 BLOCKER, 5 MAJOR, 5 MINOR |
| scout-security-rules | Rule enforcement, CI grep coverage, thread safety, security | 2 BLOCKER, 3 MAJOR, 4 MINOR |
| scout-lanes-schemas | L4b–L7 readiness, schema gaps, cross-platform | 3 BLOCKER, 8 MAJOR, 7 MINOR |
| **Total** | | **13 BLOCKER, 38 MAJOR, ~38 MINOR** |

9 belief deltas (c006–c014) written to `state/beliefs.md`; 10 open questions (q004–q013) promoted to `state/open_questions.md`.

---

## Headline findings — cross-scout themes

### Theme 1 — Test integrity (belief `c003` empirically vindicated)

The 74-test suite is competent on unit depth but the production-critical PoC `scripts/first_hanna_brief.py` is **75% untested** (only `_portfolio_line` exercised; `_state_line`, `_compose_brief`, `_persist`, `_extract_burnout`, `_read_harlo`, `_read_product_files`, `main()` have zero coverage; no integration test stitches them end-to-end — scout-tests B2).

The **round-3 frame-coalescing patch** — the exact bug class `c003` predicts — has **zero regression test** (`grep -rn "recv_buffer" tests/` returns nothing despite `_recv_buffer` being wired through `src/harlo_bridge.py:70-71, 320-323, 358-359` — scout-tests B1).

`compute_producer_phase` has undocumented `MONTHLY-beats-WEEKLY` precedence (Jun 1 2026 returns MONTHLY, not WEEKLY_MONDAY; empirically verified; untested — scout-tests B3).

### Theme 2 — D006 Calendar channel is NOT ready for L4b dispatch

- **Rhythm-anchor contradiction (q004):** D006's posture rationale promises rhythm-time anchor events at e.g. 09:00 ET; ROADMAP §4 spec hardcodes `BriefPayload.composed_at_iso` (UTC compose-moment) as the event start. First morning brief would land at random compose time (e.g. 07:42 ET), defeating D006's "context the day carries" rationale (scout-lanes-schemas B2).
- **Platform coupling (q005):** osascript is macOS-only; CI runs ubuntu-latest; no `HannaCalendarNotAvailable` + platform gate in ROADMAP §4 (NEXT.md names the exception, the lane spec doesn't — drift) (scout-lanes-schemas B1, scout-architecture).
- **No idempotency (q006):** `BriefPayload` has no dedup token; `briefs` SQLite schema has AUTOINCREMENT id with no UNIQUE constraint; `publish(brief: BriefPayload) -> CalendarEventId` would create **duplicate Joe-visible calendar events on every retry** (scout-ops B-OPS-002, scout-lanes-schemas).
- **`publish-now` CLI unspecified:** cited by ROADMAP §4 + NEXT.md but has zero argparse contract, no source-of-brief, no error semantics (scout-lanes-schemas B3).

### Theme 3 — CI green light means less than it claims

- **RULES.md greps target nonexistent paths:** `python/hanna/` and `crates/` do not exist in the repo; the CI greps run, find nothing, exit 0 trivially — the green light is meaningless for those rules (scout-security-rules B-0, belief c013 at 0.95).
- **3-layer lockout verification claim is bogus:** RULES.md asserts a 3-layer verification + `tests/test_integration/test_lockout.py` that does NOT exist. Only layer 1 (`compute_producer_phase`) is tested; `override_token` is openly spec-only (scout-security-rules B-1).
- **Rule 35 grep is bypassable by rename:** name-anchored on `harlo.write|store|author|mutate`; `harlo.commit` or `harlo.persist` would slip through. Real defense is the enumerated bridge surface, not the grep (scout-security-rules M-1).

### Theme 4 — Documentation drift survives the prior reconciliations (`2e68877`, `8e83296`)

- RULES.md §34 still describes 3-layer lockout with `HdProducer` as layer 2, contradicting RULES.md's own line-15 applicability note (post-L1) and every other propagated surface (scout-docs B1).
- README.md "Repository layout" is one-third-true: omits ORCHESTRATOR.md, docs/DECISIONS.md, docs/ROADMAP.md, docs/REVIEW_2026-05-22.md, docs/PRODUCER_LENS.md, docs/UI_UX_MAP.md, docs/SPIKE_HARLO_EDGE_2026-05-20.md, state/, scripts/, src/, tests/, data/; references nonexistent `web/README.md`; stamps BLUEPRINT as v0.1.0-draft when file self-stamps v0.2.0-audit (scout-docs B2).
- SESSION_01_RECON.md §G still claims "RULES.md does not exist in Harlo, synthesize from distributed sources" — directly contradicted by RULES.md:7. NEXT.md has carried this as "staleness flag" across sessions without resolution (scout-docs B3).
- REVIEW_2026-05-22.md carries the model-id string CLAUDE.md disallows (scout-docs MAJOR).

### Theme 5 — "Always-on" claim is unbacked operationally

- Zero `import logging` in src/ (scout-ops MAJOR, belief c011 at 0.95).
- No scheduler / cron / launchd / systemd / .plist; bin/hanna-brief.command opens a static HTML mockup and does not invoke Python (scout-ops B-OPS-001).
- No health probe, no status command, no self-test.
- HarloBridge.last_stderr() collects diagnostic data that no production caller reads.
- `override_token` mandated by Rule 34 is spec-only; no HMAC / secrets surface implemented (scout-ops MAJOR + scout-security-rules MAJOR).
- SQLite write path uses default `sqlite3.connect()` with no `journal_mode=WAL`, no timeout, no PRAGMA hardening (scout-security-rules M-3).

### Theme 6 — Orchestrator self-consistency (cross-verified independently)

`state/plan.md` exists as a standing file holding this GOAL's spec, **violating ORCHESTRATOR.md §7's adapter rule** that only `beliefs.md` + `open_questions.md` should be standing in `state/`. Flagged independently by scout-architecture AND scout-docs — strong cross-verification signal (belief c009 at 0.9, question q013).

### Theme 7 — Data-input hygiene (Rule 36 "faithful surface")

`ProductFile.parse()` has 6 silent-coercion / silent-drop input gaps (quoted YAML values, duplicate keys, unknown section headers, empty bullet lines, asymmetric ISO-datetime fallback, no Unicode normalization). None crash; each violates Rule 36's faithful-surface posture because the composer silently drops mismatched products (scout-code-quality M1).

---

## Cross-scout positive signals (worth preserving)

- The L3b round-3 frame-coalescing patch is **correctly synchronized** — `_recv_buffer` is mutated only inside `self._lock`-held call sites; no race introduced by the static-to-instance conversion (scout-code-quality + scout-security-rules cross-verify).
- D001–D009 are internally coherent as an architectural story; no contradictions sharp enough to BLOCK the next lane (scout-architecture belief).
- Rule 36 voice audit clears `_state_line`, `_portfolio_line`, `_approaching_line`, `_blockers_line` of directive imperatives (scout-security-rules).
- 0 BLOCKER from code-quality scout overall; lock discipline on production `_rpc` is sound.
- D003/D004 clone-trailer hygiene verified across all four cloned files; no model-id strings in committed code artifacts (scout-security-rules).
- ORCHESTRATOR.md §7–§9 adapter is internally consistent in *shape* (the violation is concrete — `state/plan.md` exists; the §7 design intent is sound) (scout-docs).

---

## Recommended phasing

13 agents remain in Joe's 20-cap. A full sweep would exhaust budget; Joe picks the first cycle.

### Phase 0 — Orchestrator self-fix (1 commit, ~5 min, 0 agents)

Resolve the §7 vs `state/plan.md` violation (q013). Two paths:
- **(a)** Amend ORCHESTRATOR.md §7 to permit `state/plan.md` as a per-GOAL standing file (pragmatic; expands the standing surface).
- **(b)** Migrate the GOAL block to NEXT.md adapter slot, retire `state/plan.md` (honors the original adapter; requires NEXT.md re-format).

**Orchestrator recommendation: (a)** — `plan.md` is per-GOAL, not per-session; fits the spec's task-artifact pattern conceptually. One-line §7 amendment.

### Phase 1 — Pre-L4b unblockers (~6 commits, ~600 lines, ~5–7 agents)

Required before L4b can ship trustworthily:

- **D010**: rhythm-anchor decision (q004). Default: 09:00 ET anchor (matches D006 posture). Touches `BriefPayload`, `scripts/first_hanna_brief.py:138`, and ROADMAP §4 L4b spec.
- **D011**: cross-platform stance (q005). Default: macOS-only with explicit `HannaCalendarNotAvailable` + Linux fallback that logs-and-skips publish (CI test path).
- **D012**: idempotency contract (q006). Default: brief idempotency-key = SHA256(phase + rhythm-time + body_markdown[:200]); add column to `briefs` SQLite + UNIQUE; `publish()` no-ops on existing key.
- `publish-now` CLI spec written into ROADMAP §4 (argparse: `--phase`, `--dry-run`; error semantics).
- **Round-3 frame-coalescing regression test** added to `tests/test_harlo_bridge.py` (the exact missing test belief c007 names).
- ROADMAP §4 L4b brief skeleton updated to incorporate D010/D011/D012.

### Phase 2 — Test integrity (~4 commits, ~300 lines, ~3 agents)

Build trust in "74 tests pass":

- Integration test for `scripts/first_hanna_brief.py` end-to-end (mock harlo subprocess; verify SQLite row + stdout brief; both state-blind and harlo-reachable paths).
- Sub-render coverage tests (`_state_line`, `_approaching_line`, `_blockers_line`, `_compose_brief`).
- `MONTHLY-beats-WEEKLY` precedence test + DECISIONS entry documenting the behavior (q008-adjacent).
- Layer-3 lockout test scaffold OR explicit annotation that L6 mcp_tools owns it.

### Phase 3 — CI / compliance integrity (~3 commits, ~150 lines, ~2 agents)

Make the green light meaningful:

- RULES.md compliance recipes repointed to actual paths (or annotate `src/`-only).
- Tighten Rule 35 grep + add a separate "enumerated bridge surface" allowlist check.
- Annotate non-load-bearing rules (1–17, 19–33) per D008.7 promise.
- Rule 37 grep extended to commit messages + `docs/`.

### Phase 4 — Doc-drift sweep (1 commit, ~80 lines, ~1 hour, 0–1 agent)

Fast hygiene wins:

- RULES.md §34 → 2-layer (drop HdProducer; align with line-15 applicability note).
- README "Repository layout" regenerated against actual filesystem.
- SESSION_01 §G correction OR historical stamp (q003 + q009 close).
- REVIEW_2026-05-22.md model-id removed (q010 close-pending).
- HANNA_DESIGN_ADOPTION.md status clarified.

### Phase 5 — Operational substrate (~4 commits, ~400 lines, ~3 agents)

Make "always-on" real:

- Add structured `logging` to `src/` + `scripts/`; emit at lane-boundary points.
- launchd `.plist` for macOS scheduler (q008 close).
- Health probe / status command (`python3 -m hanna status`).
- bin/hanna-brief.command swap to invoke Python (Phase-2 swap target predates L4b).
- SQLite PRAGMA hardening (`journal_mode=WAL`, `busy_timeout`).
- Read `HarloBridge.last_stderr()` at lane boundary; surface to logs.

### Phase 6 — Data hygiene (~2 commits, ~150 lines, ~1 agent)

Robustness:

- `ProductFile.parse()` validation tightening (faithful surface per Rule 36; warn-and-drop with explicit log per-product gap).
- Sub-render contract documentation (implicit ". " trailing convention).
- SQLite retention / cleanup policy.

---

## Recommended first implementation cycle

**Phase 0 + Phase 1 + Phase 4 partial.**

This unblocks L4b dispatch (the path to "Hanna is real") while:
- Fixing the orchestrator's first-run self-violation (Phase 0, 5 min).
- Resolving the 3 D-decisions L4b needs: rhythm-anchor (D010), cross-platform (D011), idempotency (D012) — Phase 1.
- Adding the round-3 regression test that c003+c007 demand — Phase 1.
- Cleaning the highest-impact doc contradictions: RULES.md §34, README layout, SESSION_01 §G — Phase 4 partial.

**Estimated budget: 6–8 agent dispatches.** Leaves 5–7 agents for the L4b dispatch itself (the lane that follows immediately after).

After this cycle, **L4b becomes dispatchable** with: rhythm-anchor resolved, cross-platform gated, idempotency contract in place, regression test landed, orchestrator self-consistent, highest-impact docs reconciled.

---

## Risks

- The 13 BLOCKERs are **latent, not catastrophic**. Hanna functions today; PR #1 merged clean. The risks emerge **at L4b dispatch** (platform mismatch, rhythm drift, duplicate events) and **as production runs** (no observability, no scheduler, CI greens that mean nothing).
- Doing the entire 6-phase plan in one cycle would exceed the 13-agent remaining budget. Joe must scope.
- A "no-go" without redirect leaves all 13 BLOCKERs latent; L4b can still be dispatched but with known gaps. PRD documents the gaps; Joe owns the call.

---

## Open questions blocking the recommended cycle

| q-ID | Question | Recommendation if Joe defers |
|---|---|---|
| q004 | rhythm-anchor timestamp | 09:00 ET anchor (D006 posture) |
| q005 | cross-platform stance | macOS-only + `HannaCalendarNotAvailable` + Linux logs-and-skips |
| q006 | idempotency key shape | SHA256(phase + rhythm-time + body_markdown[:200]) |
| q013 | ORCHESTRATOR §7 resolution | Amend §7 to permit per-GOAL `state/plan.md` |

Planner picks defaults from DECISIONS.md template if Joe doesn't override.

---

## The ask

**Go / no-go / redirect on Phase 0 + Phase 1 + Phase 4 partial as the first implementation cycle?**

Alternatively:
- "Go on Phase X only" — pick a different subset
- "Go on everything" — exhaust the budget on all 6 phases (will overflow; orchestrator will halt at budget cap)
- "Redirect" — diagnosis missed your priority; tell me where
- "No-go" — discuss specific findings before any commit

I will not act before your confirmation.

---

## Provenance

- 7 scout `findings.md` files at `state/tasks/scout-*/findings.md`
- 9 new beliefs at `state/beliefs.md` (c006–c014)
- 10 new questions at `state/open_questions.md` (q004–q013)
- This PRD at `state/tasks/prd/PRD.md`
- GOAL spec at `state/plan.md`
- Checkpoint at `state/checkpoint.md`
