# Hanna — Architectural Blueprint

**Version:** 0.2.0-audit
**Status:** Pre-scaffold. First-principles audit applied 2026-05-20 (see Audit Log below).
**Provenance:** Cloned from Harlo (`github.com/JosephOIbrahim/Harlo`). Specialized for producer-rhythm.
**License:** Apache 2.0 (matches Harlo).
**Architect:** Joe (Joseph Ibrahim).

---

## Audit Log

### 2026-05-20 — First-principles audit, three lenses, one finding

Three independent agents (inheritance, surface, build sequence) read the v0.1.0 blueprint cold and converged on the same root issue: **this blueprint is speculative architecture against an unverified Harlo edge, with substrate inheritance that is mostly decoration for the actual workload.**

Six findings, integrated into the sections below:

1. **Harlo bridge contract is fictional.** v0.1.0 §9 commits `harlo_bridge.py` to call `read_state` / `read_prediction` / `read_burnout_level`. Harlo's actually-exposed MCP tools are `coach`, `status`, `recall`, `store`, `patterns` (plus three more). The named methods do not exist on the Harlo side. The bridge contract must be reconciled with the real surface before any bridge code ships. **Open decision §12.5.** Affects §9.

2. **Substrate inheritance is over-scoped for the workload.** Hanna's workload is ~10 briefs/week × ~2KB, six events/day on a wall clock. Harlo's substrate (1-bit SDRs, sub-2ms PyO3 hot path, hippocampal apoptosis, Merkle composition, ONNX encoders) was sized for sub-second cognitive memory under continuous load. SQLite + JSON files + `time.time()` dominate on every axis at Hanna's volume. §4 inheritance table now carries Keep / Cut / Review status per item.

3. **The single load-bearing inheritance is the pure-function-over-enum pattern** (the shape of `compute_burst.py` / `compute_momentum.py`). It structurally enforces Rule 36 ("surface, don't decide") because pure enum returns cannot side-effect. Cloning more than this needs concrete justification. §4 marks this as the keep-at-all-costs piece.

4. **"Always-on producer" contradicts MCP-tools-only.** MCP tools fire only when Joe opens a Claude session. A producer that only speaks when spoken to is a logbook. The committed channel (browser-rendered brief) is also the wrong landing zone for a creative director who lives in Houdini and on iPhone. Channel choice is now **open decision §12.6** and must be one-day-tested before another design session.

5. **Input surface is missing.** v0.1.0 is silent on where portfolio state (deadlines, blockers, formation freshness) comes from. Briefs are downstream of state; state has to come from somewhere. **New §5.6 Input surface** sketches the lowest-friction shape (Calendar reads, per-product `.md` files, conversational `hanna_log` / `hanna_block` MCP tools).

6. **Day-zero should ship in one session, not eight.** v0.1.0 §11 day-zero is the *end* of 8+ lane sessions. A smaller end-to-end PoC — call Harlo's real `coach` tool, inline lockout, one stage prim, print one brief — touches every contract in ~80 lines. **§11 now carries this as the primary day-zero**; the long-form version is the post-PoC target.

Audit findings are proposals, not unilateral decisions. Joe ratifies each one before the corresponding code lands. Where a finding is still open, it is named in §12.

**Convergent recommendation:** verify the surface (Harlo edge + delivery channel) before cloning more shape onto it.

---

## Table of Contents

