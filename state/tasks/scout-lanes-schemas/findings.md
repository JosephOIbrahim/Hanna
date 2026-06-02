# scout-lanes-schemas — red_team findings

**Role:** critic[red_team]
**Task ID:** scout-lanes-schemas
**Scope:** Lane readiness (L4b, L5, L6, L7), schema gaps, cross-platform posture, forward-blocker path.
**Posture:** Adversarial pass; assume passing CI ≠ correct (c003).

---

## Executive summary

L4b is implementation-ready in shape (BriefPayload exists, ProductFile exists, ROADMAP §4 lane-spec is the most detailed in the document) but ships with three forward-blockers the brief skeleton elides: (1) the `osascript` path is macOS-only and CI runs on `ubuntu-latest`, so the lane spec needs an explicit `HannaCalendarNotAvailable` posture before tests can be authored (NEXT.md captures this; ROADMAP.md §4 L4b does not); (2) the `composed_at_iso` field on `BriefPayload` is a UTC timestamp by construction at `scripts/first_hanna_brief.py:138`, but the Calendar event needs to anchor at the rhythm-time-of-day in ET — there is an implicit timezone-coordinate confusion that nothing in the spec resolves; (3) the `publish-now` CLI subcommand cited by ROADMAP §4 L4b and NEXT.md has zero specification (no argparse contract, no source-of-brief, no error semantics) and is the bridge between `bin/hanna-brief.command` and the channel. L5/L6/L7 are all blocked on a prerequisite that has not been ratified: `LockoutResponse` (q002) is the contractual return type the entire `mcp_tools` lane depends on, and its shape is parked open; `OverrideToken` lacks any shape proposal anywhere; `JoeStateSnapshot` has no decided source-of-truth between Harlo's v9 envelope and an independent Hanna cache; `FormationRequest/Output` have no contract surface because Octavius does not exist as a repo (q001 is correctly open but L7's spec presumes a known IPC envelope). The forward-blocker analysis is: L4b is the only lane that can ship without unparking a question; everything past Real depends on belief deltas the orchestrator must source first.

---

## BLOCKER findings

### B1 — L6 `mcp_tools` cannot author tool returns until `LockoutResponse` is ratified

**Surface:** `python/hanna/mcp_server.py` (doesn't exist); HANNA_BLUEPRINT.md §5 lines 152–165; RULES.md:183; q002 in `state/open_questions.md`.

Every one of the ten `hanna_*` tools in BLUEPRINT §5 must return `LockoutResponse` during FAMILY_LOCKOUT per BLUEPRINT §7 layer 3 ("Every tool checks lockout state before executing. Lockout returns `LockoutResponse`, not an error.") The shape is parked at q002 with no proposed default in `state/open_questions.md`. SESSION_01_RECON.md:185 proposes `{status, phase, next_window_iso, override_path}` but UI_UX_MAP.md:310 explicitly opens the field shape as a design question. ROADMAP §4 L6 catalogs the lane in three lines and does not name the question. Without ratification, L6 has to either guess the shape (locking ten tool implementations to an unratified contract — guarantees re-work) or stub the lockout return (defeating the family-first structural enforcement that BLUEPRINT §7 calls non-negotiable). **L6 cannot start.**

The two field shapes are not interchangeable: if `next_window_iso` is the next *productive* window, the compute path needs `compute_producer_phase` to expose "when does this transition leave FAMILY_LOCKOUT" (which it does not today); if `override_path` is a URL it needs an HTTP surface; if it is a slash-command name it presumes Claude session UX; if it is channel-agnostic the field is structurally vacuous. The decision must precede any L6 author.

### B2 — L7 `octavius_bridge` presumes Octavius exists; q001 is the right question but the lane spec is wrong

**Surface:** ROADMAP §4 L7 lines 279; q001 in `state/open_questions.md`; HANNA_BLUEPRINT.md §9 lines 287–292.

ROADMAP §4 L7 reads "Depends on Octavius source repo existing and L6 to have a caller." A `find` across the repo for `octavius` produces only `data/products/octavius.md` (the product file stub). HANNA_BLUEPRINT.md §9 specifies the three Octavius methods (`spawn_formation`, `formation_status`, `formation_output`) and the IPC pattern ("subprocess + MCP-over-stdio") — but the formation grammar's input shape, the formation-id encoding, the polling semantics, and the harvest-output schema have zero specification anywhere. q001 captures this correctly with "medium" leverage and "open" status. **L7 is not just blocked on Octavius existing; L7's brief skeleton cannot be authored even as a spec because four contract surfaces are undefined and the calling-lane (L6) cannot consume an undefined return.**

The dependency chain in §3 lane DAG (`L6 -.-> L7`) is "soft ordering" per the legend; in practice L7 has a hard upstream on L5's `FormationRequest`/`FormationOutput` (which Hanna's caller passes / harvests) and a hard upstream on Octavius's source repo for the receive-side schema. The DAG understates this.

