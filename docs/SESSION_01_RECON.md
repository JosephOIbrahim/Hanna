# Session 01 — Recon Observations

**Branch:** `session-01-recon`
**Blueprint version:** `HANNA_BLUEPRINT.md` v0.1.0-draft
**Mode:** Read-only across `/Users/rustybeard/Code/Harlo`. No production code authored. No edits to Harlo, Octavius, or any sibling repo.
**Session date:** 2026-05-13.
**Blocker resolutions (recorded for audit):** (1) `RULES.md` path #2 — rules will be extracted from Harlo's distributed sources in a follow-on, see §G. (2) Family-first lockout overridden by explicit signal at session start. (3) `git init` performed before doc write.

---

## §A — Patterns observed

### A.1 `HANNA_BLUEPRINT.md` (canonical `BLUEPRINT.md`, renamed)

The single file present in Hanna at session start. Section structure is 14 numbered chapters with explicit clone provenance in §2 and §3, an inheritance table in §4, a specializations list in §5, lane decomposition in §10, a day-zero deliverable in §11, four open decisions with defaults in §12. The blueprint is **prescriptive about substrate inheritance and proscriptive about boundaries** — §6 lists what Hanna does not do. Cited throughout below.

### A.2 `RULES.md` — absent from Harlo

The blueprint at `HANNA_BLUEPRINT.md:290` claims `RULES.md` is cloned from Harlo. **No such file exists in `/Users/rustybeard/Code/Harlo` or anywhere under it.** What does exist: 12 distinct "Commandments" (1–12, found via `grep -roE 'Commandment[[:space:]]+[0-9]+' /Users/rustybeard/Code/Harlo`), referenced across `CHANGELOG.md`, `design/mile_2_phase_*.md`, `verify/mile_*_crucible.md`, plus a few inline in source (e.g. `src/computations/compute_momentum.py:5` cites "Commandment 2", line 41 cites "Commandment 7"). Joe selected path #2 — extract the de facto rule set into a canonical doc — handled in §G below; recon proceeds without it.

### A.3 `src/computations/compute_burst.py`

Pure function, 63 lines (`compute_burst.py:1-63`).

- **Signature shape:** `(authored: CognitiveObservation, prev_dynamics: DynamicsBlock, **thresholds: float = defaults) -> BurstPhase` (`compute_burst.py:12-19`). Inputs are a current authored observation + previous state block + tunable thresholds as kwargs with literal defaults inline. Return is a single enum value.
- **Return contract:** total function over the input space — every code path returns a `BurstPhase`. Final line `return prev_burst` (`compute_burst.py:62`) covers the unmatched case rather than raising.
- **Error handling:** none. No try/except, no validation, no logging. Invariants are enforced by the schema layer upstream; the function trusts its inputs. Type contracts are enforced statically via `__future__ annotations` + dataclass schemas in `src/schemas.py`.
- **State machine integration:** the function is the entire state machine. The transition table is documented in the docstring (`compute_burst.py:20-28`) and implemented as a flat sequence of guard clauses with explicit ordering — exit conditions first, then degradation, then promotion. No internal state. The "Pure function. NO internal counters" rule is restated in `compute_momentum.py:3-4`.
- **Test layout:** tests for `compute_burst` and `compute_momentum` both live in `tests/test_sprint1/test_cogexec.py` (sole hit for `compute_burst|compute_momentum` across `tests/`). One `TestComputeBurst` / `TestComputeMomentum` class per computation, ≥3 cases per class — docstring at the test file head asserts "Minimum 3 test cases per computation" (`tests/test_sprint1/test_cogexec.py:4`). **Note: this is a sprint-keyed layout, not a mirror-tree layout. Blueprint §14 says mirror-tree. Divergence — see §C.5.**

### A.4 `src/computations/compute_momentum.py`

Same pattern as `compute_burst.py`. Pure function, 78 lines.

