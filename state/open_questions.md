# open_questions.md — open questions (durable; never compresses)

A question closes when an active claim in `beliefs.md` with confidence ≥ CONFIDENCE_THRESHOLD (0.8)
answers it; record the closing claim in CLOSED_BY. Closed questions stay in the file — they show
the trajectory. Initially seeded from NEXT.md "Open questions still parked"; q004–q013 added
by the orchestrator from the 7-scout first-principles review (2026-05-25).

| QUESTION_ID | QUESTION | LEVERAGE | STATUS | CLOSED_BY | CREATED |
|---|---|---|---|---|---|
| q001 | Octavius IPC PoC shape — what is the spawn/poll/harvest envelope for `octavius_bridge`? (NEXT §C.2) | medium | open | none | 2026-05-25 |
| q002 | `LockoutResponse` shape — required before the L6 `mcp_tools` lane can return structured lockout JSON (NEXT §C.4) | high | open | none | 2026-05-25 |
| q003 | `docs/SESSION_01_RECON.md` §G staleness — correct the "33 rules do not exist in Harlo" claim, or stamp it as historical? (NEXT staleness flag) | low | open | none | 2026-05-25 |
| q004 | Rhythm-anchor vs compose-moment — what timestamp does `BriefPayload.composed_at_iso` carry for D006 calendar publish? D006's posture rationale promises 09:00 ET anchor events but ROADMAP §4 spec hardcodes compose-moment (scout-lanes-schemas B2; blocks L4b) | high | open | none | 2026-05-25 |
| q005 | D006 cross-platform stance — macOS-only with explicit `HannaCalendarNotAvailable` + platform gate, or CalDAV cross-platform path? CI runs ubuntu-latest; osascript is macOS-only (scout-lanes-schemas B1 + scout-architecture; blocks L4b) | high | open | none | 2026-05-25 |
| q006 | Idempotency-key shape for L4b — UUID, content hash, ULID, or `(phase, rounded-rhythm-time, body-hash)`? Without this, `publish(brief)` produces duplicate Joe-visible calendar events on every retry (scout-ops B-OPS-002; blocks L4b) | high | open | none | 2026-05-25 |
| q007 | "Brief composition" boundary — when does one composition begin and end (per D001 "≤1 coach call per brief composition" + D005.1 `begin_composition` / `end_composition`)? Currently undefined in machine-checkable terms; today's PoC satisfies the rule "accidentally" (scout-architecture; blocks L6 mcp_tools) | high | open | none | 2026-05-25 |
| q008 | Scheduling substrate — launchd .plist, cron, MCP-tool-triggered, or in-process daemon? Required to back the README "always-on" claim (scout-ops B-OPS-001) | medium | open | none | 2026-05-25 |
| q009 | `docs/SESSION_01_RECON.md` §G + HANNA_DESIGN_ADOPTION.md status — correct, stamp historical, or retire? (scout-docs B3 + MAJOR — independently re-raised from q003) | low | open | none | 2026-05-25 |
| q010 | Model-id rule scope — does CLAUDE.md's prohibition extend to docs/ and commit messages, or only to code? `REVIEW_2026-05-22.md` carries a model-id string today (scout-docs MAJOR) | low | open | none | 2026-05-25 |
| q011 | DECISIONS.md template — require an explicit "Rejected alternatives" block? D003 + D009 have it; D001/D002/D005/D006/D007/D008 fold rejections into Reasoning prose. The planner contract calls for explicit rejections (scout-architecture MAJOR) | low | open | none | 2026-05-25 |
| q012 | L5 schema split — should `OverrideToken` (security primitive), `JoeStateSnapshot` (Harlo-coupling decision), `FormationRequest/Output` (IPC contract), and a fourth parsed-data shape be one D-entry or four? Three of the four do not follow the `ProductFile`/`BriefPayload` pattern the brief skeleton invokes (scout-lanes-schemas M5) | medium | open | none | 2026-05-25 |
| q013 | ORCHESTRATOR.md §7 resolution — amend §7 to permit per-GOAL `state/plan.md` as a standing file, or migrate the GOAL block to NEXT.md per the original adapter rule and retire `state/plan.md`? (scout-architecture MAJOR + scout-docs MAJOR; orchestrator self-violates on its first run) | high | closed | c015 | 2026-05-25 |