### B3 — `BriefPayload.composed_at_iso` is UTC; Calendar event needs ET wall-clock rhythm time — schema-level mismatch

**Surface:** `src/schemas.py:134` (`composed_at_iso: str`); `scripts/first_hanna_brief.py:138` (`datetime.now(timezone.utc).isoformat()`); ROADMAP §4 L4b lines 247, 263; D006 "0-minute anchor events at the rhythm times."

The Calendar channel must place the event at the *rhythm time* (e.g., morning brief anchors at 09:00 ET, midday at 12:00 ET) per D006's posture-fit reasoning ("context the day carries"). But `BriefPayload.composed_at_iso` is the moment composition ran, in UTC, as currently constructed. If L4b's `publish(brief)` reads `composed_at_iso` for the event start time, every event will land at the compose-moment, not at the rhythm anchor — so a brief computed at 09:02:31 lands at 09:02:31, not at 09:00, and the user-visible posture ("the morning slot") collapses.

The ROADMAP §4 L4b brief skeleton says "start time: brief.composed_at_iso" — this hardcodes the bug. The spec does not name "rhythm time" as a separate concept. Either (a) `BriefPayload` gains a `rhythm_anchor_iso` field (schema gap), (b) the Calendar channel recomputes the anchor from `phase` + today's-date (computation gap — needs `compute_rhythm_anchor(phase) -> datetime` that does not exist), or (c) the lane accepts compose-time placement and D006's "rhythm anchor" claim degrades. None of the three is resolved.

Compounding: `composed_at_iso` is a string, not a `datetime`, so the channel has to round-trip through `datetime.fromisoformat()` to compute event placement — error-prone with mixed UTC/ET semantics.

---

## MAJOR findings

### M1 — Cross-platform CI cannot exercise the Calendar publish path; the lane needs an explicit testable-on-CI vs runs-on-Joe's-Mac split that the brief skeleton elides

**Surface:** `.github/workflows/ci.yml` line 11 (`runs-on: ubuntu-latest`); ROADMAP §4 L4b lines 254–255; NEXT.md line 72 (mentions `HannaCalendarNotAvailable` for non-macOS dev envs but ROADMAP does not).

The CI runner is Linux. The publish path is `osascript`. The completion criteria in ROADMAP §4 L4b line 256 says "On a macOS host with Calendar.app set up, `python3 scripts/first_hanna_brief.py` publishes a real calendar event…(manual verification; integration test is gated on env var)." This means the only thing CI ever exercises is the mocked-subprocess path. The lane has three layers of testability, only one of which has a clear test posture:

1. **Mocked subprocess** — `tests/test_calendar.py` runs on CI. Verifies AppleScript string templating, error parsing, exit-code handling. ROADMAP §4 L4b calls for ≥6 cases. **Tractable on CI.**
2. **Real `osascript` call to Calendar.app on Joe's Mac** — integration test gated on `HANNA_INTEGRATION_TEST_CALENDAR=1`. **Never runs on CI.** Manual verification only.
3. **`HannaCalendarNotAvailable` graceful-degradation path** — Linux dev env (and CI) needs to import the module, call `publish()`, and observe a structured "not available" return rather than a hard `subprocess.run` failure on missing `osascript` binary. NEXT.md names this exception; ROADMAP §4 does not.

