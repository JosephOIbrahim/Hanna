# scout-architecture findings

Audit performed 2026-05-29 in MODE=red_team over the substrate-decision stack (D001–D009),
orchestrator self-consistency, lane DAG, and inheritance-table coherence. Read-only pass over
the files declared in INPUTS plus the actually-present `state/` directory.

## BLOCKER (0 items)

None. The substrate-decision stack hangs together as a coherent story (Harlo edge reconciled →
MoE methodology → trailer hygiene → bridge hardening → channel + input surface + §4 inheritance →
orchestrator umbrella). No latent contradictions sharp enough to block L4b.

## MAJOR (4 items)

- **§7 adapter is violated by the live `state/plan.md`**: ORCHESTRATOR.md §7 line 297 names
  `plan.md` as an **alias** for `docs/ROADMAP.md` §5 + the NEXT.md GOAL block, and §7 closes
  with *"`state/` contains exactly `beliefs.md` and `open_questions.md` until a live GOAL writes
  ephemeral `gate.md` / `tasks/`."* But `state/plan.md` is a standing file that pre-dates this
  scout invocation (created during the scout-phase plan, not as a GOAL ephemeral). It is exactly
  the "pointer-of-a-pointer" the adapter rule forbids; the current `state/plan.md` even contains
  the GOAL/EXIT_CRITERIA block the adapter says should live in NEXT.md. evidence:
  `/home/user/Hanna/ORCHESTRATOR.md:293, 297, 306-308`; `/home/user/Hanna/state/plan.md:1-59`;
  rationale: the very first ratified workflow under D009 violates the adapter table that D009
  installs; this is the drift the rule was meant to prevent and it surfaced inside one session of
  ratification. The fix is either (a) move the live-GOAL block into NEXT.md per §7 and treat
  `state/plan.md` as ephemeral during a GOAL, or (b) amend §7 to legalize a standing
  `state/plan.md` for research-shaped GOALs (the current research GOAL is non-lane-shaped so
  §8 says the orchestrator drives directly — but the file location is still the question).

- **D006 cross-platform fault line is unresolved and not surfaced in open_questions.md**:
  D006 ratifies "dedicated `Hanna` iCloud calendar" with implementation "via `osascript Calendar`
  on macOS"; ROADMAP L4b spec line 256 makes "macOS host with Calendar.app set up" a completion
  criterion, and D006 Implications line 325 says "CalDAV / EventKit cross-platform considered
  later." But: (1) `bin/hanna-brief.command` is a `.command` file — a macOS-specific Launcher
  artifact; (2) the README "always-on" claim per D006 implications is operationalized only on
  Joe's Macs; (3) ROADMAP L7 (`octavius_bridge.py`) and BLUEPRINT §9 frame Octavius as running
  "in its own venv as a child process," which is platform-neutral, but the channel is not. Joe
  "lives in Houdini and on iPhone" per the D006 reasoning — iPhone is the consumer of calendar
  events, not the author, so iCloud-sync is fine for read. But there is no documented stance on:
  what happens when Joe is on a non-mac Linux build host running CI? (CI already exists per L2.)
  Is the brief never published from CI? Is L4b CI-skipped? evidence:
  `/home/user/Hanna/docs/DECISIONS.md:307, 325`; `/home/user/Hanna/docs/ROADMAP.md:247, 256, 269`;
  `/home/user/Hanna/HANNA_BLUEPRINT.md:199`; rationale: L4b is the next queued lane (c004 has
  confidence 0.9) and the platform question is one Joe will hit on the first dispatch. A
  pre-L4b open_question with high leverage would prevent the lane from being filed before that
  is resolved.

- **D001 / D005.1 contract drift around "per brief composition"**: D001 establishes the
  `coach` rate-limit semantic as "≤1 call per brief composition" with the rate limit "living in
  the bridge, not in calling code" (DECISIONS.md:69). D005.1 ratifies `begin_composition` /
  `end_composition` scope methods as the implementation of that semantic. But neither D001 nor
  D005 names what a "brief composition" is in machine-checkable terms — is it the lifetime of a
  single MCP-tool call (`hanna_morning_brief`)? Is it one publish-call to the Calendar channel?
  Is it the L4a composer's `compose_brief` function call? Today's PoC at
  `scripts/first_hanna_brief.py` (per D005 implications line 284) "accidentally" satisfies the
  rule via short-lived bridge instances. L4b (channel) and L6 (mcp_tools) will both invoke the
  composer and the bridge in new shapes; the next ratifier will have to define the boundary
  ad-hoc unless a follow-on D-entry binds it. evidence:
  `/home/user/Hanna/docs/DECISIONS.md:58, 69, 256-264, 284`; rationale: the semantic is a
  cross-lane contract (computations + bridge + mcp_tools + channels all touch it) and the
  current load-bearing definition is "whatever the PoC happens to do." This will resurface as a
  L6 design question and would be cheaper to ratify before L6 starts.