- **Signature shape:** `(authored, prev_state, **threshold_kwargs) -> Momentum` (`compute_momentum.py:18-25`). Identical contract shape to burst — different state block (`StateBlock` vs `DynamicsBlock`) and different enum return.
- **Return contract & error handling:** identical to burst — total function, no exceptions, trust-the-schema.
- **State machine:** transition rules in docstring (`compute_momentum.py:27-36`). Two important specializations: (a) **RED-state override is enforced at the computation level** (`compute_momentum.py:41-43`): `if burnout == Burnout.RED or prev_state.burnout == Burnout.RED: return Momentum.CRASHED`. (b) **Degradation paths** with `max(prev_momentum - 1, COLD_START)` for frustration or low coherence (`compute_momentum.py:50-54`) — one-step-down rather than instant crash for sub-RED signals. Hanna's `compute_producer_phase` will need an analogous lockout override.
- **Test layout:** same file as burst — `tests/test_sprint1/test_cogexec.py`, dedicated `TestComputeMomentum` class with ≥3 cases including the `CRASHED → COLD_START` baseline (`tests/test_sprint1/test_cogexec.py:76-80`).

### A.5 `src/delegate_claude.py` (the Hydra delegate pattern)

Class `HdClaude(HdCognitiveDelegate)`, 116 lines.

- **Interface:** five required methods — `get_delegate_id`, `get_capabilities`, `sync`, `execute`, `commit_resources` (`delegate_claude.py:40-76`). Base class is `HdCognitiveDelegate` in `src/delegate_base.py` (not opened in this recon — flagged below).
- **Capabilities object:** `DelegateCapabilities(delegate_id, supported_tasks, latency_class, context_window, compression_factor)` (`delegate_claude.py:43-53`). The blueprint's `HdProducer` adds `latency_max="interactive"` and `context_budget="medium"` — these may need to be mapped onto `latency_class` and `context_window` to match the existing dataclass, unless `DelegateCapabilities` is extended. Schema confirmation pending in §C.
- **Execution contract:** `execute(task)` returns `DelegateResult(response, proposed_mutations, observation_data, tokens_used)` (`delegate_claude.py:64-72`). Crucially, the delegate **does not act** — it composes enriched context for the actor (Claude itself) to reason over, and proposes mutations the caller may commit via `commit_resources` (`delegate_claude.py:74-76`). This shape is directly portable to `HdProducer`: surface decisions, do not make them (blueprint §13).
- **Error handling:** none in the visible delegate body — same trust-the-caller posture as the computations. State-mutation routing happens through `proposed_mutations` (`delegate_claude.py:102-107`) rather than direct side effects.
- **RED override location — open question.** The blueprint claims the delegate "inherits Harlo's RED-state override pattern" (§5). The visible RED override in this codebase is at `compute_momentum.py:41-43`, not in the delegate. There may be additional RED handling in `delegate_base.py` or in the registry that dispatches to delegates. Confirmed-or-falsified in §C.6.
- **Test layout:** not searched in this pass; flagging for scaffold session.

### A.6 `python/harlo/mcp_server.py` (the MCP tool registration pattern)

The path differs from the blueprint's `python/cognitive_twin/mcp_server.py` — package was renamed `cognitive_twin → harlo`. File present and current. 643 lines, FastMCP-based.

- **Server construction:** `server = FastMCP(name="harlo", instructions=...)` at module level (`mcp_server.py:212-221`). Instructions string is human-readable description of tool purposes and includes a tone rule: "In user-facing prose, refer to 'Harlo' — never the tool names" (`mcp_server.py:218-220`).
- **Tool registration:** decorator-based — `@server.tool(name="recall")` or `@server.tool()` (name inferred). Eight visible registrations at lines 229, 264, 326, 391, 438, 467, 506, 550, 571.
- **Per-tool shape:** typed function signature with default kwargs, docstring serves as the tool description for Claude. Body pattern is uniform: (1) `_ensure_data_dir()` (`mcp_server.py:242`), (2) `enrichment = _enrich(tool_name, tool_input)` to push the call through the v9 cognitive engine and advance `exchange_index` (`mcp_server.py:104-120`, called at 243, 277, etc.), (3) try-block doing the actual tool work, (4) JSON-stringified response with a `status` field of `"ok"` or `"error"` and the enrichment merged in via `response.update(_v9_block(enrichment))` (`mcp_server.py:258-261, 298-301`).
- **Error handling:** each tool wraps its body in `try/except` and returns `json.dumps({"status": "error", "error": str(e)})`. **Errors never raise out of the tool — they become structured responses.** This is the pattern Hanna's `LockoutResponse` will follow (blueprint §5: "Lockout returns a structured LockoutResponse, not an error").
- **Lazy singletons + locks:** `_engine` initialized once per process with a sticky-False sentinel on failure (`mcp_server.py:70-101`); `_engine_lock` guards init; `_exchange_lock` serializes USD writes because "`pxr.Usd.Stage` writes are not thread-safe; `exchange_index` must be monotonic" (`mcp_server.py:36-42`). `_hot_store`, `_injection_store` follow the same lazy-singleton pattern (`mcp_server.py:304-323`).
- **Test layout:** `tests/test_mcp/` exists per the top-level `ls` (one of 30+ test directories). Mirror-tree-ish but keyed to subsystem, not file. Same divergence as §C.5.

