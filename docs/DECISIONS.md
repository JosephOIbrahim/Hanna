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

### D004 — Attribution-trailer hygiene at reviewer and conventions layers

**Status:** resolved
**Date:** 2026-05-20
**Ratified by:** Joe (Joseph Ibrahim)
**Scope:** D002 compliance-reviewer checklist; [`docs/CONVENTIONS.md`](CONVENTIONS.md) §-note on fresh-seed vs. clone state.

**Decision.** D003 made the attribution trailer the only required per-file marker for cloned files. D004 installs the operational guardrails so the rule actually holds across future sessions.

**Clause A — Reviewer checklist amendment.** The D002 compliance reviewer expert's checklist gains one mandatory item:

> Every file in `src/**`, `python/hanna/**`, or `scripts/**` that descends from a Harlo source must carry the attribution trailer `# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.` within its first 20 lines. Files with no Harlo ancestor must not carry the trailer. The reviewer FAILs the pass if either condition is violated.

The 20-line bound is generous on purpose — it tolerates a multi-line provenance comment block before the trailer without forcing strict line-1 placement.

**Clause B — CONVENTIONS pointer.** [`docs/CONVENTIONS.md`](CONVENTIONS.md) gains §2 ("Fresh-seed vs. clone state") pinning the rule for files that are *partially* clones — files born as fresh Hanna seeds today but expected to absorb Harlo content in a future session. [`src/schemas.py`](../src/schemas.py) is the canonical case (Session 02 minimal seed; later sessions clone Harlo schemas in). The §-note resolves the ambiguity: **the trailer is added at clone-time, not seed-time** — the session that first lands cloned Harlo content into the file adds the trailer in the same commit.

**Reasoning.** D003 establishes the marker rule; D004 makes it auditable and forward-compatible. Without Clause A, the reviewer has no enforcement surface and discipline drifts as the codebase grows. Without Clause B, the boundary case (fresh today, clone-bearing tomorrow) has no canonical answer and each session has to relitigate. Both clauses are small and orthogonal — bundling them in one decision keeps the D-series readable and ensures the operational layers (reviewer prompt + conventions doc) ship together.

The "20 lines" bound was chosen empirically: D003's amended files place the trailer at line 1 or 15. 20 accommodates a future clone that preserves a multi-line top-of-file Harlo comment before adding the trailer. Tighter bounds force trailer-placement battles for no audit benefit.

**Implications.**

- D002's reviewer-expert prompt template gains the Clause A check. Next MoE dispatch picks it up automatically.
- [`docs/CONVENTIONS.md`](CONVENTIONS.md) gains §2 from Clause B in the same commit.
- [`src/schemas.py`](../src/schemas.py) stays as-is (no trailer) until a future session lands cloned Harlo schema content. Trailer added in that same commit per Clause B.
- Reviewer FAIL gate is non-skippable per D002 §"Review."
- No code changes for existing files — Session 02's D003 amendments already satisfy the rule.

**Related.**

- D002 — reviewer-checklist surface this amendment lives on.
- D003 — established the trailer rule this decision operationalizes.
- [`docs/CONVENTIONS.md`](CONVENTIONS.md) — destination of the Clause B §-note.
- `NEXT.md` will flag this for the session that next touches [`src/schemas.py`](../src/schemas.py).

---

### D005 — Harlo bridge hardening (rate-limit + read timeout + stderr drain)

