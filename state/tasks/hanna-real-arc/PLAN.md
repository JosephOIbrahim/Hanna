# PLAN.md — live line-of-attack structure

**Updated:** 2026-05-25 (SKETCH gate)
**Mode:** ORCHESTRATED TEAM (per Complexity Gate; see DIGEST.md)
**Effective independent lines:** 3 (graph-predicted; not probed; rationale in DIGEST.md)

---

## Initial line structure

### Line A — L4b Calendar channel
**GOAL:** Ship `src/channels/calendar.py` + `CalendarEventId` schema + reconciliation column on `briefs` + the 4 sibling launchd .plists, satisfying P2 + P6 + part of P9.
**CONTRACT:** P2 (calendar publish + idempotency end-to-end), P6 (reconciliation invariant), P9 partial (launchd-side restart survival).
**VERIFIER:** L1 mocked osascript + tmp_path SQLite; L2 idempotency property; **L3 + L4 require Joe's Mac** (P2 stochastic).
**Proposal queue (ranked):**
1. Author `src/channels/__init__.py` + `src/channels/calendar.py` with `publish(brief)` + `archive(event_id)` per ROADMAP §4 L4b spec, honoring D010 (`brief.phase_anchor_iso` as event-start) + D011 (`HannaCalendarNotAvailable` on non-mac) + D012 (lookup by `brief_id` before insert) + 0-min anchor events.
2. Add `CalendarEventId = NewType("CalendarEventId", str)` to `src/schemas.py`. Add `calendar_event_uid TEXT` and `unpublished_reason TEXT` columns to the `briefs` table; back-compat via ALTER TABLE in `_apply_pragmas` or a migration helper.
3. Wire `publish()` into `scripts/first_hanna_brief.py` `main()` after `_persist()`; populate the new SQLite columns.
4. Author 4 sibling `.plist` files (`bin/com.hanna.brief.{midday,evening,weekly_monday,weekly_friday}.plist`) — each per its D010 anchor; update `bin/README.md`.
5. Author `tests/test_calendar.py` (≥6 mocked-subprocess) + `tests/test_reconciliation.py` (property: every `briefs` row has UID or reason).
**Verifier-gates-progression:** each proposal lands only after L0+L1 pass on it.
**DEADENDS check:** no prior dead ends touch this line.

### Line B — L5 schemas + q002/q007 substrate decisions
**GOAL:** Author `OverrideToken`, `JoeStateSnapshot`, `FormationRequest`, `FormationOutput` in `src/schemas.py`. Author D014 ratifying `LockoutResponse` shape (q002) and D015 ratifying brief composition boundary (q007). These are substrate-decision-class per D002; author-by-main-thread.
**CONTRACT:** Enables P1 (MCP tools have schema inputs/outputs), P5 (LockoutResponse shape exists), and unblocks Line C entirely.
**VERIFIER:** L0 parse + L1 dataclass-construction tests; L2 frozen-immutability + serialization round-trip property.
**Proposal queue (ranked):**
1. D014 `LockoutResponse` shape ratification (q002 close). Open the rejected-alternatives explicitly: error-with-rich-message vs structured-no-op-JSON vs decorator-injected-skip. Pick structured-no-op-JSON per Rule 36 + Claude Code render-meaningfully.
2. D015 brief composition boundary ratification (q007 close). Likely shape: composition = single MCP-tool invocation; `begin_composition`/`end_composition` brackets one tool body. Document.
3. Author the 4 L5 schemas in `src/schemas.py` (frozen dataclasses; `OverrideToken` carries `token: str` + `expires_at_iso: str` + `signature: str` — actual HMAC happens at the verifier site, not in the schema).
4. Author `tests/test_schemas.py` extensions: ≥3 cases per schema per CONVENTIONS §1.
**DEADENDS check:** no prior dead ends touch this line.