### A.7 `src/cognitive_stage.py` (the stage-authoring example)

Picked over `stage_factory.py` (36 lines, too thin). 345 lines.

- **Construction:** `Usd.Stage.Open(root_path)` if the `.usda` exists, else `Usd.Stage.CreateNew(root_path)` then `_init_hierarchy()` then `GetRootLayer().Save()` (`cognitive_stage.py:70-76`). On-disk root is `data/stages/harlo.usda`; the file `data/stages/cognitive_twin.usda` exists but is stale (post-rename artifact, flagged in `design/mile_2_phase_2_scout_src.md`).
- **Hierarchy:** `_init_hierarchy` defines a fixed prim set via `DefinePrim(path, "Scope")` — `/state`, `/state/momentum`, `/state/burnout`, `/state/energy`, `/state/injection`, `/state/allostatic`, `/routing`, `/sessions`, `/delegates`, `/prediction`, `/memory`, `/projects` (`cognitive_stage.py:92-101`). **Directly portable shape for `/hanna/*` namespace** in blueprint §5.
- **Time sampling:** `author(prim_path, exchange_index, value)` writes a JSON-serialized value to a `data` attribute at `Usd.TimeCode(float(exchange_index))` (`cognitive_stage.py:109-117`). Exchange-index as time code is the consistent convention — this is what blueprint §8 ("time-sampled prims") means in practice.
- **Sublayer pattern:** delegate state lives on separate `.usda` files in `data/stages/delegates/`, composed via USD sublayer mechanics (`cognitive_stage.py:42, 67-69`). The `/schedule/` skeleton is parked on its own sublayer specifically so the daemon's root save doesn't clobber external edits (`cognitive_stage.py:86-90`). Useful precedent: **Hanna's `/hanna/joe_state_snapshot` should live on its own sublayer if Harlo writes to it via the read-bridge mechanism**, so the staleness-cache doesn't get clobbered.
- **Error handling:** none at the stage boundary. The class is a drop-in for `MockUsdStage` and matches its interface (`cognitive_stage.py:6, 26-31`).
- **Tests:** `tests/test_*` has no `test_cognitive_stage.py` matching this filename directly — likely covered under `tests/test_integration/` or one of the sprint test buckets. Scope-deferred to scaffold session.

---

## §B — Clone targets (one per Hanna specialization in blueprint §5)

