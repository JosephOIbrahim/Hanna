# scout-docs — findings

**Mode:** critic[red_team]
**Task:** scout-docs
**Scope:** every `.md` at the repo root + every `.md` under `docs/`; `web/templates/morning_brief.html` referenced from BLUEPRINT; `bin/hanna-brief.command` referenced from BLUEPRINT
**HEAD audited:** `c65b6ae` (orchestrator-adoption commit; `main` HEAD per beliefs = `e08aebb`)
**Read-only:** yes

---

## Executive summary

Hanna's documentation is dense, deliberate, and largely coherent across nine root files and eight docs files — but it carries three classes of debt that two reconciliation passes (`2e68877`, `8e83296`) did not catch. **(1) RULES.md §34 is the most visible drift in the repo:** it still describes a three-layer lockout with "Delegate routing (`HdProducer`)" as layer 2, yet D008.1 ratified that delegate Cut and every other doc (README, BLUEPRINT, NEXT, UI_UX_MAP, ORCHESTRATOR.md §9) reflects two active layers. RULES.md's own line-15 applicability note flags layer 2 as Cut, contradicting its own §34 body 170 lines later. **(2) README.md's "Repository layout" is a one-third-true map of the filesystem** — it omits ORCHESTRATOR.md (added in c65b6ae), docs/DECISIONS.md, docs/ROADMAP.md, docs/REVIEW_2026-05-22.md, docs/PRODUCER_LENS.md, docs/UI_UX_MAP.md, docs/SPIKE_HARLO_EDGE_2026-05-20.md, the `state/` durable layer, the `scripts/` directory, the `data/` directory, and the `bin/hanna-brief.command` Phase-2 swap target, and miscalls the BLUEPRINT version as `v0.1.0-draft` when the file self-stamps `v0.2.0-audit`. **(3) HANNA_DESIGN_ADOPTION.md is a stale prompt artifact** that was preserved post-execution but reads as live instructions to a non-existent agent (it tells the reader to `git checkout -b ui-design-adoption`, references "Joe placed it"/"surface and pause if", and embeds duplicate copies of README/BLUEPRINT content that have since drifted from the canonical files). The orchestrator adapter (§7–§9) is internally consistent and the D-entry anchor links are well-formed for GitHub slug resolution; the SESSION_01_RECON §G staleness flag in NEXT.md is still valid (the doc remains uncorrected). Below: 5 BLOCKERs (RULES.md §34 contradiction is the worst; README layout drift is structural; SESSION_01_RECON.md still actively claims rules don't exist in Harlo, contradicting RULES.md itself), 8 MAJORs, 6 MINORs, 4 proposed belief deltas, 3 open questions.

---

## Findings

### BLOCKER

#### B1 — RULES.md §34 body still describes a three-layer lockout with `HdProducer` delegate as layer 2

**File:** `/home/user/Hanna/RULES.md:181-187`

**Observation:** RULES.md §34 body verbatim:
> "Enforced at three layers: 1. State machine (`compute_producer_phase`) ... 2. **Delegate routing (`HdProducer`):** RED-state override is inherited from Rule 18. `FAMILY_LOCKOUT` is the second override. Nothing routes through the delegate during lockout. 3. MCP tool gating ... Tests verify all three layers. **Bypassing any layer fails CI.**"

This text was authored before D008.1 ratified the delegate Cut. RULES.md line 15 (the applicability note added by L1 commit `ec6752a`) now reads: "Layer 2 `HdProducer` delegate Cut per D008.1; Layer 3 per-tool MCP gating deferred." The file therefore contradicts itself: line 15 says two active layers (1+3); lines 181–187 say three active layers including the Cut layer 2.

Every other doc surface has been propagated (HANNA_BLUEPRINT.md §7 line 230 reads "Cut per D008.1 ... lockout model is now two active layers (1+3)"; README.md mermaid §"Family-first" labels layer 2 "Cut per D008.1"; UI_UX_MAP.md §7 marks layer 2 parked with the Cut annotation). RULES.md is the one place a new reader will go for the canonical rule statement, and the canonical rule statement still says HdProducer is the layer-2 enforcer.

