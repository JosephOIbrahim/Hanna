# NEXT — for tomorrow-you

## 2026-05-22 session outcome

Three commits landed on `claude/hanna-mcp-review-ZsorY`:

- `3cdd516` — Rule 34 layer 1 lands (FAMILY_LOCKOUT enum return; ET tz contract; PoC SSOT consumer; bridge `with`-block).
- `5acd00a` — D005 drafted (open) bundling three bridge-hardening sub-decisions.
- `7d74337` — first-principles review at `docs/REVIEW_2026-05-22.md` (405 lines).

Plus, this commit lands:

- **D006 — RESOLVED.** Delivery channel for v1 briefs = dedicated `Hanna` iCloud calendar with 0-minute anchor events at rhythm times, brief body in event notes. Full reasoning at [`docs/DECISIONS.md`](docs/DECISIONS.md) D006. The 3-day behavioral test in the §12.6 default was skipped; first-principles reasoning is the substitute. Implementation lane: a future MoE dispatch at `src/channels/calendar.py` (Bridge Engineer + Brief Composer + Compliance Reviewer).
- **D007 — DRAFTED (open).** Input surface MVS = per-product `.md` files at `data/products/{name}.md`, YAML frontmatter + named sections. Initial set: `harlo`, `octavius`, `moneta`, `comfy_cozy`. Six open sub-decisions (D007.1–D007.6) on frontmatter format, status enum, empty-file handling, layer (b)/(c) follow-on, `.gitignore` posture. Awaits Joe's ratification.
- **D008 — DRAFTED (open).** §4 inheritance ratification = Cut six pending items (Hydra delegate, USD stage, three-tier storage, Rust hot path, XGBoost, dual venv); Review the 33 rules (selective re-adoption as constrained components land). Seven open sub-decisions (D008.1–D008.7), per-item ratifiable. Awaits Joe's ratification.

D006's Calendar choice corroborates D008.2 (USD Cut): Calendar IS the stage for v1. D007's input surface and D006's output channel are symmetric — both decisions favor surfaces Joe already inhabits over Hanna-authored fresh substrate.

**Substrate-decision tree at end of session:**
- D001 (Rule 35 permissive) — resolved
- D002 (MoE methodology) — resolved
- D003 (Apache headers) — resolved
- D004 (trailer hygiene) — resolved
- D005 (bridge hardening — rate-limit + read timeout + stderr drain) — **resolved** (whole-batch 2026-05-22)
- D006 (Calendar channel) — resolved
- D007 (per-product `.md` input surface MVS) — **resolved** (whole-batch 2026-05-22)
- D008 (§4 inheritance ratification, 7 sub-decisions) — **resolved** (whole-batch 2026-05-22)

**All substrate decisions resolved.** Downstream lanes unblocked:
- D005 → MoE Dispatch #2 hardens `src/harlo_bridge.py` (rate-limit scope methods, `selectors.DefaultSelector` timeout, background stderr drainer + ring buffer).
- D006 → MoE dispatch lands `src/channels/calendar.py` (osascript Calendar publish + archive; `BriefPayload → CalendarEventId`).
- D007 → land `data/products/{harlo,octavius,moneta,comfy_cozy}.md` stubs + `ProductFile` schema in `src/schemas.py` + brief-composer rewrite (Path.read_text + YAML frontmatter parse + section render).
- D008 → BLUEPRINT §4 table propagation (column rename + per-row ratified value) + §5 strike-throughs (Hydra delegate, USD stage prims) + §10 lane diagram refresh (`delegate`/`stage`/Rust crate lanes removed). Hygiene-pass commit per [`docs/REVIEW_2026-05-22.md`](docs/REVIEW_2026-05-22.md) §3.3.

## Where you are

- Branch: `main` (HEAD = `4dcc36b`).
- Origin: `github.com/JosephOIbrahim/Hanna` — main pushed, `session-02-scaffold` pushed for history.
- Session 02 closed out 2026-05-20.

## Session 02 receipts

- `session-02-scaffold` merged `--ff-only` into main:
  - `e7ac833` — feat(computations): scaffold `compute_producer_phase` (Session 02).
  - `732b676` — docs(decisions,notice): ratify D003 — drop per-file Apache headers.
- Net line count: **90** (target ~100; cap 130).
- Tests: **7 / 7 pass** (`Harlo/.venv314/bin/python -m pytest tests/computations/`).
- All 7 phase branches in `src/computations/compute_producer_phase.py` raise `NotImplementedError("Session 03")`.

## Decisions ratified

- **D003** — Apache header convention: clones inherit absence. NOTICE read literally; 4 files amended.
- **D004** — Attribution-trailer hygiene at reviewer + conventions layers (commit `4dcc36b`).
- Next decision number: **D005**.

## Session 03 entry point

**First deliverable:** implement the 7 transition bodies in `src/computations/compute_producer_phase.py`. Each branch currently raises `NotImplementedError("Session 03")`. Target mapping:

| Branch condition (current code) | Returns |
|---|---|
| `weekday() >= 5` or `hour ∉ [work_start, work_end)` | `ProducerPhase.FAMILY_LOCKOUT` |
| `now.day == monthly_day` | `ProducerPhase.MONTHLY` |
| `weekday() == 0 and hour == weekly_monday_hour` | `ProducerPhase.WEEKLY_MONDAY` |
| `weekday() == 4 and hour == weekly_friday_hour` | `ProducerPhase.WEEKLY_FRIDAY` |
| `hour < morning_end_hour` | `ProducerPhase.MORNING` |
| `hour < midday_end_hour` | `ProducerPhase.MIDDAY` |
| fallthrough | `ProducerPhase.EVENING` |

Then convert the 7 stubs in `tests/computations/test_compute_producer_phase.py` from `pytest.raises(NotImplementedError)` to assertions on the returned `ProducerPhase` value. Per Harlo's `tests/test_sprint1/test_cogexec.py:4` precedent (and CONVENTIONS §1), each branch wants **≥3 cases** — boundary + interior + adjacent-day-or-hour — so the test file grows to ~21+ cases.

**Followups for Session 03 to surface:**

- Lockout-window granularity: ET vs. UTC, holidays, half-days. If finer-grained than Mon–Fri 09–17 ET is needed, surface for D005.
- Hanna still has no `pyproject.toml` / venv. Session 03 may want to establish one before the test suite grows; alternative is keep using Harlo's `.venv314` indefinitely.
- `prev_phase` is currently a signature arg but unused in the spec table above. Session 03 will need to decide whether prev_phase informs the transition (e.g., hysteresis on phase flips at boundary hours) or is purely for symmetry with `compute_burst.py`'s pattern.

## D005 — RESOLVED 2026-05-22 — Harlo bridge hardening (whole-batch ratification)

Three latent issues in `src/harlo_bridge.py`. Two surfaced during Session 02; the third surfaced during the 2026-05-22 senior review. All three bundled into [`docs/DECISIONS.md`](docs/DECISIONS.md) D005, ratified whole-batch on 2026-05-22 at the proposed defaults. The implementation lane (MoE Dispatch #2: Bridge Engineer + Compliance Reviewer per D002) is unblocked; estimated ~50–80 lines.

- **D005.1 — `_coach_driven` rate limit has the wrong shape.** [D001](docs/DECISIONS.md) mandates "≤1 `coach` call per brief composition" with the rate limit living in the bridge. The current boolean (`src/harlo_bridge.py:43, 85–89`) enforces "≤1 per `HarloBridge` instance, ever" — any long-lived caller composing more than one brief raises `HarloCoachingExchangeAlreadyDriven` on the second composition. The current PoC accidentally honors the intent by instantiating one bridge per run (now via the `with`-block landed in commit `3cdd516`). Default proposed: `begin_composition()` / `end_composition()` scope methods.
- **D005.2 — `_read_frame` timeout is dead.** The `timeout` parameter is plumbed through `_rpc → _read_frame` but the body never references it (`src/harlo_bridge.py:175–201`). `proc.stdout.readline()` and `proc.stdout.read(content_length)` are blocking pipe reads. A hung Harlo subprocess freezes the bridge indefinitely. Day-zero PoC didn't surface this because the test paths didn't exercise hang scenarios. Default proposed: `selectors.DefaultSelector` + `select(timeout=…)`.
- **D005.3 — stderr is undrained.** `subprocess.Popen` opens with `stderr=subprocess.PIPE` (`src/harlo_bridge.py:116`) but no thread or call reads from it. Once Harlo writes ~64KB to stderr (OS pipe-buffer default), the subprocess blocks on the next stderr write — deadlocking the bridge. Default proposed: background drainer thread + bounded ring buffer for diagnostics.

All three are bridge-hardening concerns, not Rule 35 issues. Once D005 ratifies, a single MoE Dispatch #2 (Bridge Engineer + Compliance Reviewer per D002) lands the three together — estimated ~50–80 lines.

## Open questions still parked

(carried from prior NEXT)

- **§C.2** — Octavius IPC PoC (deferred until `octavius_bridge` lane).
- **§C.3** — Harlo MCP-client precedent (partially addressed by §11.1 day-zero PoC; close out after Session 03 if no new questions surface).
- **§C.4** — `LockoutResponse` shape (needed before `mcp_tools` lane).
- **§C.6** — RED override in delegate dispatch (needed before `delegate` lane; ~5-min read of `Harlo/src/delegate_base.py` + `delegate_registry.py`).

None of these block Session 03's first deliverable.

## Staleness flag — still carried

Session 01 `docs/SESSION_01_RECON.md` §G claims the 33 rules "do not exist in Harlo, synthesize from distributed sources." Still wrong — rules existed in `Harlo/CLAUDE.md` lines 37–194 the whole time. Session 01.5 extracted directly; no synthesis was needed.

Joe's call at Session 03 start: fix §G with a correction note (one short paragraph), or leave as a session-stamped historical artifact?
