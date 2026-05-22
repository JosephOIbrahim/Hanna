# Hanna — Conventions

Conventions resolved across sessions. Each entry cites the session that surfaced it.

---

## 1. Test layout — hybrid

**Resolution of:** Session 01 §C.5 (open question on test layout).
**Status:** Resolved 2026-05-13.

### The rule

Hanna's test tree uses **two layouts side by side**, picked per file:

- **Mirror-tree** — applies to genuinely new Hanna components. Test file path mirrors the source file path under `tests/`.
- **Sprint-keyed** — applies to patterns cloned from Harlo where Harlo's lived convention is sprint-keyed. Test file lives in the sprint folder Harlo would have placed it in.
- **When in doubt:** mirror-tree by default.

### Which applies to what

| Hanna file | Convention | Test path |
|---|---|---|
| `src/computations/compute_producer_phase.py` | mirror-tree | `tests/computations/test_compute_producer_phase.py` |
| `src/computations/compute_brief_priority.py` | mirror-tree | `tests/computations/test_compute_brief_priority.py` |
| `src/computations/compute_forcing_function.py` | mirror-tree | `tests/computations/test_compute_forcing_function.py` |
| `src/computations/compute_formation_readiness.py` | mirror-tree | `tests/computations/test_compute_formation_readiness.py` |
| ~~`src/delegate_producer.py`~~ | **Cut per [D008.1](DECISIONS.md)** — no delegate ships; layer 2 collapsed into layer 3 per-tool lockout | n/a |
| `src/harlo_bridge.py` | mirror-tree | `tests/test_harlo_bridge.py` |
| `src/octavius_bridge.py` | mirror-tree | `tests/test_octavius_bridge.py` |
| `python/hanna/mcp_server.py` | subsystem-keyed (sprint convention) | `tests/test_mcp/test_*.py` per tool |
| ~~`/hanna/*` stage prim authoring~~ | **Cut per [D008.2](DECISIONS.md)** — persistence is SQLite-only at `data/hanna.sqlite` | n/a |
| Cross-layer lockout integration | subsystem-keyed | `tests/test_integration/test_lockout.py` |

The two struck-through rows are preserved for historical context; if the L6 `mcp_tools` lane reorganizes the test surface, this table is re-resolved per CONVENTIONS hygiene (cite the session that ratified the new entry).

### Reasoning

Two precedents from Session 01:

- **Harlo's lived test convention is sprint-keyed.** `tests/test_sprint1/test_cogexec.py` holds seven different computation tests in one file with one `TestClass` per computation, ≥3 cases per class — docstring at file head asserts "Minimum 3 test cases per computation" (Session 01 §A.3, citing `tests/test_sprint1/test_cogexec.py:4`). Other Harlo test directories are keyed to subsystem (`test_mcp/`, `test_coach/`, `test_hot_store/`), not to source file.
- **Blueprint §14 prescribes mirror-tree.** "Mirror tree under `tests/`" is written into the convention spec for Hanna.

The hybrid resolution: **honor mirror-tree for the parts of Hanna that are new** (computations, the producer delegate, the bridges — these are the things the blueprint actively prescribes). **Honor sprint/subsystem-keyed for the parts that wrap subsystems Harlo already organized that way** (MCP server, stage, integration tests). This minimizes friction for engineers who came in from Harlo and gives new Hanna code the clarity of file-to-file mapping.

### Minimum case count

Per Harlo's precedent (`tests/test_sprint1/test_cogexec.py:4`), **every computation has ≥3 test cases**, organized as one `TestClass` per computation regardless of which layout the file uses. Mirror-tree files keep this rule per-file. Subsystem-keyed files keep this rule per-`TestClass`.

### Open question parked

If a single Hanna file requires tests that *also* touch a Harlo-cloned subsystem (e.g., a `compute_*` that consumes Harlo bridge state in an integration test), the integration test goes under `tests/test_integration/`, not under the mirror-tree path. Surfaced for revisit if it becomes load-bearing.

---

## 2. Fresh-seed vs. clone state — attribution trailer timing

**Resolution of:** [D004](DECISIONS.md) Clause B.
**Status:** Resolved 2026-05-20.

### The rule

A Hanna source file's attribution-trailer requirement depends on whether the *content* descends from Harlo, not on the file's path:

- **Pure clone** (file's content is derived from a Harlo original, even if structurally adapted): carries the trailer from creation. Examples: `src/harlo_bridge.py`, `src/computations/compute_producer_phase.py` (per [D003](DECISIONS.md)).
- **Fresh seed** (file's content is authored in Hanna with no Harlo ancestor): carries no trailer. Examples: today's `src/schemas.py` (Session 02 minimal seed per `NEXT.md` option (b)); all `tests/**` mirror-tree test files.
- **Fresh-seed-becoming-partial-clone** (file starts fresh but will absorb cloned Harlo content in a later session): the trailer is added **at clone-time, not seed-time** — the session that first lands cloned Harlo content into the file adds the trailer in the same commit.

### The canonical case

`src/schemas.py` was created in Session 02 as a fresh seed with only `ProducerPhase` (per `NEXT.md` option (b)). It is expected to grow as later sessions clone Harlo schemas in. Until that first clone-bearing commit, `schemas.py` carries no trailer. The session that lands the first cloned schema:

1. Adds the trailer as the file's first comment line, immediately above the module docstring.
2. Updates the module docstring to reflect the cloned content.
3. Commits trailer addition + cloned content in a single commit.

### Reasoning

[D003](DECISIONS.md) made the trailer the only required per-file marker for cloned files. The boundary case — files whose Harlo-derivation status changes over time — needed an explicit rule so the reviewer ([D004](DECISIONS.md) Clause A) has an unambiguous audit surface and future sessions don't relitigate. Anchoring the trailer to clone-time (not file-creation-time) matches the trailer's semantic purpose: it marks a file as carrying Harlo-derived content. A file with no Harlo content has nothing to attribute.

### Open question parked

If a file is later refactored such that all Harlo-derived content is replaced by fresh Hanna authoring, does the trailer come off? Surfaced for revisit if it ever happens; default is **keep the trailer** — the file's lineage doesn't change just because all the original lines did.

---

## End of CONVENTIONS.md

Conventions accrete as sessions resolve open questions. Every entry must cite the session that resolved it and the date.