```
compute_producer_phase.py
  ├─ clones:    src/computations/compute_burst.py
  ├─ rationale: total-function-over-enum pattern with timestamp + state inputs;
  │              transition rules documented in docstring as a flat table;
  │              tunable thresholds as kwargs.
  └─ divergence: enum is { MORNING, MIDDAY, EVENING, WEEKLY_MONDAY,
                            WEEKLY_FRIDAY, MONTHLY, FAMILY_LOCKOUT };
                 the FAMILY_LOCKOUT override at this layer is the parallel of
                 burst's "coherence drop breaks burst" exit
                 (compute_burst.py:39-41).

compute_brief_priority.py
  ├─ clones:    src/computations/compute_momentum.py
  ├─ rationale: ranking over a small enum with degradation paths
  │              (max(prev - 1, ...) pattern at compute_momentum.py:50-54)
  │              maps cleanly to priority degradation when a product cycle
  │              slips.
  └─ divergence: input shape is a list of products × cycle positions, not a
                 single observation. The compute body becomes a stable-sort
                 over a priority enum, rather than a single transition.

compute_forcing_function.py
  ├─ clones:    src/computations/compute_burst.py
  ├─ rationale: threshold-crossing detector (deadline distance in days vs.
  │              critical-window threshold) — same shape as
  │              "velocity ≥ burst_detect_velocity" check (compute_burst.py:45).
  └─ divergence: returns a list of forcing functions in the critical window,
                 not a single enum. If we want to preserve the
                 total-function-over-enum shape, this could instead be
                 split into a per-deadline boolean and a list comprehension
                 at the caller.

compute_formation_readiness.py
  ├─ clones:    src/computations/compute_momentum.py
  ├─ rationale: gated state machine (RED-blocks-everything precedent at
  │              compute_momentum.py:41-43) maps to family-lockout-blocks-
  │              spawn and joe-state-RED-blocks-spawn.
  └─ divergence: output enum is { READY, QUEUE, REFUSE_LOCKOUT, REFUSE_RED }.
                 Inherits both override sources (RED + lockout).

delegate_producer.py — class HdProducer
  ├─ clones:    src/delegate_claude.py
  ├─ rationale: surfaces enriched context, does not act; five-method
  │              interface (get_delegate_id, get_capabilities, sync, execute,
  │              commit_resources) maps verbatim.
  └─ divergence: capabilities are { synthesis, coordination, producer }
                 (blueprint §5). _build_coach_block becomes _build_producer_brief
                 — same structural-text-block shape, different fields:
                 phase, brief currency, forcing functions, formation health.
                 RED-override AND lockout-override gating — see §C.6.

python/hanna/mcp_server.py
  ├─ clones:    python/harlo/mcp_server.py (note: blueprint path
  │              "python/cognitive_twin/" is stale — renamed to "harlo/").
  ├─ rationale: FastMCP server + decorator-registered tools + try/except-
  │              returns-JSON pattern is exactly what's needed.
  └─ divergence: ten new tools (blueprint §5). Every tool gains a
                 _lockout_check() preflight returning LockoutResponse; the
                 try-block pattern at mcp_server.py:245-261 becomes a
                 lockout-then-try pattern. server instructions string
                 reframed for "Hanna, never the tool names."

/hanna/* stage prims
  ├─ clones:    src/cognitive_stage.py (the prim-hierarchy + time-sampling
  │              pattern; not the file wholesale — Hanna writes to its own
  │              stage)
  ├─ rationale: DefinePrim(path, "Scope") for the namespace skeleton,
  │              author(prim_path, exchange_index, value) for time-sampled
  │              state, sublayer-on-disk for state that an external system
  │              might write through.
  └─ divergence: separate stage file (data/stages/hanna.usda), separate
                 hierarchy (/hanna/daily/*, /hanna/weekly/*, /hanna/monthly/*,
                 /hanna/forcing_functions, /hanna/formations/*,
                 /hanna/products/*, /hanna/joe_state_snapshot). The
                 joe_state_snapshot prim parked on its own sublayer is the
                 right pattern for the read-bridge cache (precedent:
                 cognitive_stage.py:86-90 for /schedule/).

src/harlo_bridge.py
  └─ NO DIRECT HARLO ANALOG. See §C.3.

src/octavius_bridge.py
  └─ NO DIRECT HARLO ANALOG. See §C.2.
```

---

## §C — Gaps surfaced

### C.1 — Rules inheritance is unresolved at the substrate

**Status:** path #2 selected; extraction is its own deliverable. See §G.

### C.2 — Octavius IPC (subprocess + MCP-over-stdio) has no Harlo precedent

Blueprint §9 specifies the Octavius bridge runs Octavius "in its own venv as a child process" via "subprocess + MCP-over-stdio." Harlo's `mcp_server.py` is the **server side** of this transport. There is no `src/*_client.py` or `python/harlo/*_client.py` that demonstrates the **client side** of an MCP-over-stdio handshake against another subprocess. The pattern needs to be designed, not cloned.

**Question for Joe:** Should the Octavius bridge be sketched as a small standalone PoC in Session 2 before being integrated into the `octavius_bridge` lane? An hour spent on a one-tool round-trip would de-risk the entire formation-spawn surface. Or wait for Octavius to be further along first.

### C.3 — Harlo bridge is a read-only MCP client; same shape gap as C.2

`src/harlo_bridge.py` calls a running Harlo MCP server from inside Hanna. Same transport question as Octavius — no client-side precedent in Harlo. The functions are simpler (read-only, three calls in blueprint §9: `read_state`, `read_prediction`, `read_burnout_level`), but they still need a working MCP-client wrapper.