The brief skeleton in ROADMAP §4 L4b lines 263–271 names `HannaCalendarNotFound` but not `HannaCalendarNotAvailable` — the dev-env / Linux-CI exception NEXT.md added. Without the latter, the module fails to import on Linux (`subprocess.run(["osascript", …])` raises `FileNotFoundError` on the first call site, which would happen during any module-level smoke test). The lane needs the platform-detection upfront — `sys.platform == "darwin"` gate at module level, or `shutil.which("osascript")` probe — and the spec does not direct the dispatcher to add it.

**Drift risk:** NEXT.md (line 72) and ROADMAP §4 L4b (line 263) are two different specifications of the same lane; NEXT.md is richer (names the third exception, names the integration wiring); ROADMAP is the lane's source-of-truth per harness contract. The next dispatcher reads ROADMAP and misses the `HannaCalendarNotAvailable` requirement; the divergence is one round of CodeRabbit away from being c003 (latent bug found post-merge).

### M2 — `publish-now` CLI subcommand has zero specification

**Surface:** `bin/hanna-brief.command` Phase-2 swap target; ROADMAP §4 L4b line 250 and 269; NEXT.md line 75.

The `bin/hanna-brief.command` Phase-2 swap is literally a one-line shell change — `open "$BRIEF_PATH"` → `python3 -m src.channels.calendar publish-now`. But `python3 -m src.channels.calendar publish-now` requires (a) the module to be runnable (`__main__.py` or `if __name__ == "__main__"`), (b) an argparse with `publish-now` subcommand, (c) a brief source — does it re-run the composer end-to-end? does it read the latest row from `data/hanna.sqlite`? does it accept a payload on stdin? — and (d) failure semantics (return code, message to stdout, retry logic). None of this is in the spec.

The integration step in NEXT.md line 75 says "swaps `bin/hanna-brief.command` Phase-2 target from `open "$BRIEF_PATH"` to `python3 -m src.channels.calendar publish-now`" but doesn't specify what `publish-now` does on the inside. A dispatcher reading the brief skeleton will improvise — and improvisation here is exactly where the launcher posture (the calendar event Joe sees when he double-clicks the icon) breaks if compose-source is wrong (re-runs compose with a different `composed_at_iso`, lands at the wrong rhythm time per B3).

### M3 — `JoeStateSnapshot` has no source-of-truth decision; L5 will author a contract for a field set Hanna doesn't own

**Surface:** HANNA_BLUEPRINT.md §8 line 249 ("Joe-state snapshot — last read from Harlo, with timestamp for staleness gating."); REVIEW_2026-05-22.md lines 124–127; `src/harlo_bridge.py` `drive_coaching_exchange()` returns `{coach_block, cognitive_context, v9}`.

The L5 catalog (ROADMAP §4 line 277) lists `JoeStateSnapshot` as one of four schemas to add. But the field set is undefined. The candidates are:

1. **Mirror of Harlo's v9 envelope** — `{momentum, burnout, energy, altitude, schedule, allostatic_load, dynamics, prediction}`. Schema is Harlo's, so Hanna would be either re-declaring Harlo's types (drift risk per Rule 35 — Hanna's `JoeStateSnapshot` declaration is a partial copy of Harlo's source-of-truth) or holding an opaque blob with a TTL.
2. **Distillation** — fields Hanna actually consumes (today: just `burnout` per `_extract_burnout` in `scripts/first_hanna_brief.py:61–71`). Smaller surface; honest; but then "snapshot" is a misnomer.
3. **Cached-blob-plus-extracted-fields** — both. Schema gets larger but lossless.

