# Hanna — Substrate Decisions

This document is the ratified-decisions log for Hanna. Substrate-level decisions — changes to [`RULES.md`](../RULES.md), [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) architecture, or any cross-cutting interpretation — are recorded here before the corresponding code or doc change merges.

Established by [`RULES.md`](../RULES.md) (end of file): *"Changes to this document require a substrate-level decision and must be ratified in `docs/DECISIONS.md` before merge."*

Established by [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §14 Doc discipline: *"Open decisions track in `docs/DECISIONS.md` with status (open / defaulted / resolved)."*

---

## Format

Each decision is a numbered entry. Numbering is monotonic across the project (D001, D002, …) and never reused after a decision is reversed — a reversal is itself a new decision that references the prior number.

```markdown
### D### — Title

**Status:** open | defaulted | resolved | reversed
**Date:** YYYY-MM-DD
**Ratified by:** Joe (Joseph Ibrahim)
**Scope:** which rule / blueprint section / module this affects

**Decision.** Single-paragraph statement of what was decided.

**Reasoning.** Why this reading over the alternatives.

**Implications.** What this enables, what this forbids, what changes in code or rules.

**Related.** Pointers to spike docs, blueprint sections, audit findings, prior decisions.
```

**Status semantics.**

- **open** — surfaced as a question, no decision yet. Defaults (if any) named in the entry.
- **defaulted** — running on the default named in the entry, no explicit ratification. Reversible without ceremony.
- **resolved** — explicit ratification by Joe. Reversal requires a new D### entry.
- **reversed** — superseded by a later decision. The original entry stays in-place as historical record.

---

## Decisions

### D001 — Rule 35 permissive reading: `exchange_index` advance is not a write

**Status:** resolved
**Date:** 2026-05-20
**Ratified by:** Joe (Joseph Ibrahim)
**Scope:** [`RULES.md`](../RULES.md) Rule 35 ("Cross-substrate writes prohibited") interpretation; [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §9 read edges; `src/harlo_bridge.py` implementation surface.

**Decision.** Rule 35's prohibition on Hanna writing to Harlo is interpreted **permissively**. The rule forbids:

1. Authoring content into Harlo's trace store.
2. Mutating Harlo's saved cognitive state.
3. Reconfiguring Harlo's engine.

The rule does **not** forbid causing Harlo's `exchange_index` counter to advance, which is unavoidable telemetry on every MCP tool call. The architecturally meaningful "write" is captured by four specific Harlo tools, which Hanna's bridge **must never call**: `store`, `stage_reload`, `resolve_verifications`, `trigger_cognitive_recalibration`.

The Harlo `coach` tool — which appends traces to the recent-traces window and saves the exchange as part of its `author → DAG → route → delegate → observe → predict → save` pipeline — is **permitted** under this reading. The framing: a Hanna call to `coach` is Hanna *participating* in a Harlo exchange (observation of Hanna's existence in Harlo's session), not Hanna *injecting content* into Harlo's cognitive model. Use of `coach` from Hanna is rate-limited to **at most one call per brief composition**, called only when a fresh prediction or a fresh routing decision is genuinely needed.

**Reasoning.** The 2026-05-20 spike ([`SPIKE_HARLO_EDGE_2026-05-20.md`](SPIKE_HARLO_EDGE_2026-05-20.md)) established that every read-side Harlo MCP tool — `status`, `coach`, `recall`, `patterns`, `query_past_experience` — advances `exchange_index`. There is no zero-side-effect read. A strict reading of Rule 35 ("no state change in Harlo whatsoever") therefore makes the entire Harlo bridge impossible to implement, which contradicts [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §9 and the architectural posture of Hanna reading Harlo for cognitive-state truth. The permissive reading is the only interpretation that lets the substrate-pairing architecture exist as designed.

The choice of *which* writes constitute architectural violations was guided by reversibility and observability: the four forbidden tools mutate persistent state that Joe would notice in a Harlo session (new traces in his memory, reloaded stages, completed verifications, cognitive recalibration). The `exchange_index` counter is telemetry that exists precisely to track that exchanges happened — incrementing it is, by design, not a state change in the cognitive model.

The `coach` edge case was the closest call. `coach` does author content (a trace per exchange) — but the trace records *that an exchange occurred*, not *what Hanna believes about Joe*. Framing it as observation rather than injection preserves the spirit of Rule 35 while keeping the prediction surface accessible.

**Implications.**

- `src/harlo_bridge.py` exposes methods that wrap exactly these Harlo tools: `status`, `coach`, `recall`, `query_past_experience`, `patterns`. The bridge **never** exposes methods that wrap `store`, `stage_reload`, `resolve_verifications`, `trigger_cognitive_recalibration`.
- `drive_coaching_exchange()` (per the reconciled §9 contract) is **unblocked**. Rate-limit: ≤1 call per Hanna brief composition. The rate limit lives in the bridge, not in calling code.
- The Rule 35 compliance grep in [`RULES.md`](../RULES.md) (`grep -rE "harlo\.(write|store|author|mutate)" src/` MUST return 0) stays as the CI gate. None of the permitted methods match those verbs; the gate continues to catch the actual violation surface.
- The bridge code must be *visibly* compliant — each public method names the Harlo tool it wraps so a reader can verify Rule 35 at a glance. This is a code-organization requirement that falls out of the decision; reviewable at the diff level.
- Audit §12.5 (Harlo bridge contract reconciliation, [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md)) is fully resolved with this entry.
- The smaller day-zero PoC ([`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §11.1) is now unblocked end-to-end.

**Related.**

- [`SPIKE_HARLO_EDGE_2026-05-20.md`](SPIKE_HARLO_EDGE_2026-05-20.md) §7 (strict-vs-permissive analysis), §8 (audit §12.5 resolution).
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §9 (read edges, reconciled contract table), §12.5 (audit-added open decision, now resolved by this entry).
- [`RULES.md`](../RULES.md) Rule 35 (cross-substrate writes prohibited).

---

### D002 — Mixture-of-Experts agent-team execution model for substrate-level work

**Status:** resolved
**Date:** 2026-05-20
**Ratified by:** Joe (Joseph Ibrahim)
**Scope:** Build execution methodology across all substrate-level work in this repo (bridges, computations, MCP tools, stage authoring, day-zero deliverables, cross-cutting refactors). Applies to every Code session unless explicitly overridden in the session prompt.

**Decision.** Substrate-level work on Hanna is executed via parallelized Claude subagents in role-specialized "expert" configurations, not as single-thread implementation. The main Code thread acts as **router and integrator** — it receives the task, decomposes it into expert slices, dispatches experts (in parallel where dependencies allow), integrates outputs, runs a final compliance pass via a dedicated reviewer expert, applies fixes, and commits.

**Expert roles (the MoE taxonomy):**

| Role | Specialty | Triggers when… |
|---|---|---|
| **Architect** | File structure, interfaces, contract design, integration shape | Default; held by the main thread unless explicitly dispatched |
| **Bridge engineer** | MCP-stdio surfaces, Harlo / Octavius edges, Rule 35 boundary, the v9 envelope | `src/harlo_bridge.py`, `src/octavius_bridge.py`, or any code that opens a subprocess MCP client |
| **Computation engineer** | Pure functions, state machines, enum returns, Rule 36 enforcement | `src/computations/*.py` |
| **Stage engineer** | Persistence layer (SQLite per §4 audit / USD per §4 pre-audit), schema, prim authoring | `src/store.py`, `data/`, any persistence code |
| **Brief composer** | Markdown composition, editorial voice, "surface don't decide" framing (Rule 36) | Any code that generates user-facing brief / capsule text |
| **MCP surface engineer** | FastMCP server, tool registration, lockout gating, structured-JSON returns | `src/mcp_server.py`, `hanna_*` tool implementations |
| **Compliance reviewer** | Audits against RULES.md (especially 18, 34, 35, 36, 37), DECISIONS.md, BLUEPRINT.md contracts, compliance greps | **Mandatory final pass on every MoE execution.** Never skipped. |

**When MoE applies:**

- Substrate-level work that touches ≥2 expert roles
- Day-zero deliverables and PoCs
- Cross-cutting refactors (changes touching multiple lanes per BLUEPRINT §10)
- Any work that lands code in `src/`, `scripts/`, or `python/hanna/`

**When MoE does NOT apply:**

- Trivial fixes (single-line edits, doc typos, lint cleanups)
- Exploratory spikes (single agent or main thread; spike outputs are docs, not code)
- Personal-context updates (memory writes, `NEXT.md`, `CLAUDE.md`, `docs/CONVENTIONS.md`)
- Substrate decisions themselves (entries to this file are author-by-main-thread, ratified by Joe directly)

**Coordination protocol:**

1. **Decompose.** Main thread reads the task, identifies which expert roles are needed, defines each slice as a self-contained brief that the expert can read cold (the expert does not see the parent conversation).
2. **Dispatch.** Builder experts run in **parallel** where dependencies allow. Where one expert's output is consumed by another (e.g. PoC consumes Bridge), the downstream expert codes against the *spec*, not against the upstream expert's actual artifact — keeps the team parallel even with logical ordering.
3. **Integrate.** Builder experts may write files directly (saves a re-typing round-trip) OR return code as their final message for the main thread to Write. Main thread chooses per task — direct-write for clean greenfield, return-as-message when integration logic is needed.
4. **Review.** Compliance reviewer runs **last and alone** — never in parallel with builders. Reads the integrated artifacts. Returns PASS items, FAIL items, and RECOMMENDED-CHANGES. The reviewer's job is to catch what no builder could see (cross-file consistency, rule compliance, dead code, contract drift).
5. **Apply fixes.** Main thread applies the reviewer's RECOMMENDED-CHANGES via Edit. If the reviewer found a structural FAIL (not a fix-in-place issue), the main thread re-dispatches the affected expert.
6. **Commit.** Single commit per MoE execution, with a body that names the dispatched experts and links to the reviewer's audit. Use the canonical Claude Code trailer.

**Hard constraints inherited by every expert:**

- **Rule 35** (per D001): experts must never expose or invoke methods that call `store`, `stage_reload`, `resolve_verifications`, `trigger_cognitive_recalibration` on Harlo's MCP surface.
- **Rule 37**: experts must not raise patent topics under any framing.
- **Rule 34**: experts implementing MCP tools must include the family-first lockout gate.
- **Rule 36**: experts producing user-facing output must frame as surfaced observation, not directive.
- **Canonical commit trailer**: every commit produced by the MoE flow uses the canonical Claude Code trailer (`Co-Authored-By: Claude <noreply@anthropic.com>`).

**Reasoning.** The 2026-05-20 first-principles audit established that Hanna's substrate decisions involve genuinely different expertise lenses — Harlo-edge contract reading, pure-function discipline, persistence-layer trade-offs, editorial composition voice, compliance against an inviolable rule set. A single-thread implementation collapses these into one cognitive context and loses the specialization gain. Parallelized experts working from self-contained briefs produce sharper, more honest output (corroborated by the audit itself — three independent agents reading cold reached a stronger conclusion than a single synthesizer would have). MoE also matches the architectural posture of Hanna (a producer that surfaces parallel work streams) — the build methodology mirrors the build product.

The router-integrator pattern keeps human-meaningful control in the main thread: experts produce, the router decides what lands. Reviewer-last ensures no expert sees its own work uncritically; cross-file consistency comes from a dedicated set of eyes.

**Implications.**

- Code sessions involving substrate-level work spawn ≥2 builder experts + 1 reviewer expert by default.
- The main thread does not write production code in `src/` directly; it integrates expert outputs.
- The reviewer pass is non-skippable and must run after every MoE execution. A green reviewer pass is the gate for commit.
- Builder experts' prompts must be self-contained — full context for cold reads, no reliance on parent-conversation state.
- The MoE flow is logged in the resulting commit body (which experts dispatched, what reviewer flagged, what was fixed).
- This decision is itself executable: D002 governs how D003+ get implemented when they touch code.

**Related.**

- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §10 build lanes (the MoE roles parallel the lane taxonomy), §13 inherited rules (the constraints every expert carries).
- [`RULES.md`](../RULES.md) Rules 18, 34, 35, 36, 37 (compliance reviewer's audit surface).
- D001 (Rule 35 permissive reading — inherited as a hard constraint by every Bridge expert dispatch).
- The 2026-05-20 first-principles audit (three independent agents) is the proof-of-concept demonstration of the pattern.

---

### D003 — Apache header convention: clones inherit absence

**Status:** resolved
**Date:** 2026-05-20
**Ratified by:** Joe (Joseph Ibrahim)
**Scope:** [`NOTICE`](../NOTICE) (root); per-file header convention for `src/**`, `tests/**`, `python/hanna/**`, `scripts/**`; cloning protocol for files descending from Harlo.

**Decision.** The NOTICE clause *"each cloned file retains its original Apache 2.0 header"* is read **literally**: cloned files inherit whatever per-file header the Harlo original carries, including its absence. A survey of Harlo's full source tree (`src/*.py`, `src/computations/*.py`, `python/harlo/*.py`) shows **zero** files with a per-file Apache 2.0 header — every Harlo `.py` opens with a `"""docstring"""` or a `# Sprint N:` one-liner. The Apache 2.0 grant for Harlo applies via root `LICENSE`. Hanna inherits that posture.

Concretely:

1. **Cloned files** carry no Apache header — only the module docstring (preserved from Harlo) plus an attribution trailer comment immediately above the docstring:

   ```python
   # Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
   """Pure function: compute producer phase transitions."""
   ```

2. **Fresh Hanna files** (no Harlo ancestor) carry no header — just the module docstring.
3. **Licensing** for all Hanna source applies via root `LICENSE` (Apache 2.0). Apache §4 requires `LICENSE` + `NOTICE` accompany the work; per-file boilerplate is recommended in the license appendix but is not required for the grant to attach. Harlo runs this pattern; Hanna inherits it.

The four files that landed under the prior misreading — [`src/harlo_bridge.py`](../src/harlo_bridge.py), [`src/schemas.py`](../src/schemas.py), [`src/computations/compute_producer_phase.py`](../src/computations/compute_producer_phase.py), [`tests/computations/test_compute_producer_phase.py`](../tests/computations/test_compute_producer_phase.py) — are amended in the same commit to drop the 14-line header block. Attribution trailer preserved on the three cloned files; the test file (a fresh Hanna author) keeps only its docstring.

[`NOTICE`](../NOTICE) gains one clarifying paragraph appended to the existing "retains" block, naming the literal reading and pointing at this decision.

**Reasoning.** Three findings forced the reconciliation:

1. **Empirical mismatch.** NOTICE's *"retains its original Apache 2.0 header"* implies Harlo originals carry headers. Survey: zero do. The misread was mine in Session 02 — I added headers to Hanna files thinking I was preserving an original; there was no original to preserve.
2. **Legal sufficiency.** Apache 2.0 §4 requires `LICENSE` + `NOTICE` accompany the work (both present at Hanna root). Per-file boilerplate is recommended-not-required. Harlo (also Apache 2.0) runs the no-headers pattern without issue.
3. **Operational cost.** The full Apache boilerplate is 14 lines per file. In Session 02 it consumed 44 of the 130-line scaffold budget and forced docstring trims at the cap. The same tax recurs on every cloned-pair session ahead (`compute_brief_priority`, `compute_forcing_function`, `compute_formation_readiness`, `delegate_producer`, `octavius_bridge`). Removing headers reclaims budget for content.

Alternative considered: keep per-file headers and raise per-session line caps. Rejected — adds a two-layer rule (count lines, but exclude headers) and worsens diff hygiene (clones lead with 14 lines of boilerplate before the actual cloned content).

This reconciliation follows the same pattern as D001 (Rule 35): an existing artifact (`NOTICE` / `RULES.md` Rule 35) is read literally rather than expansively, and the literal reading turns out to match the substrate's actual needs.

**Implications.**

- 4 files amended in the ratifying commit (drop Apache block, preserve docstring; preserve attribution trailer on the 3 clones).
- [`NOTICE`](../NOTICE) gains a clarifying paragraph in the same commit.
- Session 02 net line count drops from 130 → ~86, well under target.
- Future clone sessions plan line budgets against content, not boilerplate.
- D002's compliance reviewer expert checks the attribution trailer on cloned files (within first 20 lines) as part of its rule-compliance pass — adds one line to the reviewer's checklist.
- Fresh Hanna files (no Harlo ancestor) explicitly require no header. The attribution trailer is the *only* per-file marker the substrate requires, and only on clones.

**Related.**

- D001 — same "literal reading of an existing artifact" reconciliation pattern.
- D002 — MoE compliance reviewer surface (gains attribution-trailer check).
- [`NOTICE`](../NOTICE) (root) — clarifying paragraph in the same commit.
- Session 02 scaffold commit `e7ac833` on `session-02-scaffold` — surfaced this via the 130-line budget overrun.
- Harlo's [`LICENSE`](https://github.com/JosephOIbrahim/Harlo/blob/main/LICENSE) and [`NOTICE`](https://github.com/JosephOIbrahim/Harlo/blob/main/NOTICE) files — the inherited pattern.

---

## End of decisions log

Next decision number: **D004**.