- **Decision-log format drift on rejected alternatives**: The DECISIONS.md template at lines
  15-29 names the standard sections (Decision / Reasoning / Implications / Related). It does NOT
  require an explicit "Rejected alternatives" section. D003 has one in narrative form (line 188),
  D009 has a formal block (line 494) — but D001, D002, D005, D006, D007, D008 fold their
  rejected alternatives into the Reasoning paragraph (D005 lists "(a)/(b)/(c)" candidates per
  sub-decision; D006 lists iMessage / osascript / browser inline; D007 lists three input layers
  inline). The format works for human reading but is inconsistent with the planner agent's
  contract (`/home/user/Hanna/.claude/agents/planner.md:18-19`: *"Record design choices WITH
  rejected alternatives"*), and a future critic auditing decision-log quality has no canonical
  surface to grep. evidence: `/home/user/Hanna/docs/DECISIONS.md:15-29, 188, 494`;
  `/home/user/Hanna/.claude/agents/planner.md:18`; rationale: low cost to fix (amend the template
  to require a "Rejected alternatives" block; backfill D001/D002/D005/D006/D007/D008 with
  one-line summaries citing the existing prose). Buys uniformity for the planner's contract
  and a stable grep surface.

## MINOR (5 items)

- **Rule 34 timezone ambiguity**: RULES.md §34 (line 183) says "Mon–Fri 09:00–17:00" without a
  timezone; CLAUDE.md line 60 says "Mon–Fri 09:00–17:00 ET"; BLUEPRINT §11.1 line 330 says
  "Mon–Fri 09:00–17:00 ET"; BLUEPRINT §7 line 229 says "Mon–Fri 9–5"; tests pass per ROADMAP L3a
  ≥3 boundary cases per CONVENTIONS §1 but the rule-canonical doc has no tz. evidence:
  `/home/user/Hanna/RULES.md:181-183`; `/home/user/Hanna/CLAUDE.md:60`;
  `/home/user/Hanna/HANNA_BLUEPRINT.md:229, 330`; rationale: rules are inviolable per the file
  header; an inviolable rule that omits its discriminating constant is a quality issue.

- **BLUEPRINT §7 layer-count tension residual**: §7 line 230 says "The lockout model is now two
  active layers (1 + 3)" and line 235 says "Tests verify the two active layers (1 + 3)." But the
  RULES.md §34 text (lines 181-185) still enumerates "three layers" and the §34 numbering goes
  1/2/3 with no Cut annotation on layer 2 in RULES.md itself. CodeRabbit round 3 fixed a
  "README §Rules layer-count contradiction" per NEXT.md, but the same contradiction now lives
  inside RULES.md. evidence: `/home/user/Hanna/RULES.md:181-185`;
  `/home/user/Hanna/HANNA_BLUEPRINT.md:230, 235`; rationale: a reader of RULES.md alone has no
  way to know layer 2 was Cut by D008.1; tying the rule text to its substrate decision is the
  D008.7 selective-re-adoption posture's whole point.

- **L4a "done" lacks belief-layer evidence for c001's high confidence**: c001 in beliefs.md
  asserts L1–L4a + L3b shipped with confidence 1.0, citing "PR #1 merged" and "NEXT.md 2026-05-22
  post-merge section." But c003 explicitly captures that "A worker's done claim warrants only
  moderate confidence until an independent critic[verify] pass confirms it" (confidence 0.7,
  citing the 4 latent bugs CodeRabbit round 3 found). No critic[verify] pass against the L4a
  EXIT_CRITERIA in ROADMAP §4 is recorded as evidence for c001; the merge is the evidence.
  evidence: `/home/user/Hanna/state/beliefs.md:11, 13`;
  `/home/user/Hanna/docs/ROADMAP.md:220-224`; rationale: the belief layer's own discipline asks
  for an explicit verify pass as the source of "done" confidence — c001 at 1.0 contradicts c003.
  Not a blocker (merge is real), but a minor consistency issue for the belief layer.

- **D004 reviewer-check rule lacks a CI/grep surface**: D004 Clause A installs a
  reviewer-checklist item (every cloned-from-Harlo file must carry the attribution trailer
  within first 20 lines). The enforcement is human-eyes-on-diff; there is no grep recipe in
  RULES.md §Compliance Checks (lines 219-237) that catches a missing-or-misplaced trailer. The
  comparable Rule 35 / 37 enforcement is grep-backed. evidence:
  `/home/user/Hanna/docs/DECISIONS.md:219-224`; `/home/user/Hanna/RULES.md:217-237`; rationale:
  the reviewer is dispatched on every MoE call, but human attention drifts more than greps
  drift. Low-cost addition.