Without a decision, the L5 dispatcher will improvise (likely toward 1, because BLUEPRINT §8 implies it), and the next session that wires `hanna_read_joe_state` discovers the field set is wrong shape. The Harlo v9 envelope is also versioned (the name "v9" implies prior v1–v8); Hanna's schema declaration is one Harlo upgrade away from drift.

### M4 — `OverrideToken` has zero proposed shape anywhere

**Surface:** RULES.md:185 ("HMAC-signed, single-use, TTL-bounded"); HANNA_BLUEPRINT.md:233 ("requiring an explicit `override_token` with TTL"); REVIEW_2026-05-22.md:117–122.

This is the friction surface Rule 34 depends on (the "single yes from Joe per session" lockout override). REVIEW_2026-05-22.md:121 explicitly notes "No proposed shape exists in NEXT.md or the session docs." The L5 catalog lists this schema but the brief skeleton in ROADMAP §4 line 277 is one sentence: "Add `OverrideToken`, `JoeStateSnapshot`, `FormationRequest`, `FormationOutput` to `src/schemas.py`. Each follows the `ProductFile` / `BriefPayload` pattern landed in L4a."

`OverrideToken` does not follow the `ProductFile` pattern — `ProductFile` is a parsed-frontmatter-plus-sections file shape; `OverrideToken` is a signed cryptographic credential. The "pattern" reference in the brief is wrong-genre. The actual decisions L5 must take (HMAC key source, TTL default, single-use enforcement substrate — file? SQLite? in-memory?, audit log destination, the verify path that the lockout layer calls) are zero-spec'd.

### M5 — L5 brief skeleton conflates four schemas of different design weight into one session

**Surface:** ROADMAP §4 line 277.

ROADMAP §4 L5 effort estimate: "~1 session." But:

- `OverrideToken` is a security primitive (HMAC + TTL + single-use ledger) — design has not started (M4).
- `JoeStateSnapshot` is a partial copy of Harlo's v9 envelope — design has not started (M3).
- `FormationRequest` / `FormationOutput` are Octavius IPC contracts — depend on Octavius existing (B2 / q001).
- The pattern reference ("follows the `ProductFile` / `BriefPayload` pattern") only applies to two of the four if at all — and even then loosely.

A single-session L5 will produce four under-specified dataclasses. The "follows the pattern" framing in the brief skeleton suggests the dispatcher believes these are roughly equivalent in design weight. They are not. **L5 should be split into ≥3 lanes:** L5a (LockoutResponse, depends on a D-entry resolving the field shape), L5b (OverrideToken, depends on a D-entry resolving the security substrate), L5c (JoeStateSnapshot, depends on a D-entry resolving the field set), and L5d (FormationRequest/Output, depends on Octavius existing or a stipulated contract).

Note: `LockoutResponse` isn't in ROADMAP §4 L5's list at all — it is "schemas 2–5" naming `OverrideToken, JoeStateSnapshot, FormationRequest, FormationOutput`. But REVIEW_2026-05-22.md Action 3 (line 214–220) names `LockoutResponse` as Schema 2 (the first to add after `ProducerPhase`). The ROADMAP list and the REVIEW list disagree on which four schemas L5 covers. This is contract drift between two source docs.

### M6 — L6 FastMCP shape has zero specification; the ten tool contracts are not defined

