# scout-tests — findings.md

**Mode:** critic[red_team]
**Date:** 2026-05-29
**Task:** Audit Hanna's 74-test suite from first principles — coverage gaps, brittle patterns, fixture design, test-quality issues.
**Tests collected (verified):** 74 (5 brief composer + 21 harlo_bridge + 15 schemas + 12 brief_priority + 21 producer_phase).

## Executive summary

The 74-test suite is competent on the per-function unit-test axis (every public computation has its
≥3 cases per CONVENTIONS §1; harlo_bridge has thorough timeout + drainer coverage). But three
structural gaps make the suite weaker than the count suggests:

1. **The round-3 frame-coalescing bug fix has no regression test.** `_recv_buffer` is wired through
   `_read_frame_with_timeout` and `close()` but no test feeds two frames in one read or asserts
   `_recv_buffer` is consumed on the next call. The exact bug from c003 can silently regress.
2. **The `first_hanna_brief.py` PoC is 75% untested.** Only `_portfolio_line` (5 tests) is exercised;
   `_state_line`, `_approaching_line`, `_blockers_line`, `_compose_brief`, `_persist`,
   `_extract_burnout`, `_read_harlo`, `_read_product_files`, and `main()` have zero coverage. No
   end-to-end run, no SQLite persistence assertion, no FAMILY_LOCKOUT early-exit test.
3. **`compute_producer_phase` has 21 tests but misses its own precedence collisions.** Monday-the-1st
   (MONTHLY beats WEEKLY_MONDAY) and Friday-the-1st (MONTHLY beats WEEKLY_FRIDAY) are both unverified;
   no test exercises non-default keyword args; no DST/year-boundary coverage despite the
   `astimezone(_ET)` normalization being the load-bearing line.

---

## BLOCKER findings

### B1 — Frame-coalescing regression test is absent
**Where:** `tests/test_harlo_bridge.py` (entire file) vs `src/harlo_bridge.py:70-71, 320-323, 358-359`.
**Evidence:** `grep -rn "recv_buffer\|frame.coalesc\|two.frame" tests/` returns zero hits. The
`_recv_buffer` field is the entire D005.2 round-3 fix per `docs/DECISIONS.md:486` and `beliefs.md:13`
(c003 cites this exact bug). No test:
  - Feeds two complete frames in one `os.read()` and confirms both `_read_frame` calls succeed.
  - Asserts `_recv_buffer` is populated after a coalesced read and drained on the next call.
  - Verifies `close()` clears `_recv_buffer` (line 99) — relevant if a bridge is reused.
  - Verifies `_recv_buffer` is *not* leaked across compositions if the trailing bytes are partial.
**Impact:** The exact class of bug belief c003 names as "found in round 3" can silently regress and
no test will catch it. This is the highest-leverage gap in the suite.

### B2 — `scripts/first_hanna_brief.py` is a black box from the test surface
**Where:** `tests/test_first_hanna_brief.py` (5 tests, all on `_portfolio_line`).
**Evidence:** The script defines 10 functions; only 1 is tested. Uncovered:
  - `_state_line` — burnout extraction + 3-branch state messaging (unreachable / reachable+burnout /
     reachable+no-burnout).
  - `_extract_burnout` — 4 guard clauses (non-dict, missing v9, missing state, non-str burnout) all
    untested; this is the bridge between `coach()` output shape and the brief body.
  - `_approaching_line` — entry sorting, 3-item truncation, empty-state short-circuit, none-skip on
    missing description+date, `9999-99-99` sort sentinel.
  - `_blockers_line` — empty short-circuit, missing-product skip, multi-blocker join.
  - `_compose_brief` — the actual brief composition; no test asserts brief contains the expected
    sub-renders or honors `phase` in the header.
  - `_persist` — SQLite schema creation, INSERT, transaction commit, `harlo_reachable` flag (0/1)
    encoding. Never exercised in tests.
  - `_read_product_files` — `.private.md` skip, missing-dir return-empty, glob sort.
  - `_read_harlo` — `HarloUnreachable` / `HarloTimeout` → `(False, None)` swallow; success path.
  - `_phase_now` — wrap of compute_producer_phase with wall-clock; ok to skip if mocked.
  - `main` — FAMILY_LOCKOUT early-exit (the explicit `return 0` after print), end-to-end stitching.