**Cross-impact:** Section ends with "Tests verify all three layers. **Bypassing any layer fails CI.**" — that sentence has been false since D008.1 (layer 2 has no implementation surface, so no test verifies it). REVIEW_2026-05-22.md §3.2 flagged "Bypassing any layer fails CI" as aspirational at the time; L2 substrate-hygiene work delivered CI but only covers layers that actually exist.

**Confidence:** high. The contradiction is internal to RULES.md and reproducible by reading lines 15 vs. 181–187 in a single pass.

---

#### B2 — README.md "Repository layout" is stale across 9 of ~15 entries

**File:** `/home/user/Hanna/README.md:155-172`

**Observation:** The layout block claims:
```
HANNA_BLUEPRINT.md          architectural spec (v0.1.0-draft)
RULES.md                    33 inviolable rules + 8 safeguards + 4 addenda
CLAUDE.md                   project-local AI collaboration instructions
NEXT.md                     end-of-day handoff for the next session
NOTICE                      attribution to Harlo substrate
LICENSE                     Apache 2.0
docs/
  CONVENTIONS.md            day-to-day conventions
  SESSION_01_RECON.md       session 1 observation doc
web/
  templates/                Phase-1 design reference (HTML mockups)
  README.md                 design system documentation
bin/
  hanna-brief.command       morning-brief launcher (Phase-1)
```

Drift items, against actual `ls`:
1. **BLUEPRINT version label is wrong.** Layout says `v0.1.0-draft`; HANNA_BLUEPRINT.md line 3 self-stamps `v0.2.0-audit`. Drift was missed by both 2e68877 and 8e83296.
2. **ORCHESTRATOR.md is missing.** Added by `c65b6ae` (D009); README never mentions it in any section.
3. **HANNA_DESIGN_ADOPTION.md is missing.**
4. **docs/DECISIONS.md is missing** — the most cross-referenced file in the repo (D001–D009) is absent from the layout block.
5. **docs/ROADMAP.md is missing** — the single source of truth the harness reads.
6. **docs/REVIEW_2026-05-22.md is missing.**
7. **docs/PRODUCER_LENS.md is missing.**
8. **docs/UI_UX_MAP.md is missing.**
9. **docs/SPIKE_HARLO_EDGE_2026-05-20.md is missing.**
10. **`state/` durable layer is missing** — `beliefs.md`, `open_questions.md`, `plan.md` (ratified in D009).
11. **`scripts/first_hanna_brief.py` is missing** — the day-zero PoC referenced in BLUEPRINT §11.1.
12. **`src/`, `tests/`, `data/`, `.github/`, `pyproject.toml`** — all unmentioned despite shipping in L2/L3a/L3b/L4a.
13. **web/README.md is mentioned but does not exist** — the `web/` listing in HANNA_DESIGN_ADOPTION.md Step 3 says to "create the file" but `ls web/` shows only `templates/` and no `README.md`. Either the design-adoption session never executed Step 3 or the file was later removed.

**Cross-impact:** A new contributor lands on README.md and gets a half-true map. ORCHESTRATOR.md is the operating manual for every multi-agent task in this repo (per D009), and README never points at it. The repository layout is the README's anti-fiction commitment per CLAUDE.md "Each file has one job"; right now the layout fails that test.

**Confidence:** high. Every drift item verifiable by `ls /home/user/Hanna/` and `ls /home/user/Hanna/docs/`.

---

#### B3 — SESSION_01_RECON.md §G still actively claims "RULES.md does not exist in Harlo, synthesize from distributed sources"

**File:** `/home/user/Hanna/docs/SESSION_01_RECON.md:17-19, 264-279`

**Observation:** SESSION_01_RECON.md §A.2: *"`RULES.md` — absent from Harlo. The blueprint at `HANNA_BLUEPRINT.md:290` claims `RULES.md` is cloned from Harlo. No such file exists in `/Users/rustybeard/Code/Harlo` or anywhere under it. What does exist: 12 distinct 'Commandments' (1–12) ..."* and §G: *"the rules live distributed across Harlo's `CLAUDE.md`, the design/verify docs, and the inline-`Commandment N` references in source... 12 distinct Forge Commandments referenced... These read as architect-acting-as-scout discipline rules... They are not 33."*

