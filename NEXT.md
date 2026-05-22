# NEXT — for tomorrow-you

## 2026-05-22 (post-merge) — buildout chapter closed

PR [#1](https://github.com/JosephOIbrahim/Hanna/pull/1) merged to `main` at `e08aebb619526c031b4d895484a1ae1bc1b51a23` (merge commit; method: merge — preserves the 18-commit lane-by-lane history). Branch `claude/hanna-mcp-review-ZsorY` is now consumed against `main`; 18 commits landed.

Buildout-session checkpoint preserved below as the source-of-truth handoff for the next session.

---

## 2026-05-22 session outcome — post-ratification buildout (L1–L4a + L3b)

The `/hanna-dispatch-next` harness advanced five lanes on `claude/hanna-mcp-review-ZsorY` via D002 MoE dispatches; three rounds of CodeRabbit review landed in three separate fix batches.

### Lane commits (top of branch, in order before merge)

- `298f50c` — fix: CodeRabbit round 3 (4 latent bugs + 2 test polish) — HarloTimeout fallback in PoC, frame coalescing in bridge `_read_frame_with_timeout` (with new `self._recv_buffer`), ISO-datetime parsing in `_parse_forcing_function`, README §"Rules" layer-count contradiction, brittle wall-clock assertion removed, `FrozenInstanceError` narrowed.
- `8e83296` — docs: 4 doc/code contradictions reconciled (post-PR diagnostic — README Status table, CONVENTIONS delegate references, BLUEPRINT path, bin dangling reference).
- `2e68877` — docs: D003 + D008 contradictions in BLUEPRINT + README + RULES + NEXT.md refresh (CodeRabbit round 2).
- `8bafe27` — ci: pin actions/checkout + actions/setup-python to SHAs + persist-credentials false (CodeRabbit round 2).
- `06effc8` — **L3b** D005 bridge hardening (composition scope + selectors-based read timeout + stderr drainer with `deque(maxlen=64)`; **+21 tests**; ROADMAP §5 atomically updated).
- `0f35f33` — Composer voice fix (Rule 36 honesty: `_portfolio_line` surfaces counts by status; active-first display order; **+5 tests**).
- `ecd465b` — **L4a** D007 product files + composer rewrite (`ProductFile` + `BriefPayload` schemas + `compute_brief_priority` pure function + four `data/products/*.md` stubs; **+25 tests**; ROADMAP §5).
- `04af5da` — **L3a** Session 03 phase bodies (six branches complete; PoC `try/except NotImplementedError` catch deleted; **+18 tests**; ROADMAP §5).
- `2f44e52` — **L2** Substrate hygiene (`pyproject.toml` + `tests/conftest.py` + `.github/workflows/ci.yml` + `.gitignore` patches; ROADMAP §5).
- `ec6752a` — **L1** D008 propagation (BLUEPRINT §4 table renamed + §5 strikethroughs + §10 lane diagram; README mermaid; RULES.md applicability note).
- `413e7ad` — docs+fix: CodeRabbit PR #1 review round 1 (D001 anchors, NEXT.md status alignment, midday/evening phase fallback).

### Test count

**74 tests pass on HEAD** (`298f50c`). Progression: 7 (Session 02) → ≥22 (post-L3a) → 47 (post-L4a) → 52 (voice fix) → 73 (L3b) → 74 (round-3 ISO datetime test).

### Substrate-decision tree at end of session

| D-entry | Status | Implementation |
|---|---|---|
| D001 | resolved | `src/harlo_bridge.py` permitted-tool surface (visibly compliant per D001 implications bullet 4) |
| D002 | resolved | every MoE dispatch in this session followed the protocol |
| D003 | resolved | clones carry trailer only; fresh seeds carry no trailer |
| D004 | resolved | reviewer audits trailer placement within first 20 lines |
| D005 | resolved | **landed via L3b** (`06effc8`); frame coalescing patched in `298f50c` (`self._recv_buffer` preserves trailing bytes across `_read_frame_with_timeout` calls) |
| D006 | resolved | **pending L4b implementation** (next lane) |
| D007 | resolved | **landed via L4a** (`ecd465b`); `_parse_forcing_function` ISO-datetime split patched in `298f50c` (canonical `: ` delimiter; preserves `2026-06-01T10:30:00-04:00` timezone offsets) |
| D008 | resolved | **landed via L1** (`ec6752a`) |

### ROADMAP §5 status

| Lane | Status |
|---|---|
| L1 — D008 propagation | done |
| L2 — Substrate hygiene | done |
| L3a — Session 03 phase bodies | done |
| L3b — D005 bridge hardening | done |
| L4a — D007 product files + composer rewrite | done |
| L4b — D006 calendar.py | queued (next) |
| L5 — Schemas 2–5 | queued |
| L6 — `mcp_tools` lane | queued |
| L7 — `octavius_bridge.py` | queued |

## Where you are

- **Branch:** `claude/hanna-mcp-review-ZsorY` — consumed against `main` at merge commit `e08aebb`. Branch still exists in the remote; not deleted (Joe's discretion).
- **PR:** [#1](https://github.com/JosephOIbrahim/Hanna/pull/1) **merged**. CI was green on HEAD `298f50c` (success in 13s). All 13 CodeRabbit threads addressed across 3 rounds.
- **`main` HEAD:** `e08aebb` (merge commit; 18 commits incorporated).

## Next session entry point — L4b

L4b lands `src/channels/calendar.py` (D006 — Calendar channel implementation). It is the terminal lane of "Hanna is real" — after L4b ships, briefs land on Joe's iCloud calendar.

MoE dispatch per D002:

- **Bridge Engineer** — `src/channels/__init__.py` + `src/channels/calendar.py` with `publish(brief: BriefPayload) -> CalendarEventId | None` (returns `None` during `FAMILY_LOCKOUT` per Rule 34 gate at publish site) and `archive(event_id)`. AppleScript via `subprocess.run(["osascript", "-e", template])`. New exceptions: `HannaCalendarNotFound`, `HannaCalendarNotAvailable` (for non-macOS dev envs), `HannaCalendarPublishFailed`. Add `CalendarEventId = NewType("CalendarEventId", str)` to `src/schemas.py`. Author `tests/test_calendar.py` (≥6 mocked-subprocess tests).
- **Brief Composer** — `src/channels/_calendar_body.py` with `format_brief_body_for_calendar(body: str, max_chars: int = 1024) -> str` truncation helper. Author `tests/test_calendar_body.py` (≥3 cases per CONVENTIONS §1).
- **Compliance Reviewer** — D002 final-reviewer protocol. Confirm Rule 34 lockout check exists at publish call site; trailer hygiene (all three new files are fresh seeds — no Harlo ancestor — so no trailer).
- **Integration** — main thread wires `publish()` into `scripts/first_hanna_brief.py` main() with graceful `HannaCalendarNotAvailable` handling for non-macOS environments; swaps `bin/hanna-brief.command` Phase-2 target from `open "$BRIEF_PATH"` to `python3 -m src.channels.calendar publish-now`.

After L4b: L5 (schemas 2–5: `OverrideToken`, `JoeStateSnapshot`, `FormationRequest`, `FormationOutput`) and L6 (`mcp_tools` lane authoring `python/hanna/mcp_server.py`) are queued.

## Open questions still parked

- **§C.2** — Octavius IPC PoC (deferred until `octavius_bridge` lane / L7).
- **§C.3** — Harlo MCP-client precedent — **closed by L3b + round-3 patch.** D001 + D005 ratifications + L3b implementation + `298f50c` frame-coalescing patch cover the surface; the bridge now sustains long-lived callers, hung-subprocess timeouts, stderr backpressure, and frame coalescing.
- **§C.4** — `LockoutResponse` shape (needed before L6 `mcp_tools` lane).
- **§C.6** — RED override in delegate dispatch — **void per D008.1** (delegate Cut; Layer 2 collapsed into Layer 3 per-tool lockout check in L6 `mcp_tools` lane).

## Lessons from this session (for future buildout sessions)

- **Invocation surfaces what mocked tests miss.** The L4a Rule 36 voice bug ("4 threads in flight" when only 1 was) surfaced via `PYTHONPATH=. python3 scripts/first_hanna_brief.py`, not via the 47 passing tests. Always invoke the PoC at edges after each lane.
- **Deeper review catches what your own confidence misses.** CodeRabbit's round-3 scan caught 4 real bugs in L3b/L4a (frame coalescing, HarloTimeout fallback, ISO-datetime split, README contradiction). All 4 were latent — passing tests + my self-audit didn't surface them.
- **Doc-drift accumulates faster than code-drift.** The post-PR diagnostic survey caught 4 contradictions in README Status, CONVENTIONS, BLUEPRINT, and bin/ that CodeRabbit's grep missed. Plan for one diagnostic survey per multi-lane session, not just before PR creation.

## Staleness flag — carry forward

`docs/SESSION_01_RECON.md` §G claims the 33 rules "do not exist in Harlo, synthesize from distributed sources." Still wrong per Session 01.5's direct extraction from `Harlo/CLAUDE.md` lines 37–194. Joe's call: correct or leave as session-stamped historical artifact.
