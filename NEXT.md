# NEXT — for tomorrow-you

## 2026-05-22 session outcome — post-ratification buildout (L1–L4a + L3b)

The `/hanna-dispatch-next` harness advanced five lanes on `claude/hanna-mcp-review-ZsorY` via D002 MoE dispatches. PR [#1](https://github.com/JosephOIbrahim/Hanna/pull/1) covers the full buildout against `main`.

### Lane commits (top of branch, in order)

- `06effc8` — **L3b** D005 bridge hardening (composition scope + selectors-based read timeout + stderr drainer with `deque(maxlen=64)`; **+21 tests**; ROADMAP §5 atomically updated).
- `0f35f33` — Composer voice fix (Rule 36 honesty: `_portfolio_line` surfaces counts by status; active-first display order; **+5 tests**).
- `ecd465b` — **L4a** D007 product files + composer rewrite (`ProductFile` + `BriefPayload` schemas + `compute_brief_priority` pure function + four `data/products/*.md` stubs; **+25 tests**; ROADMAP §5).
- `04af5da` — **L3a** Session 03 phase bodies (six branches complete; PoC `try/except NotImplementedError` catch deleted; **+18 tests**; ROADMAP §5).
- `2f44e52` — **L2** Substrate hygiene (`pyproject.toml` + `tests/conftest.py` + `.github/workflows/ci.yml` + `.gitignore` patches; ROADMAP §5).
- `ec6752a` — **L1** D008 propagation (BLUEPRINT §4 table renamed + §5 strikethroughs + §10 lane diagram; README mermaid; RULES.md applicability note).
- `413e7ad` — docs+fix: CodeRabbit PR #1 review batch 1 (D001 anchors, NEXT.md status alignment, midday/evening phase fallback).

### Test count

73 tests pass on `06effc8` (52 baseline + 21 from L3b). Up from 7/7 at Session 02 close.

### Substrate-decision tree at end of session

| D-entry | Status | Implementation |
|---|---|---|
| D001 | resolved | `src/harlo_bridge.py` permitted-tool surface (visibly compliant per D001 implications bullet 4) |
| D002 | resolved | every MoE dispatch in this session followed the protocol |
| D003 | resolved | clones carry trailer only; fresh seeds carry no trailer |
| D004 | resolved | reviewer audits trailer placement within first 20 lines |
| D005 | resolved | **landed via L3b** (`src/harlo_bridge.py` + `tests/test_harlo_bridge.py`) |
| D006 | resolved | **pending L4b implementation** (next lane) |
| D007 | resolved | **landed via L4a** (`src/schemas.py` `ProductFile` + `BriefPayload`; `data/products/*.md`; composer rewrite) |
| D008 | resolved | **landed via L1** (BLUEPRINT + README + RULES docs propagation) |

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

- **Branch:** `claude/hanna-mcp-review-ZsorY`.
- **PR:** [#1](https://github.com/JosephOIbrahim/Hanna/pull/1) open against `main`. CI passing on `06effc8`. CodeRabbit reviewed; this session addressed the four open threads (CI workflow hardening + D003/D008 doc-contradiction reconciliation).
- **Branch is 14+ commits ahead of `main`.**

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
- **§C.3** — Harlo MCP-client precedent — **closed by L3b.** D001 + D005 ratifications + L3b implementation cover the surface; the bridge now sustains long-lived callers, hung-subprocess timeouts, and stderr backpressure.
- **§C.4** — `LockoutResponse` shape (needed before L6 `mcp_tools` lane).
- **§C.6** — RED override in delegate dispatch — **void per D008.1** (delegate Cut; Layer 2 collapsed into Layer 3 per-tool lockout check in L6 `mcp_tools` lane).

## Staleness flag — carry forward

`docs/SESSION_01_RECON.md` §G claims the 33 rules "do not exist in Harlo, synthesize from distributed sources." Still wrong per Session 01.5's direct extraction from `Harlo/CLAUDE.md` lines 37–194. Joe's call: correct or leave as session-stamped historical artifact.