Per RULES.md line 7: *"Extracted verbatim from [`Harlo/CLAUDE.md` lines 37–194](https://github.com/JosephOIbrahim/Harlo) ('The 33 Inviolable Rules' — 33 numbered rules + 8 inquiry safeguards)."*

The rules exist as 33 numbered items in Harlo/CLAUDE.md exactly where SESSION_01_RECON.md §G claimed they didn't. NEXT.md "Staleness flag — carry forward" already names this contradiction and parks it for Joe's call: correct or stamp as historical. The current posture is "still wrong, still carried."

**Cross-impact:** This is the only documentation in the repo that contradicts the canonical rules-extraction provenance. A reader entering through Session 01 (which the README implies is the historical anchor) gets the wrong answer about where the rules come from. Two of the §G "questions for Joe" are now closed by RULES.md's existence (Phase 1 done, Phase 2 done — the rules were extracted) and one is moot (Session 01.5 was the answer).

**Confidence:** high. Cross-check against RULES.md:7 and Harlo's CLAUDE.md is the proof.

**Recommendation (for orchestrator routing, not action proposal):** the cheapest resolution is a single-paragraph header stamp on the doc — "Stamped historical artifact 2026-MM-DD. §G's claim that rules don't exist in Harlo was inverted by Session 01.5's direct extraction; see RULES.md." Three lines.

---

### MAJOR

#### M1 — HANNA_DESIGN_ADOPTION.md is a session prompt preserved as live doc

**File:** `/home/user/Hanna/HANNA_DESIGN_ADOPTION.md` (entire file)

**Observation:** The file reads as instructions to a session ("Step 1 — Switch branch ... `git checkout main; git checkout -b ui-design-adoption`"; "Step 2 — Validate the file is in position"; "Stop conditions — Surface and pause if: The HTML file isn't at `Hanna/web/templates/morning_brief.html` and Joe hasn't told you where it is"). The session ran (the HTML mockup committed; BLUEPRINT §5 carries the Producer UI Surface subsection). The doc is now a stale prompt.

Two specific drift items inside it:
1. Step 3 instructs the session to create `Hanna/web/README.md` with embedded content. `ls /home/user/Hanna/web/` returns only `templates/` — no `README.md`. The Step-3 instruction was either never executed or the file was later removed.
2. Step 4 prescribes blueprint §5 content that has since been superseded by D006 (Calendar channel) and D008 (USD stage Cut). HANNA_BLUEPRINT.md §5 "Producer UI Surface" line 199 carries the Audit 2026-05-20 note that supersedes the design-adoption prompt's phrasing.
3. The prompt references paths like `Hanna/web/templates/...` (with the repo-name prefix) where the canonical paths are `web/templates/...`.

**Cross-impact:** A new reader landing on HANNA_DESIGN_ADOPTION.md cannot tell whether this is current instructions or a session-stamped artifact. Compare to SESSION_01_RECON.md which is clearly session-stamped (date, branch, mode). HANNA_DESIGN_ADOPTION.md has no such stamp.

**Confidence:** high.

---

#### M2 — README.md mermaid lane diagram is out-of-sync with ROADMAP §5 status table

**File:** `/home/user/Hanna/README.md:107-136` (mermaid) + `/home/user/Hanna/README.md:180-188` (status table)

**Observation:** The README has *two* status surfaces:
- Lines 107–136: a mermaid lane DAG with `:::next` (orange) on Comp / HB / OB / MCPt / Persist / Channels / Day0
- Lines 180–188: a status table where L1, L2, L3a, L3b, L4a are `done` and L4b is `queued (next)`

The mermaid does not distinguish L4a-done from L4b-queued; HarloBridge and Computations are both `:::next` in the diagram even though both shipped (Comp L3a `04af5da`; HB L3b `06effc8`). The text under the diagram says "Yellow = landed. Orange = in flight or scheduled" — but every node downstream of the Rules box is orange, including ones that landed. Only Recon, Rules, UI carry yellow.

**Cross-impact:** The mermaid is the eye-catching surface a new reader sees. It claims six lanes are "in flight or scheduled" when only L4b is. The lane status table 50 lines later corrects the picture, but a reader who scrolled past the diagram has already absorbed the wrong story.

**Confidence:** high. Reproducible by reading the two README surfaces in sequence.

---

