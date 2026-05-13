# NEXT — for tomorrow-you

## Where you are

- Branch: `session-01.5-rules` (HEAD = `cbe30b5`).
- Branches in repo: `session-01-recon`, `session-01.5-rules`. **No `main` yet.**
- Session 01.5 approved 2026-05-13 17:46 ET. Session 02 starts tomorrow morning.

## Decision parked

**Trunk:** merge `session-01-recon` + `session-01.5-rules` into a `main` branch before Session 02 starts, or branch `session-02-scaffold` directly off `session-01.5-rules` and defer the trunk question? No default — surface to Joe at session start.

## Session 02 first deliverable (per Session 01 §F)

- Clone `Harlo/src/computations/compute_burst.py` → `Hanna/src/computations/compute_producer_phase.py`.
- Define `ProducerPhase` enum in `Hanna/src/schemas.py`.
- Test stub at `Hanna/tests/computations/test_compute_producer_phase.py` (mirror-tree per `docs/CONVENTIONS.md` §1).
- All transition bodies as `NotImplementedError("Session 03")`.
- ~100 lines net. Stop for review.

## Precondition flagged

`src/schemas.py` does not exist in Hanna yet. Session 02 starts by either:

- **(a)** Cloning all of `Harlo/src/schemas.py` and adding `ProducerPhase`, or
- **(b)** Creating a minimal `Hanna/src/schemas.py` with just `ProducerPhase` + only the imports `compute_producer_phase` needs.

Recommend **(b)** — clone-as-needed reduces inherited surface area. Surface to Joe at session start.

## Open questions parked from Session 01 (do not act on; be aware)

- **§C.2** — Octavius IPC PoC (deferred until `octavius_bridge` lane).
- **§C.3** — Harlo MCP-client precedent (deferred until `harlo_bridge` lane).
- **§C.4** — `LockoutResponse` shape (needed before `mcp_tools` lane).
- **§C.6** — RED override in delegate dispatch (needed before `delegate` lane; ~5-min read of `Harlo/src/delegate_base.py` + `delegate_registry.py`).

None of these block Session 02's first deliverable (a computation).

## Staleness flag — needs Joe's call at session start

Session 01 `docs/SESSION_01_RECON.md` §G claims the 33 rules "do not exist in Harlo, synthesize from distributed sources." That's wrong — rules existed in `Harlo/CLAUDE.md` lines 37–194 the whole time. My grep flagged the file but I didn't read in. Session 01.5 extracted from there directly; no synthesis was needed.

Ask Joe at session start: fix `docs/SESSION_01_RECON.md` §G with a correction note (one short paragraph), or leave it as a session-stamped historical artifact?