- **ORCHESTRATOR.md §7 alias for `parked.md` produces a split surface**: §7 line 300 maps
  `parked.md` to `NEXT.md "Open questions still parked" + state/open_questions.md`. This is a
  two-location alias: same conceptual artifact in two places, promoted between them by leverage.
  ORCHESTRATOR.md §6 line 233-243 routes red_team MINOR findings to `parked.md` and `MAJOR
  out-of-scope` to `parked.md with promote: true`. There is no rule about which of the two
  destinations a critic should write to — the orchestrator alone decides per leverage. evidence:
  `/home/user/Hanna/ORCHESTRATOR.md:230-243, 300`; rationale: ambiguity will surface once a
  worker or critic tries to "write to parked.md" and finds two real files; not a blocker because
  the orchestrator is single-writer for promotion.

## Belief deltas (4 proposed)

- claim: ORCHESTRATOR.md §7 forbids standing files under `state/` other than beliefs.md +
  open_questions.md, yet `state/plan.md` exists today as a standing file holding the live GOAL;
  suggested_confidence: 0.9; evidence: ORCHESTRATOR.md:293,297,306-308 + presence of
  /home/user/Hanna/state/plan.md with GOAL/EXIT_CRITERIA block

- claim: D006's Calendar-channel choice is platform-coupled to macOS (`osascript`, `.command`
  launcher) and no D-entry yet resolves how the channel behaves on non-mac hosts (CI, future
  Linux build environments); suggested_confidence: 0.85; evidence: DECISIONS.md:307,325 +
  ROADMAP.md:247,256,269 + BLUEPRINT.md:199

- claim: Beliefs c001 (confidence 1.0) and c003 (confidence 0.7) are in tension — c003 demands an
  independent critic[verify] pass before "done," and c001's evidence cites a merge rather than
  a verify pass; suggested_confidence: 0.7; evidence: state/beliefs.md:11,13 +
  ROADMAP.md:220-224 + absence of a state/tasks/L4a-verify/ artifact

- claim: The substrate-decision stack D001-D009 is internally coherent as an architectural
  story (Harlo edge reconciled → MoE → trailer hygiene → bridge hardening → channel/input
  surface ratifications → §4 cuts → orchestrator umbrella), with no contradictions sharp enough
  to BLOCK the next lane; suggested_confidence: 0.85; evidence: full read of DECISIONS.md D001-D009
  cross-referenced against BLUEPRINT §4/§10/§12 and ROADMAP §2/§5

## Open questions surfaced (3)

- question: What is the canonical machine-checkable boundary for "one brief composition" in the
  D001/D005.1 rate-limit semantic — is it a single MCP-tool call, a single composer.compose()
  invocation, or a single channel.publish() call?; leverage: high; why it matters: L6
  (mcp_tools) will define ≥10 tools that all invoke the composer + bridge; without a binding
  definition, each tool's reviewer will re-litigate the rule

- question: Where is the Calendar channel run from when Joe is not at a macOS host (CI, a Linux
  build, a future remote-deploy posture) — is L4b CI-gated, mac-only, or does it need a
  platform shim before L4b ships?; leverage: high; why it matters: L4b is the next queued lane;
  ratifying this before dispatch saves a re-dispatch cycle and a possible D006 amendment

- question: Should DECISIONS.md's template require an explicit "Rejected alternatives" block
  (matching the planner agent's contract), and should D001/D002/D005/D006/D007/D008 be amended
  with retrofit blocks summarizing their current narrative rejections?; leverage: medium; why
  it matters: planner agent's contract names it as a required output; a stable grep surface
  helps future critics audit decision-log quality

## Out-of-scope but noticed (4)

- area: scout-docs; finding: BLUEPRINT §7 says "two active layers (1 + 3)" while RULES.md §34
  still enumerates the three-layer text with no Cut annotation on layer 2 (doc-vs-rule
  consistency).

- area: scout-security-rules; finding: RULES.md §34 omits a timezone on the canonical
  09:00–17:00 window — every secondary doc names ET but the rule text does not; for an inviolable
  rule this is a precision gap a security reviewer should consider.

- area: scout-ops; finding: D006's Calendar channel is macOS-specific via `osascript` and `.command`
  launcher; L4b completion criteria are macOS-gated; the operational posture for non-mac CI
  or future deploy targets is undefined.

- area: scout-lanes-schemas; finding: L4b's spec (`docs/ROADMAP.md:241-272`) treats
  `bin/hanna-brief.command` as a Phase-2 swap target but does not name what happens to the
  pre-merge file if L4b's CI runs on Linux — the launcher artifact is an unowned cross-lane
  hand-off between channel-lane and any operations lane.