**Question for Joe:** Is there an existing MCP client implementation in the Harlo dependency graph (e.g. inside the `mcp` Python package or anywhere in `forge/`, `harness/`, `crates/`) that should be the reference? Or do we write from scratch against the MCP spec.

### C.4 — `LockoutResponse` has no Harlo analog

Blueprint §5 and §7 require a structured `LockoutResponse` returned in place of tool output during family hours. Harlo's MCP error pattern returns `{"status": "error", "error": str(e)}` (`mcp_server.py:260-261`); there is no precedent for a structured non-error refusal. The new shape needs design — at minimum `{"status": "lockout", "phase": "FAMILY_LOCKOUT", "next_window_iso": "...", "override_path": "..."}`.

**Question for Joe:** Is `status: "lockout"` the right new top-level state, or should it ride alongside `status: "ok"` with a `lockout: true` field? The former is more discoverable; the latter is non-breaking for any caller that already only inspects `status`.

### C.5 — Test layout: blueprint says mirror-tree, Harlo organizes by sprint

Blueprint §14: "Mirror tree under `tests/`." Harlo reality: `tests/test_sprint1/test_cogexec.py` holds tests for seven different computations (burst, momentum, burnout, energy, injection_gain, context_budget, allostasis), one `TestClass` per computation, ≥3 cases per class (`tests/test_sprint1/test_cogexec.py:1-7`). Other Harlo test directories are keyed to subsystem (`test_mcp/`, `test_coach/`, `test_hot_store/`), not to file.

**Question for Joe:** Which convention does Hanna adopt? Three options: (1) honor blueprint §14 as written — one test file per source file under `tests/` mirroring the `src/` tree, diverging from Harlo's living convention; (2) follow Harlo's lived convention — sprint-keyed buckets with one test class per computation; (3) hybrid — mirror-tree for the new `src/computations/` and `src/delegate_*.py` because they are new code, but follow Harlo's `test_<subsystem>/` for `tests/test_mcp/`, `tests/test_stage/`, `tests/test_bridge/`. I lean #3 — mirror-tree where the source files are pure and self-contained (computations, delegates), subsystem-keyed where the surface is wider (MCP, stage, bridges).

### C.6 — RED-state override location is ambiguous

Blueprint §5 says `HdProducer` "inherits Harlo's RED-state override pattern." The RED override I can verify is at the computation level (`compute_momentum.py:41-43`). The delegate (`delegate_claude.py:25-116`) shows no RED check. There may be RED handling in `delegate_base.py` (not opened in recon, to stay inside the 7-file budget) or in the dispatch path between MCP tool and delegate.

**Question for Joe:** Should Session 2 begin with a 5-minute read of `src/delegate_base.py` and `src/delegate_registry.py` to confirm where RED-override lives in the dispatch path? If it's at the registry level, the blueprint sentence is correct and inheritance is structural. If it's not present at the delegate layer at all, then `HdProducer` may be the first delegate to need an explicit dual override (RED + lockout) inside its own `execute()` — which is a divergence the blueprint should record.

---

## §D — Open-decision impact (blueprint §12)

### D.1 — Harlo state staleness TTL (5 min cache vs. event-driven)

- **First needed in:** `harlo_bridge` lane (the moment `harlo.read_state()` is implemented). Affects `mcp_tools` indirectly.
- **Default assumed:** 5-minute cache, polled (per blueprint §12).
- **Lives in:** `src/harlo_bridge.py` — a module-level constant `STATE_CACHE_TTL_SEC = 300` plus a small `_cache: dict[str, tuple[float, Any]]` keyed by call name. Flippable to event-driven by replacing the constant with a subscription pattern; the cache structure stays.
- **Caveat:** burnout reads should ignore the cache (or use a much shorter TTL) so RED-override semantics are preserved. Captured in §E.3.

### D.2 — Capsule write-through to Harlo (mirror vs. private)

- **First needed in:** `mcp_tools` lane, specifically `hanna_evening_capsule`.
- **Default assumed:** private to Hanna. No write-through (per blueprint §12, reinforced by §13 "Hanna never writes to Harlo").
- **Lives in:** the body of `hanna_evening_capsule` in `python/hanna/mcp_server.py`. Flipping to write-through means adding one call to a hypothetical `harlo_bridge.mirror_capsule(...)` — but that bridge function would itself be a **write** to Harlo, which §13 forbids. Flipping this default in the future would therefore also require relaxing the §13 "never writes to Harlo" rule. **The two are coupled — flag in `docs/DECISIONS.md` when it's created.**