### Line C — Octavius reachability spike (F3 risk-burn)
**GOAL:** Resolve F3 before L7 builds: does Octavius exist as a runnable subprocess? Single research dispatch; outcome is a finding doc + a D-entry (D016) recording reachable / not-reachable / partial.
**CONTRACT:** F3 (falsification condition #3); blocks Line D (L7) until resolved.
**VERIFIER:** L1 — can `subprocess.Popen(["octavius", "mcp"])` spawn successfully on Joe's Mac? L2 — does it accept the MCP-stdio framing per HANNA_BLUEPRINT.md §9? L3 — does a spawn/poll/harvest round-trip return a structured payload?
**Proposal queue (ranked):**
1. Spike dispatch: critic[evaluate] reads the Octavius repo (if Joe shares a path) or surveys BLUEPRINT/RULES for the assumed Octavius contract. Returns: reachable / not-reachable + evidence + a D016 draft.
2. D016 ratifies the finding. If not-reachable: arc reorganizes — L7 splits into "spec Octavius contract for future" + "stub octavius_bridge.py with NotImplementedError + tests".
**DEADENDS check:** no prior dead ends; this IS a risk-burn line.

### Line D — L6 mcp_tools (held; depends on A, B, C)
**STATUS:** **HELD** until Lines A + B + C land their core deliverables. Pre-conditions: L4b ships (so `hanna_morning_brief` has a publish path); L5 schemas exist (so tools have types); D014 LockoutResponse shape ratified; D015 composition boundary ratified; F3 outcome known.
**GOAL:** Author `python/hanna/mcp_server.py` with the 10 `hanna_*` tools. Wire Rule 34 layer-3 gates. Satisfies P1 + P3 + P5 + part of P4.
**Will be opened at REORGANIZE** after Lines A + B + C converge.

### Line E — Integration + Stress + Ship (held; arc-terminal)
**STATUS:** **HELD** until Line D ships.
**GOAL:** Run the SPEC arc through the harness's INTEGRATE + STRESS + SHIP gates. P9 (restart survival) and P10 (7-day real-Mac trial) are exercised here.

---

## Ranking rationale (Operating Principle 1: every claim falsifiable)

- **Line A first-class because:** L4b is the named-next lane per ROADMAP §5; the prior cycle (PR #2) explicitly unblocked it (D010/D011/D012 ratified + frame-coalescing regression test). The proposal queue is already partially specified by the ROADMAP §4 L4b brief. Falsifying claim: if L4b's spec is unactionable as-written, the line stalls — but the prior cycle's verify pass on D010–D012 covers this.
- **Line B first-class because:** L5 schemas are decision-shaped (q002 + q007 are open and gate L6) and the 4 dataclasses are mechanical. Lower agent cost than A; high downstream value. Falsifying claim: if L5 schemas need integration with code that doesn't exist yet (e.g., `OverrideToken` needs a verifier site), they ship as schemas-only and the verifier site lands at Line D — verified by the existing D004 reviewer pattern.
- **Line C first-class because:** F3 is the largest single arc risk. Burning it early prevents downstream stall. Falsifying claim: if Octavius IS reachable today, the spike returns in < 1 agent-cycle and confirms a default; if it ISN'T, the arc reorganizes early — both outcomes save more time than they cost.

## Critique-before-build (FORUM standing critique on opening this PLAN)

- **Critic on Line A:** the calendar publish path can't be L3-verified in this Linux dev env. Counter: mocked L1 + L2 + Joe's Mac runs L3 + L4. Acceptable per the SPEC's verification strategy.
- **Critic on Line B:** "schemas without code that uses them is decoration." Counter: q002 + q007 ratifications close real open questions independent of code. Schemas ship as L0+L1 only; integration is Line D's job — both lines need each other to be complete, but neither stalls the other.
- **Critic on Line C:** "spike-before-build is bookkeeping; just stub the bridge." Counter: stubbing-without-knowing leaves F3 unknown; the arc terminator (P4) is gated on knowing. Spike is cheap (1 dispatch) and information-bearing.
- **Critic on holding Line D:** "you're sequencing what could be parallel." Counter: L6 imports the L5 schemas; building L6 first means re-writing imports later. The hold is real dependency, not over-caution.

## REORGANIZE triggers (per harness Operating Principle 7)

- Any line that produces 3 successive proposals with no champion-score gain → reorganize.
- F3 resolves "not reachable" → reorganize: split Line D's `hanna_formation_request` into "stub with NotImplementedError" + "spec the future contract"; weaken P4 to "stub returns LockoutResponse-equivalent until Octavius ships."
- Effort budget at 25 of 50 agents → checkpoint review with Joe.

## Mode statement

ORCHESTRATED TEAM mode is declared per the Complexity Gate (BREADTH=high, INDEPENDENCE=medium-effective after contention discount, HORIZON=long, REWORK COST=high, VERIFIER COST=medium, external launcher available). The orchestrator-as-monitor invokes worker / critic / planner subagents via Claude Code's Agent tool; each runs in its own context with declared INPUTS; reads-state-acts-writes-state heartbeat via the K+S artifact files. Claim/lock protocol: the line tag (`A` / `B` / `C`) anchors writes; no two workers claim the same line at once.