**Surface:** ROADMAP §4 line 278; HANNA_BLUEPRINT.md §5 lines 153–163; `python/hanna/mcp_server.py` (doesn't exist).

The ten `hanna_*` tools are named in BLUEPRINT §5 but for each tool the input parameters, the structured-JSON return shape (other than `LockoutResponse` during lockout), the side-effect surface (which write to which SQLite table? which call to which composer? which trigger on the Calendar channel?), and the error-as-structured-response posture per SESSION_01_RECON.md:58 are zero-spec'd. ROADMAP §4 L6 fits this entire surface in one paragraph: "Author `python/hanna/mcp_server.py` with the `hanna_morning_brief`, `hanna_midday_check`, …, `hanna_formation_request` tools. Each tool calls the composer + the Calendar channel."

That's ten contracts in one sentence. The MCP tool list also has internal asymmetry: `hanna_morning_brief` / `hanna_midday_check` / `hanna_evening_capsule` are scheduled-rhythm tools that compose-and-publish, but `hanna_log` / `hanna_block` / `hanna_unblock` (per BLUEPRINT §5.6 line 197) are state-mutating tools that write to product files. The lane spec does not distinguish these classes. NEXT.md §C.4 notes `LockoutResponse` is needed before L6 — true — but doesn't mention that the *non-lockout* tool returns also have no shape.

### M7 — Composer state-blind mode is incompletely specified for the Calendar channel

**Surface:** `scripts/first_hanna_brief.py:53–58, 85–91`; D006 implications bullet 4 ("Brief composer voice calibrates to a calendar-event-notes context"); L4b spec.

The PoC already handles Harlo-unreachable degradation by returning "Harlo edge unreachable — Hanna is operating **state-blind**." This is fine for stdout. But for a Calendar event, the title-and-body pair is the user's only signal — what does the event title say when the bridge is down? "Hanna · morning" with body "state-blind"? Per D006 Implications bullet 5: "Calendar events are NOT created during FAMILY_LOCKOUT." But what about during state-blind mode? Publish anyway with a degraded body? Skip and queue? Skip and never retry?

The lane spec doesn't say. The brief composer rewrite (L4a, already landed) decided the brief composes either way. The Calendar lane has to decide whether degraded briefs publish. Joe waking up to "Hanna · morning — state-blind" lands the friction; Joe waking up to no event lands a silent failure. Both are bad in different ways; both need a D-entry or at minimum a documented stance in the lane spec.

### M8 — Lane DAG soft-dependency between L4b and L4a's BriefPayload is satisfied; the hard inverse (L4a depending on L4b for the publish surface) is hidden

**Surface:** ROADMAP §3 lane DAG; `src/schemas.py:131–136`; `scripts/first_hanna_brief.py:151–156`.

L4a shipped `BriefPayload` with four fields (`phase`, `composed_at_iso`, `body_markdown`, `referenced_products`). L4b is the *first consumer* of that schema. If L4b discovers that `BriefPayload` needs additional fields for Calendar publish (B3 above: rhythm-anchor time; M7: degraded-mode flag; possibly an event-title hint or a body-truncation pre-check), L4a's schema needs to grow. The DAG draws L4a → L4b → Real as a one-way arrow, but the contract feedback loop (L4b discovers L4a's schema is insufficient) is not surfaced. This is the "main-thread integration merges both into the single file" pattern mentioned at ROADMAP §3 line 73, but that pattern was for the original parallel-pair execution. Now that L4a is shipped and merged, L4b inheriting an inadequate schema means main-thread integration becomes a schema migration.

---

## MINOR findings

### m1 — `tests/test_calendar_body.py` per NEXT.md line 73 is not in ROADMAP §4 L4b's files-touched list

NEXT.md line 73 calls for `src/channels/_calendar_body.py` (with `format_brief_body_for_calendar(body: str, max_chars: int = 1024) -> str` truncation helper) and `tests/test_calendar_body.py` (≥3 cases). ROADMAP §4 L4b lines 245–249 lists three files plus the schema and the launcher; the body-formatter helper and its tests are absent. The dispatcher reading ROADMAP will skip them; the dispatcher reading NEXT.md will include them. Contract drift between source docs.

### m2 — The ≤1024-char truncation rule cited by ROADMAP §4 L4b line 265 is asserted, not sourced