#### M3 — REVIEW_2026-05-22.md carries a model-id string that violates CLAUDE.md trailer hygiene posture

**File:** `/home/user/Hanna/docs/REVIEW_2026-05-22.md:4`

**Observation:** Line 4: `**Reviewer:** main-thread (Claude Opus 4.7, 1M context)` — this is precisely the string CLAUDE.md line 46 disallows in commit context ("Any other form (e.g. `Claude Opus 4.7 (1M context)`) trips the auto-mode classifier and is disallowed"). The doc is committed; the string is committed; the prohibition applies to "any committed artifact" per the §9 hard-constraint inheritance in ORCHESTRATOR.md.

CLAUDE.md scope is strictly commit trailers, so this is arguably out-of-scope for that rule — but the §9 hard-constraint inheritance is broader: *"no model-id in any committed artifact."* REVIEW_2026-05-22.md is a committed artifact carrying a model-id.

**Cross-impact:** If the classifier rule is binding on docs and not just commits, this is a violation that no compliance grep currently catches (`grep -rE "claude-opus" docs/` would find CLAUDE.md's model-version trailer text and REVIEW_2026-05-22.md's reviewer line, but the former is the rule statement). The boundary "where does the rule apply" is itself underspecified.

**Confidence:** medium-high. The rule statement in CLAUDE.md is ambiguous on whether prose docs count.

---

#### M4 — RULES.md §35 verbatim Harlo bridge surface contradicts D001 and the actual bridge

**File:** `/home/user/Hanna/RULES.md:193`

**Observation:** §35 body: *"`src/harlo_bridge.py` exposes `read_state`, `read_prediction`, `read_burnout_level`."* This is the v0.1.0 contract. D001 (`docs/DECISIONS.md:43-79`) ratified the expanded contract: the bridge actually exposes `read_state`, `read_burnout_level`, `read_schedule`, `read_prediction`, `drive_coaching_exchange`, `recall`, `query_past_experience`, `patterns`. README.md §"How it relates" line 36 says the same v0.1.0 list. REVIEW_2026-05-22.md §3.3 flagged the README drift; the L1/L3b/L4a propagation did not propagate to RULES.md §35.

The bridge code at `src/harlo_bridge.py` is post-D001 and post-D005-hardened. RULES.md and README.md describe an old surface; the canonical surface is D001 + the spike doc.

**Cross-impact:** RULES.md is the compliance gate's source of truth. The §35 verbatim line is also used as the basis for the compliance grep at line 234 (`grep -rE "harlo\.(write|store|author|mutate)" src/`) — the grep still passes because the new methods don't match those verbs, but the *surface description* in §35 is stale by five method names.

**Confidence:** high. Cross-check RULES.md:193 vs. D001 implications bullet 1.

---

#### M5 — ORCHESTRATOR.md §7 adapter table commits to `NEXT.md` as `checkpoint.md` — partly truthful, not fully wired

**File:** `/home/user/Hanna/ORCHESTRATOR.md:296-299` (table) + `/home/user/Hanna/NEXT.md`

**Observation:** ORCHESTRATOR.md §7 says `checkpoint.md` is aliased to `NEXT.md` with a field crosswalk: *"LAST_TASK ← lane commits; NEXT_TASK ← 'Next session entry point'; OPEN_ISSUES ← 'Open questions still parked'; EXIT_STATUS ← ROADMAP §5 done/queued; TOKENS_USED/BUDGET ← a new field added to NEXT.md when a live GOAL runs."*

NEXT.md as it exists today does NOT carry any of: a structured `LAST_TASK:` field, a `NEXT_TASK:` field, an `EXIT_STATUS:` field, or `TOKENS_USED/BUDGET` fields. It carries narrative text under section headers. The "crosswalk" exists only in the orchestrator's reading — the data in NEXT.md is not labeled with those field names.

The current live GOAL is `state/plan.md`, not NEXT.md. The plan file has GOAL/EXIT_CRITERIA/CONFIDENCE_THRESHOLD/CONSTRAINTS/INPUTS/STATUS — but no CHECKPOINT shape mapping back to NEXT.md.

**Cross-impact:** The adapter promises a single-source-of-truth crosswalk but only the orchestrator (this Claude) knows how to parse it. A second orchestrator instance picking up the work would have to re-derive the crosswalk from prose. The §7 table is aspirational where it claims "no pointer-files" — in practice, the adapter is enforced by reader convention, not by file shape.