**Status:** resolved
**Date:** 2026-05-22
**Ratified by:** Joe (Joseph Ibrahim) — whole-batch ratification alongside D007 and D008
**Scope:** [`src/harlo_bridge.py`](../src/harlo_bridge.py); [D001](#d001--rule-35-permissive-reading-exchange_index-advance-is-not-a-write) rate-limit ownership implication; [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §9 (Harlo read edges); [`NEXT.md`](../NEXT.md) §"D005 — RESOLVED" section.

**Decision.** Three sub-decisions on bridge hardening are bundled here because they share a substrate question (*how does the bridge handle slow, hung, or noisy Harlo subprocesses*) and the same review surface. Each was drafted with a proposed default; the three defaults are now **ratified whole-batch** as the resolution. The implementation lane (MoE Dispatch #2: Bridge Engineer + Compliance Reviewer per D002) is unblocked.

**Sub-decision D005.1 — Coach rate-limit semantic.** Current implementation: per-instance via the `_coach_driven` boolean (`src/harlo_bridge.py:43, 85–89`). [D001](#d001--rule-35-permissive-reading-exchange_index-advance-is-not-a-write) mandate: "≤1 call **per brief composition**" with the rate limit living in the bridge, not in calling code. The boolean enforces "≤1 per `HarloBridge` instance, ever" — wrong shape for any caller that composes more than one brief from a single bridge instance (e.g., a future Friday harvest + brief, or any long-lived MCP server). Three candidate readings:
- **(a)** `begin_composition(composition_id: str)` / `end_composition()` scope methods on the bridge — composition-id-keyed, resets the per-composition gate on each `begin`. Matches D001's "rate limit lives in the bridge" implication while preserving the per-composition semantic across long-lived callers.
- **(b)** Token-bucket rate limit (TTL-based reset, e.g. 5-min cooldown) — looser; survives long-lived processes without explicit scoping but blurs the "per composition" contract into a wall-clock heuristic.
- **(c)** Document per-instance as the contract; require callers to instantiate one bridge per composition — punishes long-lived callers but is the smallest code change.

**Resolution: (a) — `begin_composition` / `end_composition` scope methods.** Preserves D001's stated semantic; explicit; testable.

**Sub-decision D005.2 — `_read_frame` timeout liveness.** Current implementation: `timeout` parameter plumbed through `_rpc → _read_frame` (`src/harlo_bridge.py:143, 149, 176`) but never consulted; the body uses blocking `proc.stdout.readline()` and `proc.stdout.read(content_length)`. A hung Harlo subprocess freezes the bridge indefinitely. Surfaced in `NEXT.md:50`. Three candidate readings:
- **(a)** `selectors.DefaultSelector` with `register(proc.stdout, EVENT_READ)` and `select(timeout=…)` per frame. Stdlib only.
- **(b)** Background reader thread + `queue.Queue.get(timeout=…)` per frame. Decouples I/O from the RPC loop but adds thread-lifecycle to the bridge.
- **(c)** Replace MCP-stdio framing with a structured-RPC library that has built-in timeouts. Largest change; adds dependency surface.

**Resolution: (a) — `selectors.DefaultSelector` with `select(timeout=…)` per frame.** Lowest dependency surface; matches the bridge's existing single-threaded posture.

**Sub-decision D005.3 — stderr drain.** Current implementation: `subprocess.Popen(..., stderr=subprocess.PIPE, ...)` (`src/harlo_bridge.py:116`); no reader thread or call. Once Harlo writes ~64KB to stderr (OS pipe-buffer default), the subprocess blocks on the next stderr write — deadlocking the bridge. Surfaced in `NEXT.md:51`. Two candidate readings:
- **(a)** Background drainer thread reading `proc.stderr` to a bounded ring buffer (e.g., last 64 lines) accessible via `bridge.last_stderr()` for diagnostics. Preserves debuggability.
- **(b)** Switch to `stderr=subprocess.DEVNULL` — lose Harlo's stderr diagnostics, gain simplicity.

**Resolution: (a) — background drainer thread + bounded ring buffer.** Preserves the diagnostic signal without the deadlock; the ring buffer bound keeps memory deterministic.

**Reasoning.** All three sub-decisions surfaced during Session 02 (D005.2 and D005.3 via `NEXT.md:46–53`) or via the senior review that triggered this draft (D005.1). They share the same architectural surface (`src/harlo_bridge.py`), the same expert assignment under D002 (Bridge Engineer), and the same caller (today: `scripts/first_hanna_brief.py`; future: every MCP tool). Bundling them avoids three separate ratification cycles for what is materially one "harden the bridge" decision. Each sub-decision carries its own default so Joe can ratify in whole or per-item.

The choice of `(a)` defaults across all three is guided by the same principle: prefer the smallest stdlib-only change that preserves the contract's stated semantic. None of the `(a)` options introduce new dependencies or change the bridge's caller-facing API surface beyond adding new methods (D005.1 `begin_composition`/`end_composition`, D005.3 `last_stderr`).

**Implications.**
- **Ratified — implementation lane is unblocked.** MoE Dispatch #2 (Bridge Engineer + Compliance Reviewer per D002) lands all three. Estimated ~50–80 lines.
- Until MoE Dispatch #2 lands, the status quo holds: rate limit is per-instance (caller workaround: instantiate one `HarloBridge` per brief composition, which `scripts/first_hanna_brief.py` accidentally already does via the `with`-block landed in commit `3cdd516`); `_read_frame` blocks indefinitely on hang; stderr deadlocks at ~64KB. Calling code may proceed defensively in the gap: short-lived bridge instances, generous Harlo subprocess kill timeouts via process supervisors, etc.
- The bridge's public method docstrings should name the relevant sub-decision (D005.1) once the rate-limit shape lands — per [D001](#d001--rule-35-permissive-reading-exchange_index-advance-is-not-a-write) Implications bullet 4, Rule 35 compliance is meant to be reviewable at the diff level.
- The `_read_frame` timeout-parameter plumbing already exists at `src/harlo_bridge.py:143, 149, 176` — D005.2 only needs to wire the body to the parameter, not introduce the parameter.
- Tests for the three items will live under the eventual `tests/test_harlo_bridge.py` (catalogued as can-land-anytime per [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) §3.7).

**Related.**
- [D001](#d001--rule-35-permissive-reading-exchange_index-advance-is-not-a-write) — establishes the rate-limit ownership requirement ("the rate limit lives in the bridge, not in calling code").
- [D002](#d002--mixture-of-experts-agent-team-execution-model-for-substrate-level-work) — names Bridge Engineer as the dispatcher for the eventual implementation.
- [`NEXT.md`](../NEXT.md) §"Parked for D005" — the two pre-existing parked items (D005.2 and D005.3).
- Senior review (2026-05-22) — surfaced D005.1.
- `HarloBridge._coach_driven` (`src/harlo_bridge.py:43, 85–89`) — current implementation of D005.1's status quo.
- `HarloBridge._read_frame` (`src/harlo_bridge.py:176–201`) — current implementation of D005.2's status quo.
- `HarloBridge` subprocess construction (`src/harlo_bridge.py:112–127`) — current implementation of D005.3's status quo.

---

### D006 — Delivery channel: dedicated "Hanna" iCloud calendar with 0-minute anchor events

**Status:** resolved
**Date:** 2026-05-22
**Ratified by:** Joe (Joseph Ibrahim)
**Scope:** [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §12.6 (delivery channel for v1 briefs); §5 "Producer UI Surface" line 213 (channel-agnostic posture); [`README.md`](../README.md):7 (the "always-on" front-door claim); [`bin/hanna-brief.command`](../bin/hanna-brief.command) Phase-2 wiring; future `src/channels/calendar.py` module; the `mcp_tools` lane's tool-return shape; the brief composer voice calibration.

**Decision.** Hanna's v1 brief delivery channel is **Calendar events on a dedicated "Hanna" iCloud calendar**. Every brief (morning, midday, evening, weekly_monday, weekly_friday, monthly) is authored as a 0-minute anchor event at the rhythm time, with the brief body in the event notes (markdown). The calendar is a dedicated iCloud calendar named **`Hanna`** that Joe can show/hide independently of his work calendar.

This decision **skips the 3-day behavioral observation test proposed in the §12.6 default** (the audit's recommendation) in favor of first-principles reasoning. The reasoning is recorded below; the test option is preserved as a reversal-trigger if 30 days of behavioral data shows the choice was wrong (D006-reversal would be a new D-entry, not an amendment).

**Reasoning.** The producer's job per [Rule 36](../RULES.md) / [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §1 is to *surface*, not to decide or push. Three constraints rank the candidate channels (iMessage via Shortcuts, macOS notification via `osascript`, Calendar event, browser — the original Phase-1 mockup target):

1. **Non-interruption.** A producer that pushes contradicts "surface, don't decide." iMessage and macOS notification both push; both fail this constraint.
2. **Cross-device.** Joe lives in Houdini and on iPhone (the [Audit Log](../HANNA_BLUEPRINT.md) finding #4 framing). The channel must follow Joe; macOS notification is Mac-only and fails.
3. **Persistence.** Joe may re-read the morning brief at noon. macOS notification is transient (swipe = lost); browser requires Joe to remember a URL.

Calendar event passes all three: iCloud syncs Mac ↔ iPhone ↔ Watch; events are visible in day-view without push; events persist for re-read. The dedicated `Hanna` calendar isolates Hanna's output from Joe's working calendar — show it when wanted, hide it without disturbance.

Posture fit is the cleanest argument: a Calendar event reads as **"context the day carries."** Joe opening his calendar in the morning finds Hanna's note sitting in the day-view; this matches the surface-don't-decide posture more cleanly than any push-based channel.

The audit's recommended 3-day test was the disciplined path. Skipping it is conscious; the first-principles reasoning above is the substitute. If behavioral data over the first 30 days of Calendar-channel operation shows Joe ignoring, hiding, or muting the calendar, this D006 can reverse via a new D-entry that opens the test originally proposed.

**Implications.**

- **Implementation lane.** A future session lands `src/channels/calendar.py` (the channel adapter). Initial implementation via `osascript Calendar` on macOS; CalDAV / EventKit cross-platform considered later. The module exposes `publish(brief: BriefPayload) -> CalendarEventId` and `archive(event_id: CalendarEventId) -> None`. MoE-eligible (Bridge Engineer + Brief Composer for posture calibration + Compliance Reviewer).
- **`bin/hanna-brief.command`** Phase-2 swap target is no longer "open the static HTML mockup in a browser." It becomes either (a) trigger a calendar publish if the script is fired manually, or (b) be deleted entirely once the MCP-tool surface authors calendar events automatically. The launcher's Phase-1 mockup-opening behavior stays as design *reference*; the destination is the Calendar.
- **`mcp_tools` lane** can now size tool returns to a calendar-event posture. The structured-JSON return shape includes a `CalendarEventId` for tools that publish events; lockout returns `LockoutResponse` (still spec-only per §C.4 / NEXT.md:61) without publishing.
- **Brief composer voice** calibrates to a calendar-event-notes context: markdown-ish, concise, persistent (Joe re-reads at noon), no preamble that assumes an interactive session.
- **Rule 34 enforcement.** Calendar events are NOT created during FAMILY_LOCKOUT (the publish call is gated by the per-tool lockout check per [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §7 layer 3). The `override_token` mechanism (still spec-only per RULES.md:185) governs exceptions.
- **`README.md:7` "always-on" framing.** The framing is now operationalized: Hanna fires briefs on a wall-clock schedule that lands in Joe's calendar regardless of whether Joe is in a Claude session. The "always-on" claim becomes real once `src/channels/calendar.py` lands. The README sentence wants a small cosmetic update to name the channel (deferred to the documentation-hygiene pass per [`REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) §3.3).
- **§12.7 input surface (D007 drafted in the next commit) is orthogonal.** Per-product `.md` files remain the proposed input-surface MVS regardless of channel; D006 and D007 do not bind each other.
- **§4 USD-stage Cut (D008 drafted in the next commit) is corroborated.** D006 chooses an OS-level surface (Calendar) over a Hanna-authored stage; this matches the audit's posture that USD as a stage-composition substrate is the wrong fit for Hanna's workload. Calendar IS the stage for v1.

**Related.**
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §12.6 — the audit-added open decision this entry resolves.
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) Audit Log finding #4 — the "always-on producer contradicts MCP-tools-only" tension.
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §5 "Producer UI Surface" line 213 — the channel-agnostic posture (restraint, no red, deliberate negative space, calm typography) inherits to Calendar.
- [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) §3.1 — the first-principles review that surfaced the resolution.
- [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) §5 — the prior D006 seed (status-open test plan) this decision overrides.
- D001 — the bridge-side ratification; D006 is the channel-side ratification.
- D002 — D006 is author-by-main-thread substrate work; the eventual `src/channels/calendar.py` implementation is MoE-eligible.
- [`RULES.md`](../RULES.md) §34 (family-first lockout) and §36 (surface, don't decide) — the rules that justify the channel choice.

---

### D007 — Input surface MVS: per-product `.md` files

**Status:** resolved
**Date:** 2026-05-22
**Ratified by:** Joe (Joseph Ibrahim) — whole-batch ratification alongside D005 and D008
**Scope:** [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §12.7 (audit-added input surface decision); §5.6 "Input surface" lines 196–203; the brief composer's source-of-state (currently fiction at `scripts/first_hanna_brief.py:95–104`); the future `mcp_tools` lane (`hanna_log` / `hanna_block` candidates).

**Decision.** Hanna's input surface for v1 is **per-product markdown files at `data/products/{name}.md`**. One file per portfolio product. Joe edits the file directly when state changes. File mtime is the freshness signal. The brief composer reads the file set on each compose call and renders accordingly. The six sub-decisions below (D007.1–D007.6) are **ratified whole-batch** at their proposed defaults.

**Reasoning.** Per [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §5.6, three candidate input layers were sketched:

- (a) Per-product `.md` files — lowest implementation cost, zero external API surface, Joe edits in any editor.
- (b) Calendar reads — Joe schedules in tools already used; Hanna reads dated events as forcing functions.
- (c) Conversational MCP tools (`hanna_log` / `hanna_block` / `hanna_unblock`) — single-sentence-becomes-state from any Claude session.

The audit's proposed default (BLUEPRINT:373) is (a) first, then (b), then (c). This entry ratifies **(a) as the MVS**. The other two layers are not foreclosed — they become add-ons once (a) is in production.

(a) is chosen first because: implementation cost is `Path.read_text()`; dependency surface is zero (no external API); freshness signal (file mtime) is trivially readable; Joe's existing editor habit transfers directly; and per-product separation enforces a discipline ("which product is this about?") that conversational tools blur.

The choice also harmonizes with [D006](#d006--delivery-channel-dedicated-hanna-icloud-calendar-with-0-minute-anchor-events) (Calendar channel resolved): both decisions favor surfaces Joe already inhabits over Hanna-authored fresh substrate. Calendar is the output where Hanna lives; `.md` files are the input where Joe lives. Each tool used in its grain.

**Proposed shape (open for ratification).** Each product file follows a consistent structure:

```markdown
---
product: harlo
status: in_flight
last_review_iso: 2026-05-22
---

## Status

[1–3 sentences naming where the product currently is.]

## Blockers

- [Bullet list of blockers; empty means "no blockers."]

## Approaching forcing functions

- [Bullet list with dates; e.g., "2026-05-30: Q2 review presentation"]

## Notes

[Free-form. Anything Joe wants to surface to Hanna that doesn't fit above.]
```

The frontmatter is YAML-style; the body is plain markdown with named sections. The brief composer reads each file and renders selectively: `status` → state line; `blockers` → blockers line; `approaching forcing functions` → "approaching this week" line; `notes` → optional flavor.

**Initial product set** (matches [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §5 line 186, expandable per session): `harlo`, `octavius`, `moneta`, `comfy_cozy`. The MVS ships with these four files at `data/products/{name}.md`, even if some are empty stubs — the directory and pattern are the deliverable, not the prose.

**Per-item resolutions (ratified whole-batch 2026-05-22).**

- **D007.1 — Frontmatter format.** YAML-style, TOML, or no frontmatter (sections only). YAML matches the modern markdown convention; TOML is type-strict; no-frontmatter is plain. **Ratified: YAML.**
- **D007.2 — `status` enum.** `{in_flight, parked, shipped, exploring}`, or freeform string. An enum disciplines the composer; freeform gives Joe full expression. **Ratified: enum (the four members above).**
- **D007.3 — Empty-file handling.** Ship empty stub files for every product on the initial-set list, or only the ones with real content today? **Ratified: empty stubs ship** — the pattern is the deliverable.
- **D007.4 — Calendar reads (layer b) follow-on.** Once (a) is in production, add Calendar reads? **Ratified: yes, deferred to a follow-on D-entry when (a) has shipped.**
- **D007.5 — Conversational MCP tools (layer c) follow-on.** Same shape. **Ratified: deferred; opens once `mcp_tools` lane has the channel-side ratified (D006 → Calendar already done in this session).**
- **D007.6 — `.gitignore` posture.** Should `data/products/*.md` be tracked (the substrate) or untracked (Joe's private state)? **Ratified: tracked.** The product file IS the substrate; brief composition is reproducible only if state is committed. Joe edits the file → commits the edit → Hanna reads the committed file. Cost: Joe's private blocker notes become git-history; mitigation: he writes the notes accordingly, or per-product files use a `.private.md` extension that IS gitignored for sensitive entries.

**Implications.**

- A new directory `data/products/` joins the repo. Per [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §3 the directory is checked-in. Per §10 the input lane joins the diagram as a new lane upstream of brief composition.
- The brief composer at `scripts/first_hanna_brief.py:95–104` becomes a function of `(Harlo state, ProducerPhase, product file set)` instead of fiction. The fiction text Joe sees today ("the open lanes from yesterday's session are still where you left them") is replaced by per-product status reads.
- The `mcp_tools` lane gains `hanna_log` / `hanna_block` candidate tools that write back to the product files via APPEND-ONLY semantics (never overwrite Joe's hand-edits). This is D007.5.
- Schema completeness gains a `ProductFile` type at `src/schemas.py` — parsed-frontmatter + sections. Becomes part of the schema work [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) §3.4 catalogued.

**Related.**
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §12.7 — the audit-added open decision this entry operationalizes.
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §5.6 — the three-layer input-surface sketch.
- D006 (this session) — channel resolved orthogonally; D007 binds the input side. Symmetry.
- [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) §3.6 — the review's catalog of §12.7 as blocking-pending.
- D002 — D007 is author-by-main-thread substrate work; the `ProductFile` schema and the brief-composer rewrite become MoE under future dispatches.

---

### D008 — §4 inheritance ratification: Cut six pending items; Review the 33 rules

**Status:** resolved
**Date:** 2026-05-22
**Ratified by:** Joe (Joseph Ibrahim) — whole-batch ratification alongside D005 and D007
**Scope:** [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §4 substrate inheritance table (lines 110–125); §12.8 the audit-added per-item ratification requirement; downstream lanes that inherit assumptions from §4 (delegate, stage, computations, hot/warm/cold storage); [`.gitignore`](../.gitignore) dual-venv references (lines 18–20).

**Decision.** §4 carries Cut or Review status on seven inherited components from the [2026-05-20 audit](../HANNA_BLUEPRINT.md). All seven per-item proposals below were **ratified whole-batch** as the resolution: six items Cut (D008.1–D008.6), one Reviewed with selective re-adoption (D008.7).

**Per-item resolutions (ratified whole-batch 2026-05-22).**

- **D008.1 — Hydra delegate pattern (`src/delegate_*.py`).** v0.1.0 plan: clone pattern + base class. Audit status: Cut (pending). **Ratified: Cut.** The delegate pattern was designed for routing tasks across model backends with capability negotiation; Hanna calls Claude. One backend = indirection in search of a purpose. The "second layer" of Rule 34's three-layer enforcement (the `HdProducer` delegate route) collapses into per-tool lockout checks (layer 3), which is acceptable because layer 3 already runs the check structurally per BLUEPRINT §7.

- **D008.2 — USD stage architecture.** v0.1.0 plan: verbatim. Audit status: Cut (pending). **Ratified: Cut.** USD is a stage-composition language for film pipelines; Hanna's corpus is ~10 briefs/week × ~2KB. SQLite + JSON dominates on every axis at this volume. The PoC at `scripts/first_hanna_brief.py:107–115` already writes to SQLite (`data/hanna.sqlite`); the USD stage was never built. D006's Calendar choice corroborates: Calendar IS the stage for v1. Cut formalizes the de-facto state.

- **D008.3 — Three-tier storage (Hot FTS5 / Warm SDR / Cold USD).** v0.1.0 plan: verbatim. Audit status: Cut (pending). **Ratified: Cut.** Three-tier storage was sized for sub-2ms cognitive recall under continuous load; Hanna's latency budget is "before coffee gets cold." One SQLite file per logical table (briefs, capsules, snapshots) is the whole job. Cut formalizes; SQLite-only is the substrate.

- **D008.4 — Rust hot path via PyO3.** v0.1.0 plan: inherited via cloned crates. Audit status: Cut (pending). **Ratified: Cut.** No hot path exists; Hanna runs six events/day on a wall clock. The cloned crates (none of which have shipped in this repo yet) are removed from the lane diagram. Cut formalizes the de-facto state.

- **D008.5 — XGBoost predictor harness.** v0.1.0 plan: verbatim; retrained on producer signals. Audit status: Cut (pending). **Ratified: Cut.** Two empirical facts force this: (1) Harlo's own predictor is currently inactive (`v9.engine.predictor: false` per [`SPIKE_HARLO_EDGE_2026-05-20.md`](SPIKE_HARLO_EDGE_2026-05-20.md) §4), so there is nothing live to bootstrap from; (2) a hand-coded heuristic ("deadline within 5 working days × in-flight product count") outperforms an undertrained model and ships in 30 minutes. [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) §3.6 assumes this Cut.

- **D008.6 — Dual venv (3.12 USD / 3.14 project).** v0.1.0 plan: verbatim. Audit status: Cut (pending). **Ratified: Cut.** Falls out automatically once D008.2 USD is cut. [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) Action 2 (pyproject.toml + Hanna venv) ratifies a single-venv posture; D008.6 confirms the substrate matches.

- **D008.7 — The 33 inviolable rules (Review).** v0.1.0 plan: inherited verbatim. Audit status: Review (the producer addenda 34–37 stay). **Ratified: Review with selective re-adoption.** Rules 1–8, 11–17, 19–33 are guardrails for code that doesn't exist in Hanna (hippocampal mutation, motor reflex compilation, inquiry verification). Their compliance greps in [`RULES.md`](../RULES.md) pass trivially because the constrained code isn't there — a green CI light meaning nothing. Re-adopt rules as the underlying components actually land (e.g., Rule 18 RED override stays now because the Harlo bridge respects it via `read_burnout_level`). Annotate each non-active rule in `RULES.md` as "Not yet load-bearing — applies on the session that lands the constrained component" (per [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §13 already-stated convention).

**Reasoning.** All seven items were audited 2026-05-20 against Hanna's actual workload (~10 briefs/week × ~2KB, 6 events/day on a wall clock). The audit's verdict was Cut/Review across the board because each component was sized for Harlo's continuous-cognitive-load workload, not Hanna's wall-clock scheduler. **Ratifying the Cut/Review status (rather than leaving §4 in a "pending ratification" purgatory) lets downstream lanes proceed without inheriting unfaithful assumptions.**

The 33 rules are Review rather than Cut because the *posture* they encode (biological-fidelity, surface-don't-decide, family-first) is producer-applicable even where the specific code isn't. Selective re-adoption preserves the posture.

**Implications.**

- **Lane diagram refresh.** [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §10 build lanes diagram updates: `delegate` lane removed (D008.1), `stage` lane reduced from USD prim authoring to SQLite table inserts (D008.2/3), Rust crates removed from any future lane (D008.4), XGBoost lane removed (D008.5), dual venv removed (D008.6). The diagram becomes smaller and honest.
- **`HdProducer` delegate code.** No file exists yet. With D008.1 Cut ratified, no file ever ships. The "second layer" of Rule 34 enforcement collapses into per-tool lockout checks (layer 3).
- **§5 specialization list.** Items "New Hydra delegate" and "New stage prims" in [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §5 get struck-through in the BLUEPRINT update accompanying D008's ratification. The four pure-function computations (`compute_producer_phase` already landed; `compute_brief_priority` / `compute_forcing_function` / `compute_formation_readiness` still to come) stay — that's the Keep-load-bearing inheritance from [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) Audit Log finding #3.
- **CI compliance greps.** Per D008.7, the trivially-passing greps in `RULES.md` (`sleep`, `while True`, `float32`, `cosine`) get annotated as "applies if the relevant component is landed." Documentation change, not a CI change.
- **README + BLUEPRINT cleanup.** Once D008 ratifies, the BLUEPRINT §4 table's "Audit status" column becomes "Decision (D008)" with each row carrying Keep / Cut / Review per the ratification. The "pending ratification" tag drops. Separate hygiene-pass commit (per [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) §3.3 deferred list).

**Open question parked.** If Joe ratifies all six Cuts and the components have not been built (which is the case for all six at HEAD), is there anything to *remove* from the repo? **Answer: nothing meaningful.** The dual-venv references in `.gitignore:18–20` (`.venv/`, `venv/`, `.venv-*/`) stay (they cover the future Hanna venv after [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) Action 2 lands). The `.gitignore:24–27` USD stage data patterns are cheap and harmless; they can stay. Cut formalizes the de-facto absence; no active removal needed.

**Related.**
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §4 substrate inheritance table — the per-item Cut/Review status this entry ratifies.
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §12.8 — the audit-added per-item ratification requirement.
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) Audit Log finding #2 — "Substrate inheritance is over-scoped for the workload."
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) Audit Log finding #3 — "The single load-bearing inheritance is the pure-function-over-enum pattern."
- [`docs/REVIEW_2026-05-22.md`](REVIEW_2026-05-22.md) §3.6 — the review's catalog of §12.8 as blocking-pending.
- [`docs/SPIKE_HARLO_EDGE_2026-05-20.md`](SPIKE_HARLO_EDGE_2026-05-20.md) §4 — Harlo's predictor inactive (corroborates D008.5).
- D001, D003 — prior substrate decisions this entry harmonizes with.
- D006 (this session) — Calendar channel choice corroborates D008.2 (USD Cut).
- D002 — D008 is author-by-main-thread substrate work; ratifying the Cuts means no MoE follow-on is needed for the components themselves; the dropped lane diagram is a documentation change.

---

## End of decisions log

Next decision number: **D009**.