"per Apple Calendar's body-text constraints — no images, basic markdown, ≤1024 chars per event for safety" — Apple Calendar accepts much larger event notes (multi-kB); the 1024-char number appears to be a heuristic. If it is, fine, but the spec asserts it as a constraint. A dispatcher implementing strict truncation at 1024 will silently drop content in briefs that exceed it (today's PoC composes ~250–500 chars but as products accumulate this grows).

### m3 — `archive(event_id)` is in the L4b file-list but has no rhythm — when does archive happen?

ROADMAP §4 L4b line 247 specifies `archive(event_id: CalendarEventId) -> None` moves the event to `Hanna · Archive`. But nothing in the spec calls this method. Is archive triggered by the next morning's compose? By a separate scheduled tool? By the user marking the event done? The completion criteria mention "≥6 mocked-subprocess tests (3 each for `publish` and `archive`)" — the archive method gets equal test weight but zero call-site spec. Either an L4b sub-task or a future-lane reference is missing.

### m4 — L4b reviewer audit item ("Rule 34 lockout check exists at the publish call site") presumes a call-site decision the lane spec doesn't make

The Rule 34 lockout gate at the publish site is reasonable but lives in `publish()`-call ordering: does `publish()` itself check `compute_producer_phase()`, or does the caller check before calling `publish()`? NEXT.md line 72 says `publish()` returns `None` during FAMILY_LOCKOUT (gate inside the method); the L4b reviewer item assumes a call-site gate. These are two different architectures. If `publish()` is the gate, every test of `publish()` has to set up phase context; if the caller is the gate, `publish()` is simple but the integration is duplicated everywhere a caller exists.

### m5 — `data/products/*.md` are committed but the lane assumption about Joe-edits-pushes is not strictly checked

D007.6 ratified `data/products/*.md` tracked — Joe edits → commits → Hanna reads. But there's no guard that Hanna re-reads on file change; the composer reads on each compose-call (good), so this works at the rhythm-time grain. However, if a `hanna_log` MCP tool (M6, deferred to L6) writes back to the product file mid-day, the substrate has two writers (Joe via editor; Hanna via MCP) with no coordination. D007.5 ratified the future `hanna_log` tool as "APPEND-ONLY semantics (never overwrite Joe's hand-edits)" but the schema (parser at `src/schemas.py:52–102`) doesn't enforce append-only — it parses the whole file. If L6 implements `hanna_log` with naive overwrite, Joe's edits are silently lost.

### m6 — Rule 18 (RED override) routing path through the Calendar channel is not specified

BLUEPRINT §4 line 125 keeps Rule 18 as "active now via the Harlo bridge's `read_burnout_level`." But the publish path doesn't gate on burnout. If Harlo reads `RED`, what does the Calendar event do? The PoC just surfaces `burnout reads **{burnout}**` in the brief body (`_state_line` at `scripts/first_hanna_brief.py:88`). RED is a hard override that means "no work surface during recovery" per Harlo's contract — and the Calendar event is the work-surface. The spec doesn't say whether RED suppresses publish.

### m7 — `bin/hanna-brief.command` still has Phase-1 / Phase-2 comments referencing the static HTML mockup

Lines 6–10 of `bin/hanna-brief.command` describe Phase 2 as "runs the python script that generates a fresh brief from live Harlo state, then opens the rendered result." That's the pre-D006 framing (browser delivery). The Phase-2 swap per ROADMAP §4 L4b changes the *behavior* but the launcher's commentary lags. Cosmetic but it carries forward the wrong mental model. Update with the lane.

---

## Forward-blocker analysis — shortest credible path to "Hanna is real"

**Definition of "real":** A morning brief lands on Joe's iCloud calendar at 09:00 ET Monday on a real macOS host.

**Current state:** L1–L4a + L3b shipped; L4b queued, deps done. Per c004, L4b is unblocked.

**Critical path:**

1. **D-entry on B3 (rhythm-time anchor).** Either grow `BriefPayload` with `rhythm_anchor_iso`, or add `compute_rhythm_anchor(phase, today) -> datetime` as a fifth `src/computations/*.py`. Without this, L4b ships and the event lands at compose-moment, not the rhythm time. Roughly half-session of design + a D-entry.
2. **L4b dispatch with the explicit cross-platform posture (M1 + M2 + m1 + m4 surfaced).** Bridge Engineer + Brief Composer + Compliance Reviewer per NEXT.md line 70–74. Add the platform gate, the `publish-now` CLI subcommand contract, the `HannaCalendarNotAvailable` exception, the body-formatter helper. ~1 session.
3. **Manual Mac-side verification.** Joe runs `python3 scripts/first_hanna_brief.py` on his Mac, observes the event land on the `Hanna` calendar at 09:00 ET. Not automatable; not on CI.

