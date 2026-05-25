# beliefs.md — durable belief layer (single-writer: orchestrator only)

Subagents propose belief deltas in their summaries `{claim, suggested_confidence, evidence}`;
the orchestrator validates and writes them here. Subagents never write this file directly.
Never delete a claim — supersede via SUPERSEDES / SUPERSEDED_BY. This layer never compresses.

CONFIDENCE_THRESHOLD for closing an open_question: 0.8 (default).

| CLAIM_ID | CLAIM | CONFIDENCE | EVIDENCE | SUPERSEDES | SUPERSEDED_BY | STATUS | CREATED | UPDATED |
|---|---|---|---|---|---|---|---|---|
| c001 | L1–L4a + L3b shipped and merged to `main` at `e08aebb` | 1.0 | PR #1 merged (merge commit `e08aebb`); 18 commits incorporated; NEXT.md 2026-05-22 post-merge section | none | none | active | 2026-05-25 | 2026-05-25 |
| c002 | The test suite passes 74/74 on the merged tree | 1.0 | NEXT.md "74 tests pass on HEAD (298f50c)"; CI green in 13s | none | none | active | 2026-05-25 | 2026-05-25 |
| c003 | A worker's "done" claim warrants only moderate confidence until an independent critic[verify] pass confirms it | 0.7 | CodeRabbit round-3 found 4 latent bugs (frame coalescing, HarloTimeout fallback, ISO-datetime split, README contradiction) after this thread self-declared L3b/L4a done | none | none | active | 2026-05-25 | 2026-05-25 |
| c004 | The next buildout lane is L4b (`src/channels/calendar.py`, D006) and it is unblocked | 0.9 | ROADMAP §5: L4b queued, dependencies done; NEXT.md "Next session entry point — L4b" | none | none | active | 2026-05-25 | 2026-05-25 |
| c005 | Hanna's D002 MoE taxonomy maps 1:1 onto the orchestrator roles (Architect=planner, builder experts=worker, Compliance Reviewer=critic[verify], step-5 integration=integrator) | 0.85 | docs/DECISIONS.md D002 expert table + coordination protocol steps 1–6; D009 ratification | none | none | active | 2026-05-25 | 2026-05-25 |
