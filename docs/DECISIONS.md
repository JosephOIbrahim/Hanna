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

## End of decisions log

Next decision number: **D002**.
