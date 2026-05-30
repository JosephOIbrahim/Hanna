# SPEC.md — long-horizon arc: L4b → L7 → "Hanna is real"

**Status:** ratified 2026-05-25 (Joe: "ratified") at the FRAME gate
**Arc-id:** `hanna-real-arc`
**Branch:** `claude/hanna-mcp-review-ZsorY` (post-PR-#2-open)
**Harness:** K+S × AutoScientists (on probation; D014 candidate only after this arc verifies its keep)

---

## Outcome

After the arc ships, Joe operates an always-on producer:

- Hanna composes briefs on a wall-clock cadence (5 phases × weekdays + weekly + monthly), each authored as a 0-minute anchor event at the rhythm time (D010) on his dedicated Hanna iCloud calendar (D006), idempotent on retry (D012), macOS-only (D011).
- From any Claude Code session on his Mac, he can invoke the 10 `hanna_*` MCP tools as first-class tools (morning_brief / midday_check / evening_capsule / weekly_monday / weekly_friday / monthly / log / block / unblock / formation_request). Each is gated by Rule 34 lockout, returning a structured `LockoutResponse` when paused.
- Hanna spawns Octavius formations via subprocess + MCP-over-stdio; polls; harvests; threads outputs back into subsequent briefs.
- Restart-safe: the launchd schedule resumes after sleep/wake; SQLite (WAL) survives; D012 prevents re-publish of already-shipped briefs.
- Observable: structured logs at every lane boundary; `python3 -m src status` JSON probe; `HarloBridge.last_stderr()` surfaces on failures (already landed pre-arc).

## Acceptance Predicates

- **P1** All 10 `hanna_*` MCP tools callable from a Claude Code session on Joe's Mac; each returns structured JSON per its tool contract.
- **P2** A brief composed at an off-anchor time (e.g. 08:47 ET) lands as a calendar event at the phase anchor (09:00 ET) on the Hanna calendar; second invocation in the same compose-window is a no-op (D012 idempotency holds end-to-end).
- **P3** `hanna_log` MCP-call appends to `data/products/<name>.md`; never overwrites Joe's hand-edits; the append is visible on the next brief composition.
- **P4** `hanna_formation_request` spawns Octavius via subprocess, polls until completion, harvests the output, returns it to the caller. Subprocess is reaped; no leaked thread / FD / SQLite lock.
- **P5** Any `hanna_*` tool invoked during FAMILY_LOCKOUT returns a `LockoutResponse` JSON object (per the shape ratified by q002) without executing the underlying tool.
- **P6** Reconciliation invariant: every row in `briefs` SQLite has either a `calendar_event_uid` matching an event on Joe's Hanna calendar, or an explicit `unpublished_reason` (e.g. `non_macos`, `family_lockout`, `harlo_unreachable`).
- **P7** `python3 -m pytest tests/ -q` exits 0 with ≥ 200 tests passing (extrapolating from the 117 baseline: L4b ≈ 15, L5 ≈ 20, L6 ≈ 35, L7 ≈ 15, integration ≈ 10).
- **P8** CI's full compliance grep matrix passes (Rule 1 / 35 name-anchored / 35 enumerated-allowlist / 37 across `docs/` + last-50 commits / no patent + no model-id).
- **P9** Hanna survives a clean restart: kill `harlo mcp`, remove the daemon process, re-load launchd; on next anchor, the brief composes and publishes; no orphan threads / no SQLite lock left behind / no duplicate calendar events.
- **P10** Seven-day real-Mac trial: across the trial window, count of published Hanna calendar events == count of `briefs` rows where `unpublished_reason IS NULL`, replicated across two distinct trial weeks (stochastic — replication required).

## Out of Scope

- iOS app / Apple Watch native surface (Calendar sync is cross-device; native is post-arc).
- CalDAV / cross-platform publish (explicitly out per D011; reversal requires a new D-entry).
- Joe-cognitive-twin modeling (Hanna observes portfolio state; doesn't model Joe's mind — that's Harlo's substrate per Rule 35).
- Performance / latency tuning (6 events/day on a wall clock; no hot path exists or is needed).
- Multi-user (Hanna is single-tenant; no auth surface).
- Brief content quality beyond Rule 36 voice + the D007 input surface.
- Octavius's internal development (Hanna is a request-only consumer per Rule 35).

## Falsification Conditions

- **F1** Claude Code's MCP client cannot reach a python-FastMCP server in the shape L6 targets → L6 approach must reverse; arc reorganizes.
- **F2** Calendar.app permissions on Joe's Mac block `osascript` even with explicit grant on a non-trivial macOS upgrade → D006 must reverse to CalDAV / EventKit, retiring D011's macOS-only posture.
- **F3** Octavius doesn't exist as a runnable subprocess matching the spawn/poll/harvest contract → L7 is unbuildable until Octavius ships; arc must split or stall.
- **F4** D012 brief_id collides in practice on the 7-day trial (two semantically-distinct briefs hash to the same id) → D012 reverses or extends key inputs.
- **F5** launchd misses anchor times under macOS sleep/wake without explicit Power Nap / wake-on-schedule config → wall-clock trigger model must change.
- **F6** `LockoutResponse` JSON is structurally fine but Claude Code renders it as an error in the session UI, defeating the "well-defined no-op" posture → q002's shape must reverse to something Claude-Code-renderable.

## Verification Strategy (per predicate × L0–L4; stochastic?)

| Predicate | L0 | L1 | L2 | L3 | L4 | Stochastic? |
|---|---|---|---|---|---|---|
| P1  | parse/lint MCP server | mocked MCP-client invokes each tool | property: every tool returns valid JSON | semantic: tool returns reflect real product/Harlo state | adversarial: malformed inputs | no |
| P2  | osascript template parses | mock osascript; verify event-args | property: idempotent on retry | semantic: real Mac publish | adversarial: rapid re-publish; mid-compose kill | **yes** (real-Mac timing) |
| P3  | filesystem write parses | tmp_path append test | property: never overwrites | semantic: round-trip via next compose | adversarial: concurrent edit by Joe | no |
| P4  | subprocess call parses | mocked Octavius | property: subprocess reaped | semantic: real Octavius | adversarial: Octavius crash mid-poll | **yes** (Octavius timing) |
| P5  | LockoutResponse JSON schema | mocked lockout phase | property: every tool gates | semantic: real lockout in real session | adversarial: override_token edge | no |
| P6  | SQLite schema parses | mocked reconciliation | property: invariant holds | semantic: real Mac after 7 days | adversarial: corrupted event UID | no |
| P7  | tests collect | pytest runs | property: no flaky tests | n/a | n/a | no |
| P8  | CI workflow parses | CI runs on PR | n/a | n/a | n/a | no |
| P9  | n/a | mock restart | property: no leaked threads/locks | semantic: real restart | adversarial: kill-9 mid-compose | no |
| P10 | n/a | n/a | property: count invariant | semantic: 7-day window | adversarial: replicate on 2nd week | **yes** (real-Mac, multi-week) |

## Effort budget (set at ratification)

| Resource | Cap |
|---|---|
| Agent dispatches across the whole arc | 50 (re-budget per phase if needed) |
| Token budget | re-derive per cycle from CHAMPION delta |
| Calendar time | unbounded; checkpoint per cycle so a long pause is recoverable |
| Joe's hardware | required for L3+L4 verifiers on P2, P9, P10 |

Re-derive the agent cap at every REORGANIZE; never exceed 50 without a new ratification.

## Ratification trail

- 2026-05-25 — Joe: "ratified" (in chat). FRAME gate cleared. SKETCH begins same turn.
