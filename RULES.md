# Hanna — Inviolable Rules

Inherited from Harlo (`github.com/JosephOIbrahim/Harlo`).
Apache 2.0 License. Original authorship preserved.

These rules are non-negotiable in Hanna. Extracted verbatim from
[`Harlo/CLAUDE.md` lines 37–194](https://github.com/JosephOIbrahim/Harlo)
("The 33 Inviolable Rules" — 33 numbered rules + 8 inquiry safeguards).
Producer-specific addenda follow at §34–37.

**Actual rule count:** 33 numbered inviolable rules + 8 inquiry safeguards (S1–S8) + 4 producer-specific addenda = **45 items.** The phrase "33 inviolable rules" refers to the numbered core; safeguards are sibling, addenda are extensions.

**Applicability note (ratified by [D008.7](docs/DECISIONS.md) 2026-05-22):** rules reference components inherited from Harlo's substrate (e.g., Rust hot path, hippocampus FFI, ONNX encoder). Where Hanna has not yet cloned the component, **the rule is "Not yet load-bearing — applies on the session that lands the constrained component"** — not as license to skip. The substrate is the architecture, not the schedule.

**Currently load-bearing rules:** Rule 18 (RED override, via the Harlo bridge's `read_burnout_level`), Rule 34 (family-first lockout — Layer 1 landed in `compute_producer_phase`; Layer 2 `HdProducer` delegate Cut per [D008.1](docs/DECISIONS.md); Layer 3 per-tool MCP gating deferred to the L6 `mcp_tools` lane per [`docs/ROADMAP.md`](docs/ROADMAP.md) §5), Rule 35 (cross-substrate writes prohibited, gated by the Harlo bridge surface ratified in D001 + hardened in [L3b](docs/ROADMAP.md) per D005), Rule 36 (surface, don't decide, encoded in pure-enum returns), Rule 37 (patent topics never raised, zero exceptions). Rules 1–8, 11–17, 19–33 await their constrained components per D008.7's selective re-adoption posture.

---

## Biological Constraints (v3.0)

1.  **0-WATT IDLE:** OS socket activation. No `while True`. No `sleep()`.
    Daemon exits when idle. 0W between sessions.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

2.  **ACTION POTENTIALS:** Hippocampal vectors MUST be 1-bit boolean
    arrays (Sparse Distributed Representations). Bitwise XOR
    (Hamming distance) for search. No float32. No cosine similarity.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

3.  **RUST HOT PATH:** Association Engine is Rust via PyO3.
    Cold start: <5ms. Hot recall: <2ms. No Python in hot path.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

4.  **LAZY DECAY:** Timestamp math on retrieval only. No polling.
    `strength = initial * e^(-lambda * dt) + sum(retrieval_boosts)`
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

5.  **APOPTOSIS:** `twin consolidate` physically DELETEs traces below
    epsilon. Runs VACUUM. Database file size decreases.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

6.  **MERKLE TREES:** Composition stages use Merkle Tree hashing.
    Partial branch O(log n). Not full-file SHA256 O(n).
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

7.  **AMYGDALA:** SAFETY/CONSENT resolutions = 1-shot permanent reflex.
    Skip GVR. Skip 10-rep curve. Instant compile to cerebellum.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

8.  **JSON BARRIER:** `jsonschema.validate()`. Strip `epigenetic_wash` on
    write path. Mood ephemeral. Facts permanent. No XML. No regex.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

9.  **ALLOSTATIC LOAD:** Token velocity + prompt frequency. Software
    only. High = DEPLETED = refuse to wake System 2.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

10. **ANCHORS:** SAFETY/CONSENT/KNOWLEDGE/CONSTITUTIONAL = gain 1.0
    ALWAYS. Structural. Returns 1.0 before evaluating receptor density.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

## Elenchus Constraints (v4.0)

11. **TRACE EXCLUSION:** `verify()` NEVER receives reasoning trace.
    Parameter must be None or absent. BUILD FAILS if present.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

12. **VERIFIED-ONLY CONSOLIDATION:** Only VERIFIED resolutions become
    reflexes. FIXABLE/SPEC_GAMED/UNPROVABLE never consolidated.
    BUILD FAILS if unverified resolution leaks to reflex cache.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

13. **MAX 3 GVR CYCLES:** ADHD guard. After cycle 3, promote FIXABLE
    to UNPROVABLE. Loop MUST terminate.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

14. **INTENT PRESERVATION:** Bridge checks output answers the original
    intent, not a reframed easier question.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

15. **SPEC-GAMING DETECTION:** Correct answer to wrong question is the
    dominant failure mode. Detect it. Surface it. Never consolidate it.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

16. **UNPROVABLE IS DIGNIFIED:** Carries metadata (reason, what_would_help,
    partial_progress). First-class state. Park with dignity.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

17. **BURST DEFERS, NOT SKIPS:** Queue unverified outputs during burst.
    Run GVR on burst exit. Surface problems.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

18. **RED OVERRIDES EVERYTHING:** No GVR. No injection. No inquiry.
    No motor. Full stop. Recovery menu.

## Inquiry Safeguards (v5.1–v5.2)

S1. **APOPHENIA GUARD:** Minimum evidence threshold per inquiry depth
    (5/8/15/25 independent observations). Alternative hypothesis
    required. Confidence disclosure mandatory.

S2. **EPISTEMOLOGICAL BYPASS:** Inquiry outputs verified for tone +
    boundaries, NOT objective truth. Self-reported traces bypass
    Elenchus ONLY when consumed by `src/inquiry/` namespace.
    Composition namespace gets standard verification (DIRECTIONAL).

S3. **RUPTURE & REPAIR:** Rejection = permanent non-decaying trace
    (weight 2.0). Apophenia threshold adjusts. Repair bid delayed.
    3 rejections → offer to stop. Threshold mean-reverts over time
    (90-day halflife + 0.1 credit per accepted inquiry).

S4. **UTILITY MODE:** `twin mode utility` mutes DMN. Behavioral traces
    invisible to inquiry. Semantic state updates visible (WHAT not HOW).
    Mode switch NOT logged as behavioral trace. Timestamps fuzzed
    to ISO week before DMN synthesis.

S5. **INQUIRY APOPTOSIS:** Queued inquiries carry TTL (48h–30d by type).
    Decay via `e^(-3t/ttl)`. Below 20% relevance = physical delete.

S6. **DMN SYNTHESIS WINDOW:** Asynchronous teardown. CLI released in
    <50ms. Daemon runs background synthesis up to 30 seconds.
    Then process exits. 0W.

S7. **TRACE CRYSTALLIZATION:** Emerging patterns (3+ observations,
    below threshold) get decay rate reduced to `lambda/10`. Max 50
    crystallized traces. Stale after 30 days without new obs.
    Eviction by `preservation_score = (obs/threshold) * depth_weight`.

S8. **SINCERITY GATE:** User responses classified as sincere/sarcastic/
    exasperated/performative/uncertain before tagging `self_reported`.
    Sarcasm → emotional_rupture. Performative → low weight.
    Uncertain → ask for clarification. Default: trust the user.

## Motor Cortex Constraints (v6.0)

19. **TEARDOWN PREEMPTION:** New CLI commands during DMN teardown MUST
    preempt. Save to temp file (`/dev/shm/`), NOT SQLite. Release
    in <10ms. Human presence always wins.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

20. **PERCEPTION GAP TRACES:** When Elenchus falsifies `self_reported`
    trace in Composition, emit `perception_gap` trace. DMN turns
    the contradiction into a co-evolutionary inquiry.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

21. **CRYSTALLIZATION EVICTION:** `preservation_score = (obs/threshold)
    * depth_weight`. Evict lowest. Deep patterns survive over noise.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

22. **UTILITY TIMESTAMP FUZZING:** Fuzz to ISO week before DMN synthesis
    on utility-mode semantic traces.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

23. **INHIBITION DEFAULT:** Basal Ganglia defaults to INHIBIT ALL.
    Every action requires ALL five checks to pass. One failure =
    inhibit. No exceptions.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

24. **ONE ACTION AT A TIME:** Motor Cortex executes ONE atomic action,
    returns to full cognitive loop. No automatic chaining.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

25. **LEVEL 3 IS STRUCTURAL:** Financial transactions, irreversible
    deletions, other people's data, anchor-touching actions.
    Gate NEVER opens. Like anchor immunity.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

26. **MOTOR REFLEXES ALWAYS GATED:** Skip planning, NEVER skip Basal
    Ganglia. Safety checks run every time, even on cached patterns.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

27. **DEPLETED DOWNGRADES MOTOR:** DEPLETED state → Level 1 becomes
    Level 2 (require per-action consent).
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

28. **RED KILLS MOTOR:** RED state halts ALL motor activity. Gate locked.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

29. **REVERSIBILITY CAP:** Level 1 + irreversible = Level 2.
    Level 2 stays Level 2 (flagged RED in UI).
    Level 3 is ONLY for anchor/consent violations.
    NEVER: Level 2 + irreversible = Level 3 (logical deadlock).
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

30. **PREEMPTION TEMP FILE:** During abort, dump to `/dev/shm/` or `.tmp`.
    NEVER write to SQLite during preemption. Kill process. Hot-path
    reads, merges, deletes temp file on boot.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

31. **ACTION PLAN PERSISTENCE:** Active ActionPlan + `current_step_index`
    stored in Composition stage. Motor mutates to Step N+1 on
    success. Premotor checks for active plan before generating new.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

32. **MOTOR REFLEX ZERO-TOLERANCE:** Single failure = instant
    de-compilation (`compiled=False, success_count=0`). Route to
    Premotor for re-planning.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

33. **BLIND SPOT ACCEPTANCE:** If user rejects `perception_gap` inquiry,
    tag claim as `blind_spot_accepted`. Elenchus keeps using objective
    truth for Composition but NEVER emits gap traces for that
    specific claim again. Claim-specific, not categorical.
    The Twin chooses the relationship over the truth.
    *Not yet load-bearing per [D008.7](docs/DECISIONS.md) — applies on the session that lands the constrained component.*

---

## Producer-specific addenda

### Rule 34 — Family-first lockout

Family hours (Mon–Fri 09:00–17:00 inverse, i.e. evenings + weekends) are a structural constraint, not a setting. Enforced at **two active layers** (Layer 2 was Cut per [D008.1](docs/DECISIONS.md); layer numbering preserved for backward reference):

1. **State machine (`compute_producer_phase`):** returns `FAMILY_LOCKOUT` outside Mon–Fri 09:00–17:00, regardless of other inputs. No downstream surface generates briefs or formations during lockout.
2. ~~**Delegate routing (`HdProducer`):**~~ **Cut per [D008.1](docs/DECISIONS.md).** Hanna calls Claude directly with no delegate routing; this layer collapses into Layer 3 (per-tool lockout).
3. **MCP tool gating:** every Hanna MCP tool checks lockout before executing. Lockout returns a structured `LockoutResponse`, not an error. Calling Hanna during family time is a well-defined no-op. *Currently deferred to the L6 `mcp_tools` lane per [`docs/ROADMAP.md`](docs/ROADMAP.md) §5.*

Override path exists for true exceptions: explicit `override_token` with TTL (HMAC-signed, single-use). This is a deliberate friction surface, not a flag. Tests verify the two active layers; the layer-3 test scaffold lands with L6. **Bypassing any active layer fails CI.**

### Rule 35 — Cross-substrate writes prohibited

Hanna never writes to Harlo. Hanna never writes to Octavius outside of the formation spawn/poll/harvest contract.

- **Harlo edge:** read-only. `src/harlo_bridge.py` exposes `read_state`, `read_prediction`, `read_burnout_level`. Any function that mutates Harlo state is a rule violation.
- **Octavius edge:** request-only. `src/octavius_bridge.py` exposes `spawn_formation`, `formation_status`, `formation_output`. Anything beyond this contract is a rule violation.

Each substrate stays single-purpose: Harlo owns cognitive-state truth, Hanna owns producer-rhythm truth, Octavius owns multi-agent execution.

### Rule 36 — Surface, do not decide

Every Hanna output is framed as a surfaced decision, not a directive. Hanna surfaces what's in-flight, what's blocking, what's approaching. The director directs.

Concrete shape:

- Briefs are observations, not action items.
- Forcing-function warnings are timestamps + signal, not commands.
- Formation requests are proposals, not auto-spawns (gated by the `hanna_request_formation` MCP tool).
- The XGBoost predictor surfaces a forecast distribution, not a single prescription.

### Rule 37 — Patent topics never raised

Hard rule. No exceptions. No prompts. No suggestions. No analysis. No tangents. No "here's an interesting question" framings.

This rule is meta-honored by every session prompt, every commit message, every doc generated. The rule applies to Hanna's outputs and to any session where Hanna is the build subject.

---

## Compliance Checks

The Harlo originals (`Harlo/CLAUDE.md` lines 195–205) check `python/harlo/` paths. Hanna's actual code lives in `src/` (modules), `scripts/` (entrypoints), and `tests/` (suite). The Harlo-class Rust hot-path / hippocampus-FFI / ONNX-encoder components have not been cloned (per [D008.7](docs/DECISIONS.md) selective re-adoption posture), so the cloned-crate greps below are scoped to `src/` and `scripts/` and re-activate once those components land:

```bash
grep -rn "sleep(" src/ scripts/                                   # MUST return 0 results (Rule 1)
grep -rn "while True" src/ scripts/ | grep -v "src/harlo_bridge.py"  # MUST return 0 results (Rule 1 — bridge frame-read exempted)
grep -rn "float32" src/ scripts/                                  # MUST return 0 results until Rust hot path lands (Rule 2)
grep -rn "cosine" src/ scripts/                                   # MUST return 0 results until Rust hot path lands (Rule 2)
grep -rn "DELETE.*audit" src/ scripts/                            # MUST return 0 results (Rule 5)
grep -rn "reasoning_trace" src/                                   # MUST return 0 results until Elenchus verifier lands (Rule 11)
grep -rn "store_reflex" src/ scripts/                             # MUST return 0 results until reflex consolidation lands (Rule 12)
```

Producer-specific compliance checks:

```bash
# Rule 35 — name-anchored first line of defense (catches obvious renames of forbidden verbs)
grep -rE "harlo\.(write|store|author|mutate|commit|persist|save|update)" src/ scripts/         # MUST return 0 results
grep -rE "octavius\.(write|store|author|mutate|commit|persist|save|update)" src/ scripts/      # MUST return 0 results
# Rule 35 — enumerated bridge-surface allowlist (the authoritative check, per D001):
#   src/harlo_bridge.py must only call _call_tool("X") for X in
#   {status, coach, recall, query_past_experience, patterns}.
#   The forbidden Harlo tools (store, stage_reload, resolve_verifications,
#   trigger_cognitive_recalibration) must NEVER appear. CI enforces this
#   via an inline python check in .github/workflows/ci.yml.
grep -rE "\b(stage_reload|resolve_verifications|trigger_cognitive_recalibration)\b" src/ scripts/  # MUST return 0 results
# Rule 37 — patent topics never raised. Code, scripts, tests, docs, and commit messages.
#   Meta-references to "Rule 37" itself and recipe self-references are exempted
#   via `grep -v` in the CI step (.github/workflows/ci.yml).
grep -rEi "patent|provisional|uspto|claim[[:space:]]+language" src/ scripts/ tests/ docs/  # MUST return 0 results after exemptions
git log -50 --format=%B | grep -iE "patent|provisional|uspto|claim[[:space:]]+language"    # MUST return 0 results after exemptions
# Lockout three-layer test (Rule 34) — see tests/test_integration/test_lockout.py
```

---

## End of RULES.md

Changes to this document require a substrate-level decision and must be ratified in `docs/DECISIONS.md` before merge.
