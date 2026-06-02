# state/plan.md — Live GOAL: Hanna first-principles review

## GOAL

Review the Hanna codebase from first principles via a 7-agent scout phase, synthesize findings into a PRD identifying opportunities and areas for improvement, and surface to Joe with an explicit ask for "go" confirmation before any implementation. The PRD is the deliverable of this phase; implementation is gated on Joe's confirmation.

## EXIT_CRITERIA

- 7 scout findings delivered (one per survey angle) at `state/tasks/scout-<name>/findings.md`
- A consolidated PRD authored at `state/tasks/prd/PRD.md`, with prioritized recommendations + acceptance criteria + open questions + estimated effort
- `state/beliefs.md` updated with validated belief deltas from scout proposals (orchestrator-written; single-writer rule)
- `state/open_questions.md` updated with new high-leverage questions surfaced by scouts
- `state/checkpoint.md` written reflecting scout phase complete, awaiting "go"
- Joe presented with: scout summaries + PRD pointer + the orchestrator's prioritized recommendation + explicit "go / no-go / redirect" ask
- Implementation BLOCKED until Joe confirms "go"

## CONFIDENCE_THRESHOLD

0.8 (default per ORCHESTRATOR.md §3)

## CONSTRAINTS

- ≤20 agent calls total across scout + implementation phases (Joe's directive)
- Scout phase: 7 `critic[red_team]` dispatches; budget = 7 agents
- Implementation phase (post-go): ≤13 agents; worker/critic cycles per workflow
- Scout phase is READ-ONLY: no `src/`, `tests/`, or `docs/` modifications; only `state/` writes
- No implementation begins before Joe's explicit "go" confirmation
- All workers and critics inherit Hanna's hard constraints (Rules 34/35/36/37; canonical commit trailer; D003/D004 trailer hygiene; no new deps without a DECISIONS.md entry)

## TASK GRAPH

```
scout-architecture, scout-code-quality, scout-tests, scout-docs,
scout-ops, scout-security-rules, scout-lanes-schemas
       (7 parallel critic[red_team] dispatches)
              ↓
orchestrator synthesis → state/tasks/prd/PRD.md
       + state/beliefs.md belief-delta writes (validated)
       + state/open_questions.md updates
       + state/checkpoint.md
              ↓
report to Joe + WAIT for "go"
              ↓ (only after "go")
[implementation phase — designed post-go from PRD recommendations]
```

## INPUTS (per ORCHESTRATOR.md §2 — declared explicitly)

- Repo HEAD: `c65b6ae` on `claude/hanna-mcp-review-ZsorY`; `main` HEAD = `e08aebb` (PR #1 merged).
- All `state/beliefs.md` claims c001–c005 (active; including c003 at 0.7 — "done warrants critic[verify] before close").
- All `state/open_questions.md` rows q001–q003.
- `docs/DECISIONS.md` D001–D009.
- `docs/ROADMAP.md` §5 lane DAG (L1–L4a+L3b done; L4b queued; L5–L7 downstream).
- `HANNA_BLUEPRINT.md`, `RULES.md`, `NEXT.md`, `ORCHESTRATOR.md`.

## STATUS

Phase: SCOUT (in flight)
