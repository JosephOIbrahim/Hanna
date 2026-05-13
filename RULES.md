# Hanna — Inviolable Rules

Inherited from Harlo (`github.com/JosephOIbrahim/Harlo`).
Apache 2.0 License. Original authorship preserved.

These rules are non-negotiable in Hanna. Extracted verbatim from
[`Harlo/CLAUDE.md` lines 37–194](https://github.com/JosephOIbrahim/Harlo)
("The 33 Inviolable Rules" — 33 numbered rules + 8 inquiry safeguards).
Producer-specific addenda follow at §34–37.

**Actual rule count:** 33 numbered inviolable rules + 8 inquiry safeguards (S1–S8) + 4 producer-specific addenda = **45 items.** The phrase "33 inviolable rules" refers to the numbered core; safeguards are sibling, addenda are extensions.

**Applicability note:** rules reference components inherited from Harlo's substrate (e.g., Rust hot path, hippocampus FFI, ONNX encoder). Where Hanna has not yet cloned the component, the rule applies as soon as the component is added — not as license to skip. The substrate is the architecture, not the schedule.

---

## Biological Constraints (v3.0)

1.  **0-WATT IDLE:** OS socket activation. No `while True`. No `sleep()`.
    Daemon exits when idle. 0W between sessions.

2.  **ACTION POTENTIALS:** Hippocampal vectors MUST be 1-bit boolean
    arrays (Sparse Distributed Representations). Bitwise XOR
    (Hamming distance) for search. No float32. No cosine similarity.

3.  **RUST HOT PATH:** Association Engine is Rust via PyO3.
    Cold start: <5ms. Hot recall: <2ms. No Python in hot path.

4.  **LAZY DECAY:** Timestamp math on retrieval only. No polling.
    `strength = initial * e^(-lambda * dt) + sum(retrieval_boosts)`

5.  **APOPTOSIS:** `twin consolidate` physically DELETEs traces below
    epsilon. Runs VACUUM. Database file size decreases.

6.  **MERKLE TREES:** Composition stages use Merkle Tree hashing.
    Partial branch O(log n). Not full-file SHA256 O(n).

7.  **AMYGDALA:** SAFETY/CONSENT resolutions = 1-shot permanent reflex.
    Skip GVR. Skip 10-rep curve. Instant compile to cerebellum.

8.  **JSON BARRIER:** `jsonschema.validate()`. Strip `epigenetic_wash` on
    write path. Mood ephemeral. Facts permanent. No XML. No regex.

9.  **ALLOSTATIC LOAD:** Token velocity + prompt frequency. Software
    only. High = DEPLETED = refuse to wake System 2.

10. **ANCHORS:** SAFETY/CONSENT/KNOWLEDGE/CONSTITUTIONAL = gain 1.0
    ALWAYS. Structural. Returns 1.0 before evaluating receptor density.

## Elenchus Constraints (v4.0)

11. **TRACE EXCLUSION:** `verify()` NEVER receives reasoning trace.
    Parameter must be None or absent. BUILD FAILS if present.

12. **VERIFIED-ONLY CONSOLIDATION:** Only VERIFIED resolutions become
    reflexes. FIXABLE/SPEC_GAMED/UNPROVABLE never consolidated.
    BUILD FAILS if unverified resolution leaks to reflex cache.

13. **MAX 3 GVR CYCLES:** ADHD guard. After cycle 3, promote FIXABLE
    to UNPROVABLE. Loop MUST terminate.

14. **INTENT PRESERVATION:** Bridge checks output answers the original
    intent, not a reframed easier question.

15. **SPEC-GAMING DETECTION:** Correct answer to wrong question is the
    dominant failure mode. Detect it. Surface it. Never consolidate it.

16. **UNPROVABLE IS DIGNIFIED:** Carries metadata (reason, what_would_help,
    partial_progress). First-class state. Park with dignity.

17. **BURST DEFERS, NOT SKIPS:** Queue unverified outputs during burst.
    Run GVR on burst exit. Surface problems.

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

20. **PERCEPTION GAP TRACES:** When Elenchus falsifies `self_reported`
    trace in Composition, emit `perception_gap` trace. DMN turns
    the contradiction into a co-evolutionary inquiry.

21. **CRYSTALLIZATION EVICTION:** `preservation_score = (obs/threshold)
    * depth_weight`. Evict lowest. Deep patterns survive over noise.

22. **UTILITY TIMESTAMP FUZZING:** Fuzz to ISO week before DMN synthesis
    on utility-mode semantic traces.

23. **INHIBITION DEFAULT:** Basal Ganglia defaults to INHIBIT ALL.
    Every action requires ALL five checks to pass. One failure =
    inhibit. No exceptions.

24. **ONE ACTION AT A TIME:** Motor Cortex executes ONE atomic action,
    returns to full cognitive loop. No automatic chaining.

25. **LEVEL 3 IS STRUCTURAL:** Financial transactions, irreversible
    deletions, other people's data, anchor-touching actions.
    Gate NEVER opens. Like anchor immunity.

26. **MOTOR REFLEXES ALWAYS GATED:** Skip planning, NEVER skip Basal
    Ganglia. Safety checks run every time, even on cached patterns.

27. **DEPLETED DOWNGRADES MOTOR:** DEPLETED state → Level 1 becomes
    Level 2 (require per-action consent).

28. **RED KILLS MOTOR:** RED state halts ALL motor activity. Gate locked.

29. **REVERSIBILITY CAP:** Level 1 + irreversible = Level 2.
    Level 2 stays Level 2 (flagged RED in UI).
    Level 3 is ONLY for anchor/consent violations.
    NEVER: Level 2 + irreversible = Level 3 (logical deadlock).

30. **PREEMPTION TEMP FILE:** During abort, dump to `/dev/shm/` or `.tmp`.
    NEVER write to SQLite during preemption. Kill process. Hot-path
    reads, merges, deletes temp file on boot.

31. **ACTION PLAN PERSISTENCE:** Active ActionPlan + `current_step_index`
    stored in Composition stage. Motor mutates to Step N+1 on
    success. Premotor checks for active plan before generating new.

32. **MOTOR REFLEX ZERO-TOLERANCE:** Single failure = instant
    de-compilation (`compiled=False, success_count=0`). Route to
    Premotor for re-planning.

33. **BLIND SPOT ACCEPTANCE:** If user rejects `perception_gap` inquiry,
    tag claim as `blind_spot_accepted`. Elenchus keeps using objective
    truth for Composition but NEVER emits gap traces for that
    specific claim again. Claim-specific, not categorical.
    The Twin chooses the relationship over the truth.

---

## Producer-specific addenda

### Rule 34 — Family-first lockout

Family hours (Mon–Fri 09:00–17:00 inverse, i.e. evenings + weekends) are a structural constraint, not a setting. Enforced at three layers:

1. **State machine (`compute_producer_phase`):** returns `FAMILY_LOCKOUT` outside Mon–Fri 09:00–17:00, regardless of other inputs. No downstream surface generates briefs or formations during lockout.
2. **Delegate routing (`HdProducer`):** RED-state override is inherited from Rule 18. `FAMILY_LOCKOUT` is the second override. Nothing routes through the delegate during lockout.
3. **MCP tool gating:** every Hanna MCP tool checks lockout before executing. Lockout returns a structured `LockoutResponse`, not an error. Calling Hanna during family time is a well-defined no-op.

Override path exists for true exceptions: explicit `override_token` with TTL (HMAC-signed, single-use). This is a deliberate friction surface, not a flag. Tests verify all three layers. **Bypassing any layer fails CI.**

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

The Harlo originals (`Harlo/CLAUDE.md` lines 195–205) check `python/harlo/` paths. For Hanna, the equivalent checks target `python/hanna/`:

```bash
grep -r "sleep(" python/hanna/                            # MUST return 0 results
grep -r "while True" python/hanna/                        # MUST return 0 results
grep -r "float32" crates/                                 # MUST return 0 results (cloned crates)
grep -r "cosine" crates/                                  # MUST return 0 results (cloned crates)
grep -r "DELETE.*audit" python/hanna/                     # MUST return 0 results
grep -r "reasoning_trace" python/hanna/elenchus/verifier.py  # Must be None/absent
grep -r "store_reflex" python/hanna/                      # Must check verification_state
```

Producer-specific compliance checks:

```bash
grep -rE "harlo\.(write|store|author|mutate)" src/        # MUST return 0 results (Rule 35)
grep -rE "octavius\.(write|store|author|mutate)" src/     # MUST return 0 results (Rule 35)
grep -rEi "patent|provisional|uspto|claim[[:space:]]+language" src/ python/hanna/ docs/  # MUST return 0 results (Rule 37)
# Lockout three-layer test (Rule 34) — see tests/test_integration/test_lockout.py
```

---

## End of RULES.md

Changes to this document require a substrate-level decision and must be ratified in `docs/DECISIONS.md` before merge.