### D.3 — Formation authorization (HMAC+TTL vs. trusted-localhost)

- **First needed in:** `octavius_bridge` lane, specifically the body of `octavius.spawn_formation`.
- **Default assumed:** trusted-localhost. HMAC added when Hanna runs over network (per blueprint §12).
- **Lives in:** `src/octavius_bridge.py` — an `_authorize(request)` function gated by a module-level boolean `REQUIRE_HMAC = False`. Flipping for network deployment is a one-line change plus an HMAC implementation block in the same file.

### D.4 — Predictor cold-start (synthetic-from-scratch vs. bootstrap-from-Harlo)

- **First needed in:** whichever lane first calls the predictor — based on blueprint §11 day-zero deliverable, this is **not** Session 2 (day-zero only needs phase + brief-priority + stage authoring). Likely surfaces in `mcp_tools` when `hanna_forcing_function_check` first ranks deadlines.
- **Default assumed:** bootstrap from Harlo's predictor, substitute Hanna-trained when sufficient signal accumulates (per blueprint §12).
- **Lives in:** `src/harlo_bridge.py::read_prediction()` initially — Hanna calls Harlo's predictor through the bridge. The substitution happens by adding `src/predictor.py` later and switching the call site in `mcp_tools` to prefer the local predictor when its confidence exceeds a threshold. **The flip is at the call site, not the bridge** — preserves the bridge's read-only contract.

---

## §E — Risk register (top 3, ranked by `(blast × likelihood) / mitigation_cost`)

### E.1 — Octavius IPC pattern has no Harlo precedent

- **Failure mode:** the formation-spawn surface (the most ambitious part of Hanna) blocks because the subprocess + MCP-over-stdio handshake is being designed and debugged at the same time as the higher-level `hanna_request_formation` tool. Each layer can mask the other's bugs.
- **Lanes affected:** `octavius_bridge` directly; `mcp_tools` indirectly (the `hanna_request_formation` tool); `day_zero` if formations are part of the first brief.
- **Mitigation:** spike a one-tool round-trip PoC in Session 2 or 3 — Hanna-side client launches a stub Octavius MCP server subprocess, calls one tool, harvests the response. Confirms the transport before any formation grammar work.

### E.2 — Family-first lockout enforced at three layers (blueprint §7) drifts silently

- **Failure mode:** §7 requires lockout enforcement at three layers — computation (`compute_producer_phase` returns `FAMILY_LOCKOUT`), delegate (`HdProducer` second override), and MCP tool gating. A future refactor changes one layer's behavior without changing the others, and the lockout starts leaking. Tests at each layer pass independently; the integration breaks.
- **Lanes affected:** `computations`, `delegate`, `mcp_tools` — i.e. most of the surface.
- **Mitigation:** an integration test (under `tests/test_integration/test_lockout.py` or equivalent) that drives a single mock-time scenario into all three layers and asserts every layer refuses. Make it part of the day-zero deliverable's success criterion, not a follow-on.

### E.3 — Joe-state staleness masks RED-override

- **Failure mode:** D.1 default is a 5-minute TTL on Harlo state. If Joe transitions to RED at minute 0 of a cache window, Hanna composes a brief at minute 4 still reading a sub-RED snapshot, and surfaces a brief that the RED-state override should have blocked.
- **Lanes affected:** `harlo_bridge`, `mcp_tools`.
- **Mitigation:** `harlo_bridge.read_burnout_level()` (blueprint §9 calls it "cheap, called often") bypasses the cache or uses a much shorter TTL (e.g. 15 sec). Every tool that composes user-facing output checks `read_burnout_level()` immediately before composition, regardless of cached state. **Cost is low — a second uncached round-trip per brief — and aligns with §9's stated cheapness.**