**That's it.** L5/L6/L7 are *post*-real lanes per the ROADMAP DAG. Reaching "real" requires step 1 to be ratified before step 2 starts, but step 1 is small.

**Parallelizable from current HEAD:**
- L4b is the only queued lane with done dependencies. No parallel sibling.
- L5 schema work could *partially* start (the design of `LockoutResponse` field shape) but is blocked on a D-entry for q002 → can't author code yet.
- L7 cannot start (B2: Octavius does not exist).

**Blocked, in order of unblock cost:**
- L5a (LockoutResponse) — blocked on a single D-entry resolving q002. Cheapest unblock.
- L5b (OverrideToken) — blocked on a D-entry on the security substrate (M4). Medium unblock.
- L5c (JoeStateSnapshot) — blocked on a D-entry on field set + Harlo-coupling posture (M3). Medium unblock.
- L5d (FormationRequest/Output) + L7 — blocked on Octavius existing (q001 → B2). Heaviest unblock.
- L6 — blocked on L5a (LockoutResponse) at minimum; in practice on a full L6 contract-design D-entry (M6). Largest unblock.

**Recommendation framing (no specific actions per scope):** the orchestrator can ship L4b independently and "Hanna is real" on Joe's Mac, but every post-Real lane has a contract gap that wants a D-entry first. The pattern from the c003 belief (workers' "done" warrants moderate confidence) applies in reverse here: skipping the D-entry and dispatching L5/L6/L7 anyway will produce schemas that look right and fail on the first real consumer.

---

## Proposed belief deltas (orchestrator to validate)

```yaml
- claim_id: c006
  claim: "L4b can ship as-spec'd in ROADMAP §4 only after a D-entry resolves the rhythm-time anchor; otherwise the published event lands at compose-moment, not the rhythm time, and D006's posture-fit reasoning fails on the first morning brief."
  suggested_confidence: 0.85
  evidence: "BriefPayload.composed_at_iso constructed at scripts/first_hanna_brief.py:138 as datetime.now(timezone.utc).isoformat(); ROADMAP §4 L4b line 263 hardcodes 'start time: brief.composed_at_iso'; D006 reasoning requires rhythm-time anchor; no compute_rhythm_anchor exists."

- claim_id: c007
  claim: "L5 as catalogued in ROADMAP §4 (one session, four schemas, 'follows the ProductFile/BriefPayload pattern') is under-specified by a factor of ≥3; OverrideToken, JoeStateSnapshot, and FormationRequest/Output each need a precursor D-entry before authoring."
  suggested_confidence: 0.8
  evidence: "REVIEW_2026-05-22.md:117–134 surfaces zero shape for OverrideToken and incomplete shape for JoeStateSnapshot; ROADMAP §4 L5 lists four schemas in one sentence with effort ~1 session; security primitives (OverrideToken) and IPC contracts (FormationRequest/Output) do not fit ProductFile's parsed-file shape; LockoutResponse is named at REVIEW_2026-05-22.md:214 as Schema 2 but absent from ROADMAP L5's four — contract drift between source docs."

- claim_id: c008
  claim: "Octavius does not exist as a repo at HEAD; L7 cannot start; q001 captures the right question but L7's lane spec presumes a known IPC envelope that does not exist."
  suggested_confidence: 0.9
  evidence: "find . -name '*octavius*' returns only data/products/octavius.md (a product-file stub); HANNA_BLUEPRINT.md §9 specifies three Octavius method names but zero IPC envelope; q001 in state/open_questions.md is open with medium leverage."

- claim_id: c009
  claim: "The CI runner is ubuntu-latest; the publish path is osascript (macOS-only); the L4b lane spec in ROADMAP §4 does not name HannaCalendarNotAvailable as required exception, but NEXT.md does — drift between two source docs that the dispatcher must reconcile or the module fails to import on CI."
  suggested_confidence: 0.85
  evidence: ".github/workflows/ci.yml line 11 'runs-on: ubuntu-latest'; ROADMAP §4 L4b lines 263–271 lists only HannaCalendarNotFound; NEXT.md line 72 lists three exceptions including HannaCalendarNotAvailable; subprocess.run(['osascript', …]) raises FileNotFoundError on Linux."

- claim_id: c010
  claim: "L6 cannot author the ten hanna_* tools because nine of ten tool contracts (input params, return shape, side-effect surface, error-as-structured-response posture) are zero-spec'd in ROADMAP §4 line 278; the lockout-shape gap (q002) is necessary but not sufficient."
  suggested_confidence: 0.8
  evidence: "HANNA_BLUEPRINT.md §5 lines 153–163 lists ten tool names; no input/return/side-effect spec for any of the ten; ROADMAP §4 L6 paragraph compresses ten contracts to one sentence; LockoutResponse (q002) is one gap; the other nine returns (composer outputs as structured JSON) are also undefined per REVIEW_2026-05-22.md:129–130."
```

