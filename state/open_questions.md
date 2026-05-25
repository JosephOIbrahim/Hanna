# open_questions.md — open questions (durable; never compresses)

A question closes when an active claim in `beliefs.md` with confidence ≥ CONFIDENCE_THRESHOLD (0.8)
answers it; record the closing claim in CLOSED_BY. Closed questions stay in the file — they show
the trajectory. Seeded from NEXT.md "Open questions still parked" (§C.3 already closed by L3b,
§C.6 voided by D008.1 — neither seeded as open).

| QUESTION_ID | QUESTION | LEVERAGE | STATUS | CLOSED_BY | CREATED |
|---|---|---|---|---|---|
| q001 | Octavius IPC PoC shape — what is the spawn/poll/harvest envelope for `octavius_bridge`? (NEXT §C.2) | medium | open | none | 2026-05-25 |
| q002 | `LockoutResponse` shape — required before the L6 `mcp_tools` lane can return structured lockout JSON (NEXT §C.4) | high | open | none | 2026-05-25 |
| q003 | `docs/SESSION_01_RECON.md` §G staleness — correct the "33 rules do not exist in Harlo" claim, or stamp it as historical? (NEXT staleness flag) | low | open | none | 2026-05-25 |