(Risks 4–N parked for now: stale `cognitive_twin.usda` file confusion in clone; venv topology mismatch on a fresh Hanna checkout; `DelegateCapabilities` field name mismatch with blueprint's `latency_max`/`context_budget`; FastMCP version drift between Harlo's pinned and Hanna's clone.)

---

## §F — What I'd build first in Session 2

**Scaffold `src/computations/compute_producer_phase.py` cloning `src/computations/compute_burst.py` line-for-line — the function signature, the `ProducerPhase` enum import (which means defining it in `src/schemas.py` first as a sibling to `BurstPhase`), the docstring transition table for `MORNING/MIDDAY/EVENING/WEEKLY_MONDAY/WEEKLY_FRIDAY/MONTHLY/FAMILY_LOCKOUT`, the threshold-kwargs shape — but with every transition body raising `NotImplementedError("Session 3")`. Pair it with the test file stub (`tests/test_sprint1/test_producer_phase.py` if Joe picks Harlo's sprint-keyed convention from §C.5, otherwise `tests/computations/test_compute_producer_phase.py`) containing one `TestComputeProducerPhase` class with three named-but-skipped tests (`@pytest.mark.skip("Session 3")`). The deliverable is two committed files where the shapes are right and the logic is empty — Session 3 fills the bodies. Stop for review before any further computation or any delegate work.**

Concretely: one module, one test file, one schemas update (one new enum, mirroring `BurstPhase`). Roughly 100 lines of net code. Cloneable in well under an hour. Picks the safest computation first (phase is a pure timestamp-driven transition; brief-priority and forcing-function involve external state).

---

## §G — Rules inheritance plan (resolution of blocker #1)

> **Historical note (2026-05-25, Phase 4 doc-drift sweep):** This section's premise — that Harlo's rules live distributed across CLAUDE.md, design/verify docs, and inline `Commandment N` references — was wrong. The 33 inviolable rules existed verbatim in `Harlo/CLAUDE.md` lines 37–194 throughout Session 01. Session 01.5 extracted them directly from that source into `RULES.md` (no Phase-1-extraction-from-distributed-sources was needed). The "Forge Commandments" cataloged below are a separate, parallel discipline layer in Harlo, not the Hanna-inherited rules. §G is preserved unedited below as a session-stamped historical artifact per `state/open_questions.md` q003 / q009; the prose is the recon-time misread, not the live state.

---

Joe selected path #2: rules live distributed across Harlo's `CLAUDE.md`, the design/verify docs, and the inline-`Commandment N` references in source. Recon survey:

- **12 distinct Forge Commandments** referenced (`Commandment 1` through `Commandment 12`), surfaced in `CHANGELOG.md`, six `design/mile_2_phase_*.md` files, four `verify/mile_*_crucible.md` files, and inline at `src/computations/compute_momentum.py:5,41`, `src/cognitive_stage.py:6-9`, plus several other source files. These read as **architect-acting-as-scout discipline rules** — phase ordering, verification gates, retry budgets, subprocess isolation, casing conventions. They are not 33.
- **Harlo's `CLAUDE.md`** at repo root holds additional project-level conventions.
- **`README.md`, `INSTALL.md`, `PATENTS.md`** (recon did not open these in this session — content unverified) likely hold additional rules.
- **Lived practice** — rules implemented in code but not stated in any doc (e.g. "pure functions have no internal counters" is stated in `compute_momentum.py:3-4` but not in any rules doc).

**Proposed two-phase extraction (not done in this session — needs Joe's approval before starting):**

- **Phase 1 (lives in Harlo, not Hanna):** audit `CLAUDE.md`, the 12 Commandments, the design+verify docs, and a grep across `src/` for `"""` rule statements. Consolidate into `/Users/rustybeard/Code/Harlo/RULES.md`. Final count is whatever it is — the "33" is aspirational. Ship as a Harlo PR.
- **Phase 2 (in Hanna):** clone `RULES.md` into Hanna's root verbatim. Append the producer-specific addendum from blueprint §13 (family-first three-layer, cross-substrate-write prohibition, surface-don't-decide, no patent topics). This is a 10-minute task once Phase 1 is done.

**Question for Joe:** is the rules extraction Session 1.5 (own session, Joe reviews `RULES.md` before Session 2 starts) or Session 2.5 (parallel-track while scaffold work proceeds against the assumption that the rules will land before integration)? I'd recommend Session 1.5 — getting `RULES.md` settled before any clone-with-attribution begins avoids retroactive header edits.

---

## End of recon

Six blueprint-required sections (A–F) plus one extension (G) covering the rules-inheritance gap Joe unblocked. Awaiting review before Session 2.