**Impact:** The day-zero PoC ships effectively untested. State-blind handling, SQLite persistence,
and FAMILY_LOCKOUT short-circuit are all single points of failure. Belief c003 ("done warrants
critic[verify] before close") applies — these helpers were declared shipped without testing.

### B3 — `compute_producer_phase` precedence collisions untested
**Where:** `tests/computations/test_compute_producer_phase.py` (21 tests) vs
`src/computations/compute_producer_phase.py:32-37`.
**Evidence:** Confirmed by probe:
  - `compute_producer_phase(datetime(2026, 6, 1, 9, 0, tzinfo=_ET), ...)` returns `MONTHLY`, not
    `WEEKLY_MONDAY` — Jun 1 2026 is a Monday at 9am; MONTHLY check (line 32) precedes the weekly
    check (line 34). This precedence is undocumented in the source comment and untested.
  - `compute_producer_phase(datetime(2026, 5, 1, 16, 0, tzinfo=_ET), ...)` returns `MONTHLY` over
    `WEEKLY_FRIDAY` — May 1 2026 is a Friday at 4pm. Same precedence collision, untested.
  - No test exercises any non-default keyword argument (`work_start_hour`, `morning_end_hour`,
    `weekly_monday_hour`, `monthly_day`). All 21 tests use defaults; the parameterization surface
    is asserted nowhere.
**Impact:** A future refactor that swaps the MONTHLY / WEEKLY order in `compute_producer_phase` will
pass all 21 tests but change the production phase emitted on ~24 first-of-month days per year.

---

## MAJOR findings

### M1 — Brittle stderr-drainer timing assertions
**Where:** `tests/test_harlo_bridge.py:259-310` (`TestStderrDrainer`).
**Evidence:** `_wait_until(predicate, timeout=2.0)` polls every 10ms. The test
`test_stderr_drainer_no_deadlock_on_large_write` explicitly notes "an explicit wall-clock bound was
brittle under loaded CI runners" — meaning this is *known* timing-flakey. Three of four drainer
tests rely on the same poll loop; if CI ever runs slower than 2s, they go red without surfacing a
real bug. No test pins down ordering deterministically (e.g., by having the drainer call a flush
hook or using a Queue.Queue with `get(timeout)` semantics).
**Impact:** Latent flake source. The exact pattern your README warns about (timing-dependent
assertions) is reproduced inside the drainer tests.

### M2 — HarloTimeout fallback path (`timeout=None`) is untested
**Where:** `src/harlo_bridge.py:278-281` (`_read_frame` branch on `timeout is None` → blocking).
**Evidence:** No test passes `timeout=None`. `_read_frame_blocking` (lines 283-307) is therefore
entirely uncovered:
  - The `while True: readline` loop.
  - `Content-Length: not-an-int` in blocking mode.
  - Short-body detection: `if len(body) != content_length: raise HarloUnreachable`.
  - JSON decode failure path.
**Impact:** Belief c003 names "HarloTimeout fallback" as a round-3-found latent bug. The fallback
path has six branches and a test count of zero. Any callers that call `_rpc(method, params)`
without `timeout=...` exercise the blocking path in production.

### M3 — Public HarloBridge surface is mostly mocked at `_call_tool`
**Where:** `tests/test_harlo_bridge.py` — methods `read_state`, `read_burnout_level`,
`read_schedule`, `read_prediction`, `recall`, `query_past_experience`, `patterns`,
`drive_coaching_exchange(session_id=...)` are never directly tested.
**Evidence:** `grep -n "read_state\|read_burnout\|read_schedule\|read_prediction\|recall\|patterns\|query_past"
tests/test_harlo_bridge.py` returns zero hits. Only `_coach` and `drive_coaching_exchange()` (no
arg) appear. `read_state()` uses `["v9"]` key access — KeyError if Harlo returns a non-v9 envelope;
`read_burnout_level` chains `["state"]["burnout"]` — untested for any of the 3 missing keys.
**Impact:** The wrappers are thin but contain real assumptions about Harlo's response envelope.
Harlo's contract shifts will surface as production KeyErrors, not test failures.

### M4 — `_call_tool` content/structuredContent fallthrough has zero tests
**Where:** `src/harlo_bridge.py:228-240`.
**Evidence:** `_call_tool` has 3 branches: (a) `content` list with `type: text` items, (b)
`structuredContent` dict fallback, (c) `HarloProtocolError` raise. None are tested directly. The
test suite mocks at `_call_tool` itself (e.g., `patch.object(bridge, "_call_tool", return_value=
{"ok": True})`), so the parsing layer it shields is invisible to the tests.
**Impact:** The MCP envelope parsing is the most likely surface to break on a Harlo upgrade; it's
also the surface no test exercises.

### M5 — `_send_notification` and `_write_frame` have no test coverage
**Where:** `src/harlo_bridge.py:257-272` and `262-272`.
**Evidence:** No test exercises `_send_notification` or `_write_frame`. `_write_frame` has a
`BrokenPipeError, OSError` → `HarloUnreachable` raise path that is the canonical "Harlo died
mid-write" failure mode. Zero tests.

### M6 — Test isolation across `HarloBridge()` instances assumes no class state
**Where:** `tests/test_harlo_bridge.py` constructs fresh `HarloBridge()` instances per test, but
none verify isolation if the class is later refactored to use class-level caching. Test ordering
is not asserted (no `pytest-randomly` hook), but each test mutates `bridge._proc` directly and
some tests assert on `threading.enumerate()` (line 321) — a global. If any other test in the run
spawns a `HarloBridge._drain_stderr` thread that does not join, this test goes red transiently.
**Impact:** Hidden ordering dependency on `threading.enumerate()`. Low probability, real footgun.

### M7 — `ProductFile.parse` edge cases unprobed
**Where:** `tests/test_schemas.py` (15 tests on schemas) vs `src/schemas.py:52-115`.
**Evidence:** Confirmed by probe:
  - **Empty `product:` value parses silently** — `ProductFile.parse('---\nproduct: \nstatus:
    in_flight\nlast_review_iso: 2026-05-22\n---\n')` succeeds with `product=""`. No test guards.
  - **Invalid `status:` value raises `ValueError` (from `ProductStatus(...)`)** — handled but no
    test asserts the raise type/message; a future refactor to `ProductStatus.MISSING` default would
    pass silently.
  - **Duplicate section headers silently merge** — two `## Status` headers concatenate text into a
    single `status_text`. No test guards. This is likely a bug surface (parse order assumed once).
  - **Unicode in section bodies** — works in practice (`café`, `Ω`) but unasserted; a future ASCII
    normalization would regress invisibly.
  - **Tab-prefixed bullets parse** — they do via `strip().startswith("- ")`. Unasserted.
  - **No closing `---` raises** — handled at line 62 but no test.
  - **Frontmatter line without `:` raises** (line 70) — handled but untested.
  - **Section *before* frontmatter close** — line iteration continues past frontmatter; if a `## `
    line appears inside the frontmatter block it's ignored, but no test guards.
**Impact:** The parser is the load-bearing format contract for every `data/products/*.md` file;
~8 edge cases are uncovered and at least one (empty product) is a likely production bug.

### M8 — No SQLite persistence test
**Where:** `src/first_hanna_brief.py:159-167` (`_persist`) vs `tests/`.
**Evidence:** No `import sqlite3`, no `tmp_path` fixture, no in-memory DB test in the suite.
`SCHEMA` migration safety (re-run idempotence) is unverified. `harlo_reachable` int-flag encoding
(`1 if reachable else 0`) is unverified. INSERT correctness is unverified.
**Impact:** The single persistence call in the PoC is invisible to tests.

### M9 — No `__enter__` / `__exit__` test for HarloBridge
**Where:** `tests/test_harlo_bridge.py`. `HarloBridge.__enter__` returns self and `__exit__` calls
`close()`; both are exercised implicitly by `_read_harlo()` but no test confirms `close()` is
idempotent under reuse, nor that an exception inside the `with` block still triggers close.
**Impact:** A subclass / refactor that overrides `__exit__` without calling super has no test
guardrail.

---

## MINOR findings

### m1 — Mock realism: `_MockProc.poll` always returns initial state
`_MockProc` in `tests/test_harlo_bridge.py:41-66` never transitions `_poll_result` based on stdin
state, so tests cannot simulate "Harlo died mid-call" easily. The fix is a small `simulate_death()`
hook; today's tests work around it by not testing the "died mid-call" branch.

### m2 — `_PipeProc.stderr` is `io.BytesIO`, not a real pipe
`_PipeProc` is used for timeout/read tests but its stderr is in-memory. The drainer tests use
`_MockProc` with `io.BytesIO`, not a real pipe either. Production stderr is a `subprocess.PIPE`
(line 214 in src) with kernel-level buffering that `BytesIO` does not model. This is the gap behind
the "no deadlock on large write" test using 80 KB — a real pipe would have demonstrated deadlock
without the drainer, but `BytesIO` never blocks on write so the test is a no-op for the deadlock
property it claims to verify.

### m3 — `compute_brief_priority` `_working_days_between` boundary tests sparse
The function has a `target < today` (return None) branch, a `target == today` (return 0) branch,
and a `days_remaining > _WORKING_DAYS_HORIZON` early-exit branch. The first two are exercised
indirectly via the deadline tests; the early-exit at horizon+1 is unasserted as a unit (only
indirectly via "far forcing function not treated as near"). A direct test of the helper would be
worth ~3 lines.

### m4 — `compute_brief_priority` ignores invalid ISO date (`except ValueError: continue`)
`src/computations/compute_brief_priority.py:69` silently swallows `ValueError` on
`date.fromisoformat`. Means "2026-13-99" becomes effectively "no deadline." No test guards this
silent-swallow behavior; a strict-mode flag in the future would regress invisibly.

### m5 — `ForcingFunction` with date but no description is allowed
`_parse_forcing_function` returns `ForcingFunction(date_iso="2026-05-30", description="")` when
the bullet is `"- 2026-05-30:"`. No test asserts this. Composer code in `_approaching_line` skips
entries that are both empty, but a date-only entry passes through with empty description and
prints as `"2026-05-30 —  (product)"` with trailing whitespace.

### m6 — `BriefPayload.referenced_products` mutation safety unverified
The dataclass is `frozen=True` so attribute reassignment is blocked, but `referenced_products` is a
mutable `list[str]`. `payload.referenced_products.append("x")` is not guarded. The frozen test
catches `body_markdown = ...` but not the list mutation. Minor; common Python idiom.

### m7 — `tests/computations/__init__.py` is empty
Fine, but the parent `tests/__init__.py` is also empty. Neither file participates in conftest
discovery beyond `conftest.py` itself; the empty `__init__.py` files are vestigial.

### m8 — Test naming consistency is good but `TestPortfolioLine` should mirror module
`tests/test_first_hanna_brief.py::TestPortfolioLine` is the only class. When more composer tests
land, a class-per-helper convention (`TestStateLine`, `TestApproachingLine`, `TestBlockersLine`,
`TestComposeBrief`) would mirror the mirror-tree convention.

### m9 — No `pytest.mark` taxonomy
No `@pytest.mark.slow`, `@pytest.mark.integration`, `@pytest.mark.harlo` markers. The suite is
homogeneous enough today (~0.44s for 74 tests) that this is fine, but as soon as integration
tests land, selective skip will require this. ORCHESTRATOR.md §9 lockout gates would benefit from
a `@pytest.mark.lockout` cluster.

### m10 — `conftest.py` only does sys.path injection
No shared fixtures (no `tmp_path` wrapper, no `mock_bridge`, no `phase_freeze`). Each test file
duplicates `_make(name, status)` helpers. `_make_product` could move to conftest and be reused
across `test_compute_brief_priority.py` and `test_first_hanna_brief.py`.

### m11 — `test_rule_36_voice_no_directives` checks 5 phrases, none from the actual Rule 36 spec
`tests/test_first_hanna_brief.py:63-70` checks `"you should", "you must", "you need to", "I
recommend", "please"`. RULES.md should be the source of truth for the directive vocabulary; if it
changes, this test does not. Worth a cross-reference comment to `RULES.md` rule 36.

### m12 — Producer phase tests label dates in test names but not docstrings
`test_morning_thursday_upper_boundary` is descriptive, but the test bodies use bare
`datetime(2026, 5, 28, 10, 59, tzinfo=_ET)` — a date-checker has to mentally compute the weekday.
A constant `_THURSDAY_MAY_28 = datetime(2026, 5, 28, ...)` at file head would reduce error.

---

## What integration tests are missing

1. **End-to-end `first_hanna_brief.py` run.** Mock `HarloBridge` at the constructor, point
   `PRODUCTS_DIR` and `DB_PATH` at `tmp_path`, run `main()`, assert SQLite row inserted, assert
   `print` body shape, assert exit code.
2. **FAMILY_LOCKOUT early-exit integration.** Freeze `datetime.now(_ET)` to a Saturday, run
   `main()`, assert no Harlo call attempted, no SQLite write, exit code 0, stdout matches "paused"
   message.
3. **State-blind handoff.** Mock `HarloBridge.drive_coaching_exchange` to raise `HarloUnreachable`,
   assert brief body contains "state-blind" marker, assert SQLite row has `harlo_reachable=0`.
4. **Multi-product portfolio integration.** Fixture: 3 `.md` files in `tmp_path/products/`, run
   `_compose_brief`, assert ranking matches `compute_brief_priority` output, assert all 3 referenced.
5. **Bridge round-trip with frame coalescing.** Spawn a fake JSON-RPC echo subprocess that writes
   two frames in one buffer; assert `_read_frame` returns the first frame and the second is in
   `_recv_buffer`; assert the next call returns the second without blocking.
6. **Composition-scope across a real `_rpc` cycle.** Today's coverage stops at `_call_tool` mock.
   An integration test that exercises the full `begin → write_frame → read_frame → end` cycle
   would surface the `_call_tool` envelope branches (M4) and the `_write_frame` failure modes (M5).

---

## Proposed belief deltas (3)

1. **New belief c006.** *Hanna's test suite has solid unit-test depth but no integration tests; the
   day-zero PoC `scripts/first_hanna_brief.py` is 75% untested.* Confidence: 0.8. Provenance: scout
   read every test file; 1 of 10 brief-composer functions has tests, 0 of `_persist` / `main` /
   `_compose_brief` / state-blind path. Status: active. Triggers a future plan entry for an
   integration-test sprint.

2. **New belief c007.** *Belief c003 ("done warrants critic[verify] before close") is empirically
   confirmed and the specific round-3 frame-coalescing bug fix has no regression test.* Confidence:
   0.9. Provenance: `_recv_buffer` exists in `src/harlo_bridge.py:70-71, 320-323, 358-359`; grep
   for `recv_buffer` in `tests/` returns zero. Status: active. Strengthens c003 (recommend bumping
   c003 from 0.7 → 0.8 or adding c007 as a corroborating belief).

3. **New belief c008.** *`compute_producer_phase` has precedence-collision behavior (MONTHLY beats
   WEEKLY_MONDAY / WEEKLY_FRIDAY on first-of-month) that is undocumented in the source and
   unverified by tests.* Confidence: 0.85. Provenance: probed Jun 1 2026 → MONTHLY; May 1 2026 →
   MONTHLY; both should be either WEEKLY_* or there should be a comment/test asserting the
   precedence. Status: active. Triggers a test-or-doc decision in DECISIONS.

---

## Open questions (3)

1. **Q: Is the MONTHLY-beats-WEEKLY precedence intentional, or a latent bug?** No
   `docs/DECISIONS.md` entry names the precedence; if intentional, it needs a docstring and a test;
   if unintentional, the function order needs to change. Either way, an explicit decision.
2. **Q: Should `_persist` SQLite calls be tested in-memory or against `tmp_path`?** Either pattern
   works; CONVENTIONS does not yet name one. The choice affects the integration-test design and
   whether persistence tests can run in parallel.
3. **Q: Should the brief composer sub-renders move to `src/composers/` so they can be unit-tested
   without `importlib.util.spec_from_file_location`?** `tests/test_first_hanna_brief.py:15-17`
   loads the script as a module via importlib because it lives in `scripts/`, not `src/`. This is
   the friction point that may explain why only `_portfolio_line` is tested — adding new helper
   tests requires copying the importlib boilerplate. Architectural choice; not a test fix.

---

## Noticed (out of scope)

- **First-line attribution trailer on `tests/`** — verified: zero test files have the cloned-from
  trailer. Correct per CONVENTIONS §3 (fresh seeds, no Harlo ancestor). No findings.
- **Rule 37 hygiene** — no patent vocabulary in any test file. Clean.
- **The `test_harlo_bridge.py` file header docstring claims D005.3 is "background stderr drainer
  writes into a 64-deep ring buffer."** This is also asserted in production code via
  `collections.deque(maxlen=64)`. Consistent. No finding.
- **Cross-file inconsistency:** `tests/computations/test_compute_brief_priority.py:24` uses
  `_TODAY = date(2026, 5, 22)` (a Friday — also Hanna's launch date). The producer-phase tests use
  date-by-date. A shared `tests/_constants.py` would deduplicate but is a code-quality (scout-code-
  quality) finding, not a test-quality one.
- **`compute_producer_phase` test names use weekday-by-name in the test name but not the
  docstring** — handed off to m12 above as a minor.