---

## Open questions surfaced

```yaml
- question_id: q004
  question: "Rhythm-time anchor — where does the Calendar event's start time come from? Options: (a) grow BriefPayload with rhythm_anchor_iso; (b) add compute_rhythm_anchor(phase, today_date) -> datetime as a fifth pure computation; (c) accept compose-moment placement and degrade D006's posture-fit claim. The decision affects L4b schema, the channel implementation, and downstream lanes that author events."
  leverage: high
  rationale: "B3 — L4b ships wrong without this. Blocks Real."

- question_id: q005
  question: "State-blind + Calendar — when Harlo is unreachable, does L4b publish a degraded event ('state-blind' body) or skip publish? When Harlo reads RED (Rule 18), does L4b publish or suppress? Both are unspecified in the lane brief."
  leverage: medium
  rationale: "M7 + m6 — surfaces a Rule-18 + D006 interaction that has no decision. Affects Joe's first-Monday experience."

- question_id: q006
  question: "L5 split — does L5 stay as one lane authoring four under-specified schemas, or split into L5a (LockoutResponse, gated on q002), L5b (OverrideToken, gated on a security-substrate D-entry), L5c (JoeStateSnapshot, gated on a Harlo-coupling D-entry), L5d (FormationRequest/Output, gated on q001/B2)?"
  leverage: medium
  rationale: "M5 — the current L5 spec produces four wrong-shape schemas in one session; the split adds D-entries but produces correct contracts."
```

---

## Noticed (out-of-scope per the contract)

- `src/computations/compute_producer_phase.py:32` returns `MONTHLY` whenever `now.day == monthly_day` (default 1) regardless of hour — meaning every brief composed on the 1st of a month between 09–17 ET returns `MONTHLY`, never falling through to MORNING/MIDDAY/EVENING for that day. Adversarial: the morning brief on the 1st of the month does not exist; instead a `monthly` brief replaces it. Whether that is correct depends on Joe's intent for "monthly" (the morning slot is overwritten? or monthly is its own additional cadence?). Belongs to scout-code-quality or scout-tests.
- The CI workflow's "Rule 1 — no sleep() calls" grep excludes `tests/` but `tests/test_first_hanna_brief.py` is allowed sleeps; the grep also wouldn't catch `time.sleep`-via-import-alias. Belongs to scout-security-rules.
- `docs/SESSION_01_RECON.md` §G claim that "33 rules do not exist in Harlo" is q003; flagged in `state/open_questions.md` already.
- BLUEPRINT §11 day-zero remains divided into 11.1 PoC (shipped) and 11.2 long-form (post-PoC target); the lane DAG does not say when 11.2 is satisfied. Belongs to scout-docs.

---

*End of findings. Read-only pass. Belief deltas and open questions surfaced for orchestrator to validate/write.*
