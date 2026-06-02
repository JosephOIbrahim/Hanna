# Hanna — Claude Code Project Instructions

Project-local instructions. Supplements (does not replace) the global instructions at `~/.claude/CLAUDE.md`. Where this file and the global conflict, this file wins for work inside `/Users/rustybeard/Code/Hanna`.

---

## What Hanna is

An always-on AI producer cloned from Harlo's substrate. Surfaces decisions; does not make them. See [`HANNA_BLUEPRINT.md`](HANNA_BLUEPRINT.md) for the architectural spec.

Hanna inherits the 33 inviolable rules from Harlo plus 4 producer-specific addenda. See [`RULES.md`](RULES.md).

Hanna conventions accrete as sessions resolve open questions. See [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

---

## Read edges

- **Harlo:** read-only via `src/harlo_bridge.py`. Hanna never writes to Harlo. (Rule 35.)
- **Octavius:** request-only via `src/octavius_bridge.py`. Spawn / poll / harvest only. (Rule 35.)

---

## Orchestration

Multi-agent work in this repo runs under the orchestrator operating manual in [`ORCHESTRATOR.md`](ORCHESTRATOR.md). Subagent roles live in `.claude/agents/` (planner / worker / critic / integrator); durable belief and open-question state lives in `state/`. `/hanna-dispatch-next` is one workflow under that orchestrator (see ORCHESTRATOR.md §8). This file does not duplicate the manual; it points at it.

---

## Commit trailer (canonical)

Every commit in this repo ends with the canonical Claude Code format:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

If model-version analytics are needed, add a separate trailer line adjacent to (not inside) `Co-Authored-By`:

```
Model-Version: claude-opus-4-7-1m
```

The `Co-Authored-By` slot is reserved for the canonical `Claude <noreply@anthropic.com>` to avoid impersonation-classifier false positives. Any other form (e.g. `Claude Opus 4.7 (1M context)`) trips the auto-mode classifier and is disallowed.

This rule is duplicated in `~/.claude/CLAUDE.md` for global enforcement. Both files agree.

---

## Patent topics

**Rule 37.** Never raised. No exceptions in any session, commit message, or doc generated under this repo.

---

## Family-first lockout

**Rule 34.** Sessions outside Mon–Fri 09:00–17:00 ET pause by default. Override path is explicit — a single yes from Joe per session — and is logged in the session prompt.

---

## Sessions

Sessions are numbered. Each session ships its own deliverable on a feature branch:

- `session-01-recon` — observation doc (shipped 2026-05-13).
- `session-01.5-rules` — rules extraction + conventions + this file.
- `session-02-scaffold` — first production code (clones first computation).
- Subsequent sessions named after their primary lane.

Session docs live under `docs/SESSION_NN_*.md`.

---

## What this file is not

- Not a duplicate of the global `~/.claude/CLAUDE.md`. Behaviors, body-first protocols, coworker blend, RSD guidance — those live globally. This file is project scope only.
- Not a duplicate of `RULES.md`. Rules live there; this file points at them.
- Not a duplicate of `HANNA_BLUEPRINT.md`. Architecture lives there.
- Not a duplicate of `ORCHESTRATOR.md`. The orchestration manual lives there; this file points at it.

Each file has one job.