**Confidence:** medium-high. ORCHESTRATOR.md §7's last sentence acknowledges the asymmetry: *"`state/` contains exactly `beliefs.md` and `open_questions.md` until a live GOAL writes ephemeral `gate.md` / `tasks/`."* This sentence is now wrong — a live GOAL is running and `state/plan.md` exists. Either §7 should mention `plan.md` as a third ephemeral artifact, or the table's `plan.md` row should distinguish "ROADMAP §5 for lane work; `state/plan.md` for non-lane GOALs."

---

#### M6 — README.md `delegate` bullet in §"Build lanes" leaks delegate vocabulary the rest of the README rejects

**File:** `/home/user/Hanna/README.md:104`

**Observation:** *"`delegate` and `stage` lanes are Cut per [D008](docs/DECISIONS.md) (delegate collapsed into `mcp_tools` layer 3; stage reduced to SQLite tables)."*

This is correct in substance but the README's mermaid §"Family-first" (lines 77–96) shows the Layer 2 `HdProducer delegate` node with `:::cut` styling — the only place in the README a reader sees the *word* "delegate" used as a Hanna construct. New readers may infer that "delegate" is something Hanna has-but-cut, when in fact Hanna never built a delegate at all. The visible Cut artifact may be misread as a removed-file when it is a never-built component.

Less severe than B1 (which is a contradiction); this is an over-clear surfacing of a Cut item that arguably should fade from the diagram entirely once the readership has matured past D008's ratification context.

**Cross-impact:** Minor cognitive load; bigger issue is symmetric with B2 (README's surfaces don't compose into a clean picture).

**Confidence:** medium.

---

#### M7 — UI_UX_MAP.md §7 carries the cut Layer 2 in a parked-class node, perpetuating the same Cut-as-present misread

**File:** `/home/user/Hanna/docs/UI_UX_MAP.md:285-304`

**Observation:** The §7 mermaid still includes `L2{"Layer 2<br/>HdProducer delegate<br/>(D008.1 Cut — collapsed)"}:::parked` and draws a dashed line "D008.1 Cut: layer 2 collapses into layer 3." Same shape as README §"Family-first" — the Cut item appears as a node, possibly confusing first-time readers. UI_UX_MAP.md is more excusable here because its job is to be a navigation map and the cut state has design implications. But it perpetuates the same noise.

**Cross-impact:** Same as M6, scoped to UI_UX_MAP.md.

**Confidence:** medium.

---

#### M8 — README §"Repository layout" gives BLUEPRINT version as v0.1.0-draft against actual v0.2.0-audit