0. [Audit Log](#audit-log) — first-principles audit findings (2026-05-20)
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
- **Venv topology:** v0.1.0 inherited the dual venv (3.12 USD / 3.14 project) verbatim from Harlo. **Audit 2026-05-20:** dual venv is build-system tax for a USD dependency Hanna may not need (see §4 status). Decision parked until §4 USD status resolves.

The clone is a **starting point**, not a destination. Within the first sprint, Hanna diverges:

- Strip cognitive-twin-of-Joe specifics that don't apply to producer rhythm.
- Specialize state machines to producer phenomena.
- Add the producer-specific surface (delegate, computations, MCP tools, stage prims).

After the initial clone commit, the two repos do not share git history.

---

## 4. Substrate inheritance

What carries from Harlo. **Audit 2026-05-20** added per-item status; **D008 2026-05-22** ratified each item whole-batch. The table below reflects the ratified state.

| Component | v0.1.0 plan | Decision (D008) | Rationale |
|---|---|---|---|
| Pure-function computation pattern (`src/computations/*.py`) | Pattern + scaffolding cloned | **Keep — load-bearing** | Structurally enforces Rule 36 ("surface, don't decide") — pure enum returns cannot side-effect. The one inheritance that earns its keep at all costs. |
| FastMCP server + structured-JSON tool returns | Module structure cloned, renamed `hanna/mcp_server.py` | **Keep** | The tool-call substrate is real. Renaming holds. |
| RED-state override (Rule 18) routed via Harlo bridge | Verbatim | **Keep** | Rule 18 actually lives here; the override is non-negotiable. |
| Test discipline (pytest, mirror tree) | Verbatim | **Keep** | Biological-fidelity gates apply selectively — only where the function shape matches. |
| Apache 2.0 headers and `NOTICE` | ~~Updated for Hanna attribution~~ Reversed by D003: no per-file headers. | **Reversed (D003)** | D003 ratified the literal reading of `NOTICE` — Harlo carries zero per-file headers; the clone inherits the absence. One-line attribution trailer at the top of each cloned file. |
| Hydra delegate pattern (`src/delegate_*.py`) | Pattern + base class cloned | **Cut (D008.1)** | Designed for routing tasks across model backends with capability negotiation. Hanna calls Claude. One backend = indirection in search of a purpose. Rule 34's "second layer" collapses into per-tool lockout checks (layer 3); no `HdProducer` file ever ships. |
| USD stage architecture | Verbatim | **Cut (D008.2)** | USD is a stage-composition language for film pipelines. Hanna's corpus is ~10 briefs/week × ~2KB. SQLite + JSON dominates on every axis. D006's Calendar choice corroborates: Calendar IS the stage for v1. |
| Hot tier (FTS5) / warm tier (SDR) / cold tier (USD) | Verbatim | **Cut (D008.3)** | Three-tier storage sized for sub-2ms cognitive recall under continuous load. Hanna's latency budget is "before coffee gets cold." One SQLite file per logical table (briefs, capsules, snapshots) is the whole job. |
| Rust hot path via PyO3 | Inherited via cloned crates | **Cut (D008.4)** | No hot path exists. Hanna runs six events/day on a wall clock. Cloned crates removed from the lane diagram. |
| XGBoost predictor harness | Verbatim. Retrained on producer signals. | **Cut (D008.5)** | Harlo's predictor is currently inactive per SPIKE_HARLO_EDGE_2026-05-20 §4 — nothing live to bootstrap from. A hand-coded heuristic outperforms an undertrained model and ships in 30 minutes. `compute_brief_priority` (L4a) replaces. |
| Dual venv (3.12 USD / 3.14 project) | Verbatim | **Cut (D008.6)** | Falls out automatically once D008.2 USD is cut. Single-venv posture ratified by docs/REVIEW_2026-05-22.md Action 2 + the L2 substrate-hygiene lane. |
| The 33 inviolable rules | **Inherited.** Producer addenda 34–37 added in Session 01.5. | **Review with selective re-adoption (D008.7)** | Rules 34–37 (producer addenda) are Hanna's own and stay. Rules 1–8, 11–17, 19–33 are guardrails for code that doesn't exist in Hanna; non-active rules are annotated as "Not yet load-bearing — applies on the session that lands the constrained component" per RULES.md applicability note + §13 convention. Rule 18 (RED override) is active now via the Harlo bridge's `read_burnout_level`. |

---

## 5. Specializations

What Hanna adds on top of the cloned substrate.

### New pure-function computations

Clone the existing pattern from `src/computations/compute_burst.py` and `compute_momentum.py`:

- `compute_producer_phase.py` — returns one of `MORNING / MIDDAY / EVENING / WEEKLY_MONDAY / WEEKLY_FRIDAY / MONTHLY / FAMILY_LOCKOUT` from timestamp + state.
- `compute_brief_priority.py` — ranks what to surface first in any brief, across portfolio products.
- `compute_forcing_function.py` — which deadlines are advancing into a critical window.
- `compute_formation_readiness.py` — whether to spawn an Octavius formation now or queue it.

### ~~New Hydra delegate~~ — **Cut per D008.1 (2026-05-22)**

> ~~Clone `src/delegate_claude.py`. New file: `src/delegate_producer.py`. Class: `HdProducer`, `supported_tasks = ["synthesis", "coordination", "producer"]`, `latency_max = "interactive"`, `context_budget = "medium"`. Inherits Harlo's RED-state override pattern. Adds `FAMILY_LOCKOUT` as a second override (see §7).~~

D008.1 ratified Cut. Hanna calls Claude (one backend) so the routing-across-backends purpose of the delegate disappears. Rule 34's "second layer" collapses into per-tool lockout checks (layer 3) in the `mcp_tools` lane.

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

### ~~New stage prims~~ — **Cut per D008.2 + D008.3 (2026-05-22)**

> ~~Hanna authors to its own stage, in the `/hanna/*` namespace. USD prim paths: `/hanna/daily/{brief,midday_check,capsule}`, `/hanna/weekly/{30k_monday,harvest_friday}`, `/hanna/monthly/50k_review`, `/hanna/forcing_functions`, `/hanna/formations/{active,history}`, `/hanna/products/{name}`, `/hanna/joe_state_snapshot`.~~

D008.2 ratified Cut on USD stage; D008.3 ratified Cut on three-tier storage. Hanna's persistence is SQLite-only (per L2's substrate-hygiene posture). The functional shape that USD prims served lands as SQLite tables:

