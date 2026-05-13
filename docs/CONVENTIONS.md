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
| `src/delegate_producer.py` | mirror-tree | `tests/test_delegate_producer.py` |
| `src/harlo_bridge.py` | mirror-tree | `tests/test_harlo_bridge.py` |
| `src/octavius_bridge.py` | mirror-tree | `tests/test_octavius_bridge.py` |
| `python/hanna/mcp_server.py` | subsystem-keyed (sprint convention) | `tests/test_mcp/test_*.py` per tool |
| `/hanna/*` stage prim authoring | subsystem-keyed | `tests/test_stage/test_*.py` per prim group |
| Cross-layer lockout integration | subsystem-keyed | `tests/test_integration/test_lockout.py` |

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

## End of CONVENTIONS.md

Conventions accrete as sessions resolve open questions. Every entry must cite the session that resolved it and the date.