(Covered as part of B2 above, but called out individually because it's the most easily-fixable line of B2 and was missed by both 2e68877 and 8e83296 doc-reconciliation passes.)

**File:** `/home/user/Hanna/README.md:158`

**Cross-impact:** Trivial to fix; symbolic of the broader drift pattern.

**Confidence:** high.

---

### MINOR

#### m1 — CLAUDE.md hardcodes `/Users/rustybeard/Code/Hanna` as project-local instructions

**File:** `/home/user/Hanna/CLAUDE.md:3`

**Observation:** *"this file wins for work inside `/Users/rustybeard/Code/Hanna`"* — Mac-only absolute path, clone artifact per REVIEW_2026-05-22.md §3.3 already-known finding. The project lives at `/home/user/Hanna` in this container. Carried for two reconciliation passes without correction.

**Confidence:** high.

---

#### m2 — BLUEPRINT §"End of blueprint" line still says "Session 1 (recon) reads this document, plus the cloned Harlo source, and produces `docs/SESSION_01_RECON.md` before any code is written"

**File:** `/home/user/Hanna/HANNA_BLUEPRINT.md:420`

**Observation:** Recon has shipped (`docs/SESSION_01_RECON.md` exists), code has been written (L1–L4a + L3b done). The instruction is past-tense in reality and present-tense in the text.

**Confidence:** high.

---

#### m3 — BLUEPRINT line-count claim of "~80 lines" vs. actual 184 lines for `scripts/first_hanna_brief.py`

**File:** `/home/user/Hanna/HANNA_BLUEPRINT.md:325` ("§11.1 Primary day-zero — smaller PoC (one session, ~80 lines)")

**Observation:** REVIEW_2026-05-22.md §3.3 flagged this at 119 lines. The PoC has since grown to 184 lines via L3a and L4a integration (`wc -l /home/user/Hanna/scripts/first_hanna_brief.py`). The "~80 lines" framing is now ~2.3× wrong. Cosmetic.

**Confidence:** high.

---

#### m4 — `state/open_questions.md` q003 leverage marked low but cross-references B3 above

**File:** `/home/user/Hanna/state/open_questions.md:12`

**Observation:** q003 ("SESSION_01_RECON.md §G staleness — correct or stamp as historical?") is leverage=low. Reading B3 above, it's arguable this is leverage=medium: the contradiction is the only place in the repo where canonical-doc-vs-canonical-doc disagreement is durably preserved, and the resolution is a 3-line stamp. Cheap to close, modest signal value (it stops being a recurring item in every doc audit).

**Confidence:** medium. The leverage call is a judgment, not a fact.

---

#### m5 — ROADMAP.md §5 "Last commit" column references commits by message rather than SHA

**File:** `/home/user/Hanna/docs/ROADMAP.md:289-294`

**Observation:** Each "done" row carries the commit subject (`feat(...): ... (Lxx)`) followed by `(this commit; see git log --grep "Lxx")`. Resolvable but indirect; if a reader is scanning for what SHA grounds each lane's completion, they have to grep. NEXT.md `### Lane commits (top of branch, in order before merge)` does carry SHAs and is the better surface.

**Confidence:** medium.

---

#### m6 — DECISIONS.md anchor format check — all D-entry anchors resolvable

**Verification:** spot-checked 4 of the 14 anchor links in DECISIONS.md (the `[D001](#d001--rule-35-permissive-reading-...)` form). Each maps to a real `### D###` heading via the GitHub slug rule (lowercase, hyphens, drop em-dashes' surrounding spaces). E.g.:
- Heading: `### D001 — Rule 35 permissive reading: \`exchange_index\` advance is not a write`
- Anchor used: `#d001--rule-35-permissive-reading-exchange_index-advance-is-not-a-write`
- GitHub slug: lowercase, `—` → blank, spaces → `-`, double-dash where the em-dash sat = matches.

Same pattern verified for D002, D006, D008's anchors used at lines 285, 290, 291, 365, 479, 501–502. **No findings on anchor health.**

**Confidence:** high.

---

## Cross-doc coherence summary

| Surface | What it claims | Drift? |
|---|---|---|
| RULES.md §34 body | 3-layer lockout incl. HdProducer | **YES (B1)** — contradicts RULES.md:15 |
| RULES.md §35 body | Bridge exposes 3 methods | **YES (M4)** — contradicts D001 + actual bridge |
| README.md mermaid §"Family-first" | Layer 2 Cut per D008.1 | clean |
| README.md mermaid §"Build lanes" | 6 of 7 lanes :::next | **YES (M2)** — contradicts status table 50 lines below |
| README.md §"Repository layout" | 6 docs + web + bin | **YES (B2)** — omits 9+ files |
| README.md §"How it relates" | Bridge exposes 3 methods | **YES (carried)** — REVIEW §3.3 surfaced; not propagated |
| BLUEPRINT §4 table | Per D008 ratification | clean |
| BLUEPRINT §5 sections | Strikethroughs on Cut items | clean |
| BLUEPRINT §7 layers | Two active layers | clean |
| BLUEPRINT §"End of blueprint" | "Session 1 reads ... before any code" | **YES (m2)** — past-tense reality |
| NEXT.md staleness flag | §G of SESSION_01_RECON still wrong | **active flag — still valid (B3)** |
| ORCHESTRATOR.md §7 | NEXT.md is checkpoint.md | **YES (M5)** — partly aspirational |
| ORCHESTRATOR.md §8 | `/hanna-dispatch-next` is one workflow | clean |
| ORCHESTRATOR.md §9 | Hard constraints inherited | clean |
| DECISIONS.md D001–D009 | All cross-anchored cleanly | clean (m6 verified) |
| HANNA_DESIGN_ADOPTION.md | Live session prompt | **YES (M1)** — preserved past execution |
| SESSION_01_RECON.md §G | Rules don't exist in Harlo | **YES (B3)** — contradicts RULES.md |
| CONVENTIONS.md §1 table | Struck rows preserved with annotations | clean |
| PRODUCER_LENS.md | Forward-looking, no factual claims to falsify | clean |
| ROADMAP.md §5 | Lane status table | clean (m5 cosmetic) |
| UI_UX_MAP.md §7 | Layer 2 in diagram as parked | (M7) noise but documented |
| SPIKE_HARLO_EDGE_2026-05-20.md | D001 reconciled | clean |
| REVIEW_2026-05-22.md | Model-id in reviewer line | **YES (M3)** |

---

## Reading order — can a new reader navigate?

**Tested path: new contributor reading from cold.** Start at README.md. Reader is told:
- "Architectural spec is HANNA_BLUEPRINT.md" — pointer good.
- "Rules in RULES.md" — pointer good but lands on B1 (RULES.md is internally contradictory on Rule 34's layer count).
- "Day-to-day conventions in docs/CONVENTIONS.md" — pointer good.
- "Status governed by docs/ROADMAP.md §5" — pointer good.
- "Live session-state checkpoint at NEXT.md" — pointer good.

**Reader is NOT told:**
- ORCHESTRATOR.md exists (B2). Hits this only via CLAUDE.md (which a non-Claude reader has no reason to read).
- DECISIONS.md exists (B2). The cross-link to D008 is the first time this file is named — embedded in a Build-Lanes paragraph 200 lines into the README.
- The state/ durable layer exists (B2).
- HANNA_DESIGN_ADOPTION.md exists (B2) — and if they find it, they encounter M1's session-prompt confusion.

**Tested path: AI agent reading per ORCHESTRATOR.md.** Better than the human path because CLAUDE.md points at ORCHESTRATOR.md and ORCHESTRATOR.md §7 points at all the canonical surfaces. The agent path doesn't traverse README's stale repository layout, so B2's impact is humans-only.

**Conclusion:** the human reading path has a navigation gap at README; the agent reading path is clean modulo the contradictions in canonical files. The repo's documented north star is "each file has one job" (CLAUDE.md line 84) — currently README's layout block is failing that test, and HANNA_DESIGN_ADOPTION.md has two jobs (historical artifact + live-looking instructions).

---

## Proposed belief deltas

Per ORCHESTRATOR.md §2: critic[evaluate] writes belief deltas; critic[red_team] *proposes* but does not write. These are for orchestrator validation.

```
DELTA c006_proposal
CLAIM:        RULES.md §34 body still describes a 3-layer lockout including the Cut HdProducer delegate, directly contradicting the L1 propagation note at RULES.md:15
CONFIDENCE:   0.95
EVIDENCE:     RULES.md:15 (post-L1) vs. RULES.md:181-187 (pre-D008.1); cross-check HANNA_BLUEPRINT.md:230 ratified text
ROUTING:      candidate for high-leverage open_question or direct lane (cheap fix; high-blast risk if a future contributor cites RULES.md §34 as canonical)
```

```
DELTA c007_proposal
CLAIM:        README.md is the most navigation-load-bearing doc in the repo and is currently missing pointers to 9+ files that landed after its last full revision
CONFIDENCE:   0.95
EVIDENCE:     README.md:155-172 (repository layout); ls /home/user/Hanna/; ls /home/user/Hanna/docs/; git log entries for ORCHESTRATOR.md (c65b6ae), DECISIONS.md, ROADMAP.md, REVIEW_2026-05-22.md, PRODUCER_LENS.md, UI_UX_MAP.md, SPIKE_HARLO_EDGE_2026-05-20.md, state/, scripts/, src/, tests/
ROUTING:      candidate for high-leverage open_question
```

```
DELTA c008_proposal
CLAIM:        Doc-drift in this repo accumulates at lane velocity, not session velocity — 2e68877 + 8e83296 reconciliation passes caught contradictions visible to CodeRabbit's grep but missed RULES.md §34's layer-count contradiction, BLUEPRINT's "v0.1.0-draft" version label, and HANNA_DESIGN_ADOPTION.md's session-prompt-as-doc status
CONFIDENCE:   0.85
EVIDENCE:     NEXT.md "Lessons from this session" already names this pattern; this audit adds three new instances the prior diagnostic surveys missed
ROUTING:      candidate confirmation of NEXT.md's "Doc-drift accumulates faster than code-drift" insight; arguably already exists at lower confidence as a c003-adjacent belief
```

```
DELTA c009_proposal
CLAIM:        The ORCHESTRATOR.md §7 Hanna State Adapter is internally consistent and the D-entry anchors in DECISIONS.md are clean for GitHub slug resolution; the structural drift is not in the framework adoption but in the legacy docs (README, RULES, SESSION_01_RECON) the framework points at
CONFIDENCE:   0.85
EVIDENCE:     ORCHESTRATOR.md §7 read in full; spot-check on D001/D002/D006/D008 anchors confirms heading slug match; B1/B2/B3 are all in pre-D009 files, not D009-authored files
ROUTING:      reduces risk perception around D009 adoption; the orchestrator framework is healthy
```

---

## Open questions surfaced

```
QUESTION_ID:  q004_proposal
QUESTION:     RULES.md §34 body says "3 layers"; line 15 applicability note says layer 2 Cut. Which surface is canonical for the next agent that reads Rule 34 — the body or the applicability note? (Resolution shape: either patch §34's body to match line 15, or invert and treat line 15 as a status overlay.)
LEVERAGE:     high
RATIONALE:    RULES.md is the compliance gate's source of truth. A canonical-vs-canonical contradiction in the rules file directly threatens rule-application integrity.
```

```
QUESTION_ID:  q005_proposal
QUESTION:     Is HANNA_DESIGN_ADOPTION.md a historical artifact (stamp it as such), a living spec (extract its non-prompt content into BLUEPRINT/web docs), or a duplicate (delete; the work landed)? Currently it reads as live instructions to a non-existent agent.
LEVERAGE:     medium
RATIONALE:    A 7KB file at repo root has front-door visibility but no clear consumer. Three resolutions are all cheap.
```

```
QUESTION_ID:  q006_proposal
QUESTION:     Does the §9 "no model-id in any committed artifact" rule bind prose docs or only commit messages and code? REVIEW_2026-05-22.md:4 carries `Claude Opus 4.7, 1M context` as a docs string; CLAUDE.md:46 says the form is "disallowed" but its scope is the Co-Authored-By trailer slot. Resolution either tightens the rule (and triggers a sweep) or loosens it (and pins the prose-doc carve-out explicitly).
LEVERAGE:     medium
RATIONALE:    Without resolution, the rule is ambiguous and quietly violated in committed prose.
```

---

## Noticed (out-of-scope)

Items observed during read that are out-of-scope for scout-docs but logged here per critic protocol:

- `bin/hanna-brief.command:34` still hardcodes `open "$BRIEF_PATH"` against the static HTML mockup, despite D006 ratifying Calendar as the v1 channel and L4b being the named next lane (`NEXT.md:75`). ROADMAP §4 L4b spec includes the launcher swap as a lane completion criterion. **Out-of-scope for docs; in-scope for scout-code-quality or scout-ops.**
- `web/templates/morning_brief.html` is referenced from BLUEPRINT/UI_UX_MAP/PRODUCER_LENS as a Phase-1 design reference — it exists. `web/README.md` is referenced from HANNA_DESIGN_ADOPTION.md Step 3 as the design system doc — it does NOT exist. The design system content from Step 3's embedded markdown is preserved in HANNA_DESIGN_ADOPTION.md itself and partially mirrored in UI_UX_MAP.md §1.1, but a reader looking for `web/README.md` per HANNA_DESIGN_ADOPTION.md's promise hits a 404. **Out-of-scope for the prose audit; in-scope for whichever scout owns asset-presence.**
- `state/plan.md` is a live GOAL file (this audit's parent), but ORCHESTRATOR.md §7's adapter table doesn't mention `plan.md` as a state/ entry — only `beliefs.md` and `open_questions.md`. The §7 last sentence even says state/ contains "exactly" those two until a live GOAL writes ephemeral artifacts. `plan.md` is currently sitting there. **Logged for the scout-architecture lens; tracked in M5 here.**

---

## End of findings