- briefs (already at PoC level in `data/hanna.sqlite`, ratified by L4a's BriefPayload schema)
- capsules, formations, products (each one SQLite table; schemas land in L5)
- joe_state_snapshot (a single-row table or in-memory cache — L4a or L6 decides)

D006's Calendar choice corroborates the Cut: Calendar IS the stage for v1 (event-as-prim). Persistent state lives in SQLite, observable via the calendar.

### New bridge modules

- `src/harlo_bridge.py` — read-only MCP client to Harlo for Joe's cognitive state. **Audit 2026-05-20:** see §9 — the v0.1.0 method names (`read_state` / `read_prediction` / `read_burnout_level`) do not match Harlo's actually-exposed MCP tools. Contract reconciliation is a precondition for this module landing. See open decision §12.5.
- `src/octavius_bridge.py` — spawns Octavius formations via subprocess + MCP-over-stdio.

### Input surface (added 2026-05-20 audit)

v0.1.0 of this blueprint was silent on where portfolio state comes from. Briefs and capsules are *outputs* — Hanna cannot compose them without knowing what's in flight, what's blocking, and what deadlines are approaching. The missing surface, in three layers from lowest-friction to highest:

1. **Calendar reads.** Hanna reads Joe's existing calendar(s) over Google Calendar / Apple Calendar APIs and treats dated events tagged with portfolio-product keywords as forcing functions. Read-only. Joe schedules in the tools he already uses.
2. **Per-product Markdown files.** One `.md` per portfolio product, watched by Hanna. Joe edits these directly when state changes ("Moneta parked until Q3", "Synapse waiting on Houdini 21"). File mtime is the freshness signal. Lives at `data/products/{harlo, octavius, moneta, comfy_cozy, ...}.md`.
3. **Conversational MCP tools.** `hanna_log("free text observation")`, `hanna_block("free text blocker on product X")`, `hanna_unblock("product X")` — invoked from any Claude session so a single sentence becomes producer state. These mutate Hanna's own stage only (never Harlo, never Octavius beyond the contract).

Decision on which combination ships first: see open decision §12.7. None of the three is incompatible with the others; the question is sequencing and minimum-viable input set for the first useful brief.

### Producer UI Surface

Web-rendered briefs and capsules. Static HTML mockup at
`web/templates/morning_brief.html` is the design source of truth.

**Audit 2026-05-20:** the delivery channel itself is now an open decision (§12.6). The HTML system survives as design *reference* for any channel that has a layout — but the immediate delivery channel for v1 briefs may be iMessage, `osascript display notification`, a menubar app, or a Calendar event, none of which can host the editorial canvas. **Posture (restraint, no red, deliberate negative space, calm typography) transfers across channels. The 920px asymmetric-gutter kit does not.**

**Phase 1 (current):** Static mockup committed as design reference.
**Phase 2:** Templates parameterized against producer MCP tool output (only if the channel decision lands on browser).
**Phase 3:** Lightweight HTTP surface serving the UI locally (same conditional).

Design system documented in `Hanna/web/README.md` — Pentagram-inspired mono-forward typography (JetBrains Mono + Manrope), muted earth-cool palette with seven functional colors, asymmetric gutter layout, Notion-style structural elements (properties, callouts, mention pills, backlinks).

Family-first lockout, cross-substrate read-only, and Rule 37 inherit to this surface.

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
2. ~~**`HdProducer` delegate routing**~~ — **Cut per [D008.1](docs/DECISIONS.md) 2026-05-22.** Layer 2 collapses into layer 3 (per-tool lockout check); Hanna calls Claude directly, no delegate routing needed. The lockout model is now two active layers (1 + 3).
3. **MCP tool gating** — every tool checks lockout before executing. Lockout returns `LockoutResponse`, not an error. Calling Hanna during family time is a well-defined no-op.

Override path exists for true exceptions but is a deliberate friction surface, requiring an explicit `override_token` with TTL. Not a flag.

Tests verify the two active layers (1 + 3). Bypassing either layer fails CI.

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

> **Audit 2026-05-20 — contract reconciled and ratified.** The spike ran on 2026-05-20; full findings at [`docs/SPIKE_HARLO_EDGE_2026-05-20.md`](docs/SPIKE_HARLO_EDGE_2026-05-20.md). v0.1.0 method names are kept (they describe Hanna's intent correctly); the implementations call Harlo's real surface. Rule 35's reading of the `coach` tool's trace-authoring side effect has been **ratified permissive** in [`docs/DECISIONS.md`](docs/DECISIONS.md) D001. The bridge is unblocked end-to-end.

The reconciled contract:

| Hanna bridge method | Calls Harlo tool | Cost | Returns |
|---|---|---|---|
| `read_state()` | `status` | Cheap — no exchange driven | `v9` block (momentum, burnout, energy, altitude, schedule, allostatic load, dynamics, current prediction slot) |
| `read_burnout_level()` | `status` (projection) | Cheap | `v9.state.burnout` ∈ {`GREEN`, `YELLOW`, `ORANGE`, `RED`} |
| `read_schedule()` *(added by spike)* | `status` (projection) | Cheap | `v9.schedule` = `{kind, override_reason}` |
| `read_prediction()` | `status` (projection — *passive*) | Cheap | `v9.prediction`, or `None` when Harlo's predictor is inactive |
| `drive_coaching_exchange()` *(added by spike, unblocked 2026-05-20 by [DECISIONS D001](docs/DECISIONS.md))* | `coach` | Heavy — authors traces, routes through delegates, may refresh prediction, saves the exchange. **Rate-limited: ≤1 call per brief composition.** | `{coach_block, cognitive_context, v9}` |
| `recall()` / `query_past_experience()` / `patterns()` | identical names | Each advances `exchange_index` only | per Harlo's tool schemas |

**Hard rule (unchanged):** if Harlo is unreachable, Hanna degrades to state-blind mode. Serves cached briefs. Refuses formation requests. Never fabricates state.

**New hard rule from the spike:** Hanna's bridge calls `read_prediction()` defensively — `None` is a valid return when Harlo's predictor flag is `false`. Composition must not require a non-null prediction.

**Forbidden tools (Rule 35):** `store`, `stage_reload`, `resolve_verifications`, `trigger_cognitive_recalibration`. The bridge must never expose methods that call these.

### To Octavius (`src/octavius_bridge.py`)

- `octavius.spawn_formation(grammar, inputs)` → request a formation.
- `octavius.formation_status(id)` → poll active formation.
- `octavius.formation_output(id)` → harvest results.
- **IPC pattern:** subprocess + MCP-over-stdio. Octavius runs in its own venv as a child process. Resolves the dual-venv issue at the boundary.

---

## 10. Build lanes

Hanna is built in lanes. Lanes may be parallelized across Code sessions after the recon and scaffold phases complete.

**Audit 2026-05-20 + D008 2026-05-22 refresh.** `delegate` and `stage` lanes are Cut. `stage` reduces to SQLite tables in `data/hanna.sqlite` (no `/hanna/*` USD prim authoring). The active lane set:

| Lane | Owns | Depends on |
|---|---|---|
| `recon` | Reading existing patterns, producing observation doc | Nothing |
| `computations` | `compute_producer_phase`, `compute_brief_priority`, `compute_forcing_function`, `compute_formation_readiness` | `recon` |
| `harlo_bridge` | Read-only MCP client to Harlo | `recon` |
| `octavius_bridge` | Formation spawn via subprocess + MCP | `recon` |
| `mcp_tools` | All `hanna_*` MCP tools and their lockout gating (Rule 34 layer 3 — collapsed from layer 2 + 3 per D008.1) | `computations`, both bridges |
| `persistence` | SQLite tables in `data/hanna.sqlite` for briefs, capsules, formations, products, joe_state_snapshot. Replaces the cut `stage` lane (D008.2/D008.3). | `computations` |
| `channels` | `src/channels/calendar.py` — D006 Calendar event publishing | `computations`, `mcp_tools` |
| `tests` | Cross-lane integration tests, biological-fidelity gates | All implementation lanes |
| `day_zero` | `scripts/first_hanna_brief.py` end-to-end | All other lanes |

**Cut lanes (D008):** `delegate` (D008.1), `stage` USD-prim-authoring (D008.2/3), Rust hot path (D008.4), XGBoost predictor harness (D008.5), dual venv (D008.6). None of these were built; ratification formalizes their absence from the diagram.

**Revised build order (post-audit + post-D008):**

1. **`harlo_edge_spike`** ✓ (shipped 2026-05-20; full findings at `docs/SPIKE_HARLO_EDGE_2026-05-20.md`).
2. **`first_brief_poc`** ✓ (shipped; `scripts/first_hanna_brief.py` runs end-to-end; Rule 34 layer 1 lands per commit `3cdd516`).
3. `recon` ✓ → `rules` ✓ → `web` ✓ (Phase-1 reference shipped) → `computations` *(Session 03 fills the six non-lockout branches per L3a)* → `harlo_bridge` *(hardening per L3b — D005)* → `persistence` *(inline at the PoC level; promoted to its own lane in L4a/L5)* → `channels` *(L4b — `src/channels/calendar.py` for D006)* → `mcp_tools` *(L6 — `python/hanna/mcp_server.py`)* → `octavius_bridge` *(L7)* → `day_zero` long-form *(post-L6)*.

Lane execution is now governed by `docs/ROADMAP.md` §5's status table; the `/hanna-dispatch-next` harness advances one lane per invocation.

Multi-agent parallelism flips on when three conditions hold *simultaneously*: (a) the Harlo edge is verified end-to-end (not assumed), (b) the brief-write path is exercised once with a real persisted artifact, (c) at least two lanes share no dependency edge in the *live* code (not just on the lane diagram). Before that, parallelism is three agents stubbing against the same unverified contract. **Start single-agent. Promote to multi-agent only after `first_brief_poc` runs green.**

---

## 11. Day-zero deliverable

**Audit 2026-05-20:** day-zero now has two variants. The smaller PoC ships first, in one session, and validates every contract end-to-end before the lanes refactor it. The long-form day-zero remains the target shape — but it is reached *after* the architecture is proven, not as a leap of faith over eight sessions of lane filling.

### 11.1 Primary day-zero — smaller PoC (one session, ~80 lines)

`scripts/first_hanna_brief.py`, written inline with no module decomposition:

1. **Call Harlo's actual `coach` tool** over MCP-stdio (proves the read edge with real tools, not blueprint names). Print what comes back so the contract is observable.
2. **Inline producer phase** — `phase = FAMILY_LOCKOUT if outside Mon–Fri 09:00–17:00 ET else MORNING`. One conditional. Proves the lockout primitive without a clone ceremony.
3. **Author one timestamped artifact.** If §4 USD status resolves Keep: `Usd.Stage.CreateNew("data/stages/hanna.usda")` + `DefinePrim("/hanna/daily/brief", "Scope")` + one attribute. If §4 USD status resolves Cut: one row in `data/hanna.sqlite` `briefs` table. Either way: one persisted artifact, observable on disk.
4. **Print the composed brief** to stdout. Markdown body, two paragraphs max.

Four contracts touched (Harlo read, lockout enforcement, persisted artifact, composed output). Zero MCP server, zero delegate, zero subprocess. If this runs in one session, Hanna is real that session. **Success criterion: the architecture has been validated end-to-end before any lane absorbs it.**

### 11.2 Long-form day-zero (post-PoC target)

`scripts/first_hanna_brief.py`, after the lanes refactor the inline pieces into proper modules:

1. Boot Hanna with `PRODUCER_ENABLED=true`.
2. Read Joe's state from Harlo via `harlo_bridge` *(now backed by the contract proven in §11.1)*.
3. Compute producer phase *(now via `compute_producer_phase`, not inline)*.
4. Compute brief priority across portfolio products.
5. Author `/hanna/daily/brief` to stage with timestamp *(persistence layer per §4 resolution)*.
6. Return the brief as a single composed message to stdout.

This shape is reached when the lanes have absorbed §11.1's inline pieces *and* the §4 inheritance decisions have resolved. Not before.

---

## 12. Open decisions

**Audit 2026-05-20:** the v0.1.0 list (§12.1–4) is preserved unchanged. The audit added §12.5–8, several of which dominate the v0.1.0 items in priority. The four newly-added decisions should resolve *before code lands*; the original four can defer further.

### Original (v0.1.0)

1. **Harlo state staleness TTL** — 5 min default cache, or event-driven via Harlo MCP push notification? *Default: TTL of 5 minutes, polled.* **Spike-resolved 2026-05-20:** `status` is cheap enough that polling at brief-composition cadence (~6× per workday) is trivial. 5-minute TTL stands. Push notification not needed.
2. **Capsule write-through** — does Hanna mirror evening capsules into Harlo's stage as well, or stay private? *Default: capsules stay private to Hanna. No write-through.* Defers indefinitely until capsule shape exists.
3. **Formation authorization** — does `hanna_request_formation` need OOB consent (HMAC + TTL), or is trusted-localhost trust boundary enough? *Default: trusted-localhost. HMAC added when Hanna runs over network.* Defers until Hanna ships over network.
4. **Predictor cold-start** — retrain from scratch on synthetic producer signals, or bootstrap from Harlo's predictor for the first weeks and substitute later? *Default: bootstrap from Harlo's predictor.* **Spike-resolved 2026-05-20:** Harlo's predictor is currently inactive (`v9.engine.predictor: false`, `v9.prediction: null`). There is nothing to bootstrap from. Combined with §4's Cut-pending-ratification status on XGBoost, the practical path is: hand-coded heuristic for forcing-function ranking until Harlo's predictor flips active. Hanna's `read_prediction()` returns `None` cleanly in the meantime.

### Added by 2026-05-20 audit

5. **Harlo bridge contract reconciliation — FULLY RESOLVED 2026-05-20.** Spike ran on 2026-05-20; full findings at [`docs/SPIKE_HARLO_EDGE_2026-05-20.md`](docs/SPIKE_HARLO_EDGE_2026-05-20.md). v0.1.0 method names kept (they correctly describe Hanna's intent); implementations call `status` (cheap reads) and `coach` (heavy drive). New methods `read_schedule` and `drive_coaching_exchange` fall out of the v9 envelope. Rule 35 reading of `coach`'s trace-authoring side effect **ratified permissive** in [`docs/DECISIONS.md`](docs/DECISIONS.md) D001. The full bridge surface — cheap reads and heavy drive — is unblocked. No remaining blockers before bridge code lands.
6. **Delivery channel for v1 briefs — RESOLVED 2026-05-22 via [D006](docs/DECISIONS.md).** Hanna's v1 delivery channel is a **dedicated `Hanna` iCloud calendar with 0-minute anchor events at rhythm times**, brief body in the event notes. Full reasoning in [D006](docs/DECISIONS.md). The 3-day behavioral test originally proposed (the §12.6 default) was skipped in favor of first-principles reasoning (non-interruption + cross-device + persistence + posture fit with Rule 36 "surface, don't decide"); D006 reverses if 30-day post-implementation observation shows the choice was wrong. Implementation lands in a future MoE dispatch at `src/channels/calendar.py`. The "always-on producer" framing at [`README.md`](README.md):7 is now operationalized: briefs land in Joe's calendar regardless of whether a Claude session is open.
7. **Input surface — minimum viable set — RESOLVED 2026-05-22 via [D007](docs/DECISIONS.md) (whole-batch ratification).** Briefs can't compose without inputs. Three candidate input layers (§5.6): Calendar reads, per-product `.md` files, conversational `hanna_log` / `hanna_block` MCP tools. The audit's default — per-product `.md` files first — is the ratified MVS per [D007](docs/DECISIONS.md): YAML frontmatter + named sections, initial product set (`harlo`, `octavius`, `moneta`, `comfy_cozy`), six sub-decisions (D007.1–D007.6) ratified at their proposed defaults. Implementation lane: a future MoE dispatch lands `data/products/{name}.md` stubs + a `ProductFile` schema in `src/schemas.py` + the brief-composer rewrite.
8. **§4 inheritance ratification — RESOLVED 2026-05-22 via [D008](docs/DECISIONS.md) (whole-batch ratification).** §4 carries Cut / Review status on seven inherited components (Hydra delegate, USD stage, three-tier storage, Rust hot path, XGBoost, dual venv, the 33 rules). All seven sub-decisions (D008.1–D008.7) ratified whole-batch per [D008](docs/DECISIONS.md): six Cut, one Review with selective re-adoption. The BLUEPRINT §4 table propagation (the "Audit status" column becomes "Decision (D008)" with the ratified value per row) is a deferred hygiene-pass commit per [`docs/REVIEW_2026-05-22.md`](docs/REVIEW_2026-05-22.md) §3.3.

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
- ~~Stage namespace is `/hanna/*`.~~ **Cut per [D008.2](docs/DECISIONS.md) 2026-05-22** — persistence lives in `data/hanna.sqlite` (SQLite tables), not a USD stage.
- ~~Hydra delegate is `HdProducer` (mirrors Harlo's `HdClaude` naming).~~ **Cut per [D008.1](docs/DECISIONS.md) 2026-05-22** — no delegate ships; Hanna calls Claude directly.

### Attribution

Every cloned file carries an attribution trailer comment within the first 20 lines (per [D004](docs/DECISIONS.md) §A):

```python
# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
```

Per [D003](docs/DECISIONS.md), no per-file Apache header is added — Harlo originals carry zero per-file headers, and the clone inherits the absence. License coverage applies via the repo-root `LICENSE` (Apache 2.0) + `NOTICE` files; per Apache §4 the accompanying `LICENSE` + `NOTICE` is sufficient and per-file boilerplate is recommended-not-required. `NOTICE` at repo root credits Harlo as the substrate origin.

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
