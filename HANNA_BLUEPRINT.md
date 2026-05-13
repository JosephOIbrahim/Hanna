# Hanna — Architectural Blueprint

**Version:** 0.1.0-draft
**Status:** Pre-recon. Awaiting Session 1 observations.
**Provenance:** Cloned from Harlo (`github.com/JosephOIbrahim/Harlo`). Specialized for producer-rhythm.
**License:** Apache 2.0 (matches Harlo).
**Architect:** Joe (Joseph Ibrahim).

---

## Table of Contents

1. [Identity](#1-identity)
2. [Relationship to Harlo](#2-relationship-to-harlo)
3. [Repo posture](#3-repo-posture)
4. [Substrate inheritance — what carries unchanged](#4-substrate-inheritance)
5. [Specializations — what Hanna adds](#5-specializations)
6. [Boundaries — what Hanna does not do](#6-boundaries)
7. [Family-first as architectural primitive](#7-family-first)
8. [Producer state — what the producer twin tracks](#8-producer-state)
9. [Read edges — Harlo and Octavius](#9-read-edges)
10. [Build lanes](#10-build-lanes)
11. [Day-zero deliverable](#11-day-zero-deliverable)
12. [Open decisions](#12-open-decisions)
13. [Inherited rules and hard prohibitions](#13-inherited-rules)
14. [Naming, attribution, IP conventions](#14-conventions)

---

## 1. Identity

**Hanna is an always-on AI producer for Joe's creative portfolio.**

Hanna surfaces decisions; it does not make them. It runs daily and weekly cadences (morning brief, midday check, evening capsule, Monday 30k, Friday harvest, monthly 50k). It coordinates Octavius formations on-demand when work needs more than one agent. It enforces family-first as a structural constraint, not a setting.

Hanna's contract: **VFX producer to a director.** Visibility into what's in-flight, what's blocking, what's approaching. The director still directs.

---

## 2. Relationship to Harlo

Hanna clones Harlo's substrate because **Harlo's substrate is the right architecture for a producer.** Pure-function state machines, XGBoost prediction window, USD stage, 7-step exchange pipeline, MCP + Hydra delegate patterns — all of it is load-tested across 1,140+ Harlo tests. Cloning is faster, safer, and architecturally more honest than reinventing.

The decisive distinction:

- **Harlo** = cognitive twin of Joe. State machines describe Joe's cognitive state.
- **Hanna** = producer-rhythm twin of the portfolio. Same code patterns. Different subject.

Two twins. Same substrate. Different inputs and outputs.

Hanna **reads** Harlo via MCP to retrieve Joe's cognitive state when composing briefs. Hanna **never writes** to Harlo. Hanna **spawns** Octavius formations when multi-agent execution is needed.

Each substrate stays single-purpose:

- Harlo owns cognitive-state truth.
- Hanna owns producer-rhythm truth.
- Octavius owns multi-agent execution.

---

## 3. Repo posture

- **Repo:** `github.com/JosephOIbrahim/Hanna` (new)
- **Provenance:** initial commit is a clean clone of Harlo. Attribution in `NOTICE`.
- **License:** Apache 2.0.
- **Default branch:** `main`, protected.
- **Feature flag:** `PRODUCER_ENABLED`, mirrors Harlo's `ENGINE_ENABLED` precedent.
- **Branch model:** trunk-based with feature flags. Feature branches for lane-scoped work, merged behind the flag.
- **Venv topology:** dual venv inherited verbatim from Harlo. 3.12 USD venv, 3.14 project venv.

The clone is a **starting point**, not a destination. Within the first sprint, Hanna diverges:

- Strip cognitive-twin-of-Joe specifics that don't apply to producer rhythm.
- Specialize state machines to producer phenomena.
- Add the producer-specific surface (delegate, computations, MCP tools, stage prims).

After the initial clone commit, the two repos do not share git history.

---

## 4. Substrate inheritance

What carries from Harlo unchanged:

| Component | Status |
|---|---|
| Pure-function computation pattern (`src/computations/*.py`) | Pattern + scaffolding cloned |
| Hydra delegate pattern (`src/delegate_*.py`) | Pattern + base class cloned |
| MCP server + tool registration | Module structure cloned, renamed `hanna/mcp_server.py` |
| USD stage architecture | Verbatim |
| Hot tier (FTS5) / warm tier (SDR) / cold tier (USD) | Verbatim |
| XGBoost predictor harness | Verbatim. Retrained on producer signals. |
| Dual venv (3.12 USD / 3.14 project) | Verbatim |
| Test discipline (pytest, mirror tree, biological-fidelity gates) | Verbatim |
| The 33 inviolable rules | **Inherited.** Producer-specific addendum may be added in Session 1 recon. |
| RED-state override | Verbatim. Joe's RED state, read via Harlo bridge, still overrides Hanna. |
| Apache 2.0 headers and `NOTICE` | Updated to reflect Hanna attribution to Harlo. |

---

## 5. Specializations

What Hanna adds on top of the cloned substrate.

### New pure-function computations

Clone the existing pattern from `src/computations/compute_burst.py` and `compute_momentum.py`:

- `compute_producer_phase.py` — returns one of `MORNING / MIDDAY / EVENING / WEEKLY_MONDAY / WEEKLY_FRIDAY / MONTHLY / FAMILY_LOCKOUT` from timestamp + state.
- `compute_brief_priority.py` — ranks what to surface first in any brief, across portfolio products.
- `compute_forcing_function.py` — which deadlines are advancing into a critical window.
- `compute_formation_readiness.py` — whether to spawn an Octavius formation now or queue it.

### New Hydra delegate

Clone `src/delegate_claude.py`. New file: `src/delegate_producer.py`.

- Class: `HdProducer`
- `supported_tasks = ["synthesis", "coordination", "producer"]`
- `latency_max = "interactive"`
- `context_budget = "medium"`

Inherits Harlo's RED-state override pattern. Adds `FAMILY_LOCKOUT` as a second override (see §7).

### New MCP tools

Register in `python/hanna/mcp_server.py` (cloned from `python/cognitive_twin/mcp_server.py`):

```
hanna_morning_brief
hanna_midday_check
hanna_evening_capsule
hanna_monday_30k
hanna_friday_harvest
hanna_monthly_50k
hanna_forcing_function_check
hanna_request_formation
hanna_read_joe_state          (calls Harlo via bridge)
hanna_status                  (own-stage health)
```

Every tool checks lockout state before executing. Lockout returns a structured `LockoutResponse`, not an error.

### New stage prims

Hanna authors to its own stage, in the `/hanna/*` namespace. It never authors to Harlo's stage.

```
/hanna/daily/brief
/hanna/daily/midday_check
/hanna/daily/capsule
/hanna/weekly/30k_monday
/hanna/weekly/harvest_friday
/hanna/monthly/50k_review
/hanna/forcing_functions
/hanna/formations/active
/hanna/formations/history
/hanna/products/{harlo, octavius, moneta, comfy_cozy, ...}
/hanna/joe_state_snapshot     (cached read from Harlo, with TTL)
```

### New bridge modules

- `src/harlo_bridge.py` — read-only MCP client to Harlo for Joe's cognitive state.
- `src/octavius_bridge.py` — spawns Octavius formations via subprocess + MCP-over-stdio.

---

## 6. Boundaries

Hanna does not:

- Store Joe's cognitive state. That is Harlo's job. Hanna caches snapshots only.
- Make decisions. It surfaces them.
- Execute multi-agent work directly. It spawns Octavius formations.
- Modify Harlo or Octavius. Bridge edges are read-only (Harlo) and request-only (Octavius).
- Interrupt during family hours. Enforced structurally, not by setting (§7).
- Raise, generate, or solicit patent topics. **Hard rule, inherited and reinforced.**
- Redesign substrate. Clone-and-specialize only.

---

## 7. Family-first

This is not a config flag. It is a state-machine constraint enforced at three layers:

1. **`compute_producer_phase`** — returns `FAMILY_LOCKOUT` outside Mon–Fri 9–5, regardless of other inputs. No downstream surface generates briefs or formations during lockout.
2. **`HdProducer` delegate routing** — RED-state override is inherited. `FAMILY_LOCKOUT` is the second override. Nothing routes through the delegate during lockout.
3. **MCP tool gating** — every tool checks lockout before executing. Lockout returns `LockoutResponse`, not an error. Calling Hanna during family time is a well-defined no-op.

Override path exists for true exceptions but is a deliberate friction surface, requiring an explicit `override_token` with TTL. Not a flag.

Tests verify all three layers. Bypassing any layer fails CI.

---

## 8. Producer state

Hanna's stage authors time-sampled prims for:

- **Phase** — where in the daily/weekly/monthly rhythm we are.
- **Brief currency** — was today's morning brief surfaced? acknowledged?
- **Capsule completeness** — did last night's session generate a capsule?
- **Forcing function distance** — days until each known deadline.
- **Formation health** — active formations, idle, last contact, last output.
- **Product cadence** — per portfolio product, where in its cycle and what's blocking.
- **Joe-state snapshot** — last read from Harlo, with timestamp for staleness gating.

The XGBoost predictor learns **producer-rhythm** forecasts: when forcing functions tend to slip, when capsule generation tends to fail, when formation requests cluster. Not cognitive-state forecasts (Harlo already does that).

Cold start: open decision in §12. Default is bootstrap from Harlo predictor for the first weeks, substitute Hanna-trained predictor when sufficient signal accumulates.

---

## 9. Read edges

### To Harlo (`src/harlo_bridge.py`)

- `harlo.read_state()` → current cognitive state snapshot. Cached with TTL (default 5 min, open decision §12).
- `harlo.read_prediction()` → XGBoost 3-step forecast.
- `harlo.read_burnout_level()` → cheap, called often before any brief composition.
- **Hard rule:** if Harlo is unreachable, Hanna degrades to state-blind mode. Serves cached briefs. Refuses formation requests. Never fabricates state.

### To Octavius (`src/octavius_bridge.py`)

- `octavius.spawn_formation(grammar, inputs)` → request a formation.
- `octavius.formation_status(id)` → poll active formation.
- `octavius.formation_output(id)` → harvest results.
- **IPC pattern:** subprocess + MCP-over-stdio. Octavius runs in its own venv as a child process. Resolves the dual-venv issue at the boundary.

---

## 10. Build lanes

Hanna is built in lanes. Lanes may be parallelized across Code sessions after the recon and scaffold phases complete.

| Lane | Owns | Depends on |
|---|---|---|
| `recon` | Reading existing patterns, producing observation doc | Nothing |
| `computations` | `compute_producer_phase`, `compute_brief_priority`, `compute_forcing_function`, `compute_formation_readiness` | `recon` |
| `delegate` | `HdProducer` class | `recon`, `computations` |
| `harlo_bridge` | Read-only MCP client to Harlo | `recon` |
| `octavius_bridge` | Formation spawn via subprocess + MCP | `recon` |
| `mcp_tools` | All `hanna_*` MCP tools and their lockout gating | `computations`, `delegate`, both bridges |
| `stage` | `/hanna/*` prim authoring, time-sampling | `recon` |
| `tests` | Cross-lane integration tests, biological-fidelity gates | All implementation lanes |
| `day_zero` | `scripts/first_hanna_brief.py` end-to-end | All other lanes |

Build order: `recon` → scaffold all lanes → fill `computations` + `harlo_bridge` in parallel → fill `delegate` → fill `mcp_tools` → fill `octavius_bridge` → fill `stage` → integrate → `day_zero`.

Single-agent build serializes the lanes. Multi-agent build parallelizes after scaffold. **Start single-agent.**

---

## 11. Day-zero deliverable

`scripts/first_hanna_brief.py`:

1. Boot Hanna with `PRODUCER_ENABLED=true`.
2. Read Joe's state from Harlo via `harlo_bridge`.
3. Compute producer phase.
4. Compute brief priority across portfolio products.
5. Author `/hanna/daily/brief` to stage with timestamp.
6. Return the brief as a single composed message to stdout.

Success criterion: this script runs against a live Harlo session and returns a state-aware brief authored to stage. If this runs, Hanna is real. The rest is iteration.

---

## 12. Open decisions

Smaller list than the inside-Harlo architecture — the new-repo posture resolves several.

1. **Harlo state staleness TTL** — 5 min default cache, or event-driven via Harlo MCP push notification?
2. **Capsule write-through** — does Hanna mirror evening capsules into Harlo's stage as well, or stay private?
3. **Formation authorization** — does `hanna_request_formation` need OOB consent (HMAC + TTL), or is trusted-localhost trust boundary enough?
4. **Predictor cold-start** — retrain from scratch on synthetic producer signals, or bootstrap from Harlo's predictor for the first weeks and substitute later?

Default assumptions if not told (each is reversible later):

1. TTL of 5 minutes, polled.
2. Capsules stay private to Hanna. No write-through.
3. Trusted-localhost. HMAC added when Hanna runs over network.
4. Bootstrap from Harlo's predictor. Substitute at sufficient signal.

---

## 13. Inherited rules

Hanna inherits Harlo's 33 inviolable rules verbatim. Located at `RULES.md` in the repo root (cloned from Harlo).

Producer-specific addendum (subject to Session 1 recon validation):

- **Family-first lockout** enforced at three layers (§7).
- **Cross-substrate writes prohibited.** Hanna never writes to Harlo. Hanna never writes to Octavius outside of formation spawn/poll/harvest contract.
- **Surface, do not decide.** Every output is framed as a surfaced decision, not a directive.
- **Patent topics never raised.** Hard rule. No exceptions.

---

## 14. Conventions

### Naming

- **Hanna** is a personal name, like Harlo. No backronym.
- Files, classes, modules use `hanna_` / `Hanna` prefixes where they mirror Harlo's `harlo_` / `Harlo` patterns.
- Stage namespace is `/hanna/*`.
- Hydra delegate is `HdProducer` (mirrors Harlo's `HdClaude` naming where `Hd` is the Hydra delegate prefix).

### Attribution

Every cloned file retains the Apache 2.0 header and adds a line:

```python
# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
```

`NOTICE` file at repo root credits Harlo as the substrate origin.

### Test discipline

- Mirror tree under `tests/`.
- Every new computation has a unit test before the next computation begins.
- Biological-fidelity gates inherited from Harlo apply where the function shape matches.
- Family-first lockout has dedicated tests at each of the three enforcement layers.

### Doc discipline

- Every lane updates a section of the repo README.
- Session-level recon docs live under `docs/SESSION_NN_*.md`.
- Open decisions track in `docs/DECISIONS.md` with status (open / defaulted / resolved).

---

## End of blueprint

Session 1 (recon) reads this document, plus the cloned Harlo source, and produces `docs/SESSION_01_RECON.md` before any code is written.
