---
description: Pick the next unblocked Hanna buildout lane per docs/ROADMAP.md and dispatch it per D002.
allowed-tools: [Read, Edit, Write, Bash, Agent, AskUserQuestion]
---

# hanna-dispatch-next

You are the harness for the Hanna buildout. This slash command advances the project by one lane per invocation, reading the single-source-of-truth status table in `docs/ROADMAP.md` §5 and dispatching the topmost unblocked lane per the MoE methodology ratified in `docs/DECISIONS.md` D002.

## Protocol

1. **Read `docs/ROADMAP.md`** entirely. Pay particular attention to §4 (per-lane spec) and §5 (lane status table).

2. **Identify the next lane.** Scan §5 top-to-bottom. The next lane is the topmost row where `Status == queued` AND every dependency lane (named in the `Unblocks` columns of upstream rows, OR explicitly in §4 "Dependencies") has `Status == done`.

3. **If no lane is unblocked:**
   - All lanes done → report "All lanes complete; Hanna buildout is finished. Run `/hanna-buildout-status` (future) or read NEXT.md for what's next."
   - Some queued but dependencies missing → report the dependency state and stop.
   - Stop without dispatching.

4. **If the lane is main-thread** (per D002, substrate-decision class — currently L1 D008 propagation):
   - Execute the work directly per the §4 brief skeleton for that lane.
   - Verify completion criteria from §4.
   - Update §5 status table from `queued` → `done` and record the new commit SHA in the `Last commit` column.
   - Commit + push.
   - Report the lane's completion + the next unblocked lane.

5. **If the lane is MoE-eligible:**
   - Read §4 for that lane's brief skeleton.
   - Dispatch the named expert(s) **in parallel** per D002 step 2, using the brief skeleton verbatim with any per-invocation specialization.
   - After all builder experts return, dispatch the **Compliance Reviewer** alone per D002 step 4.
   - Apply reviewer RECOMMENDED-CHANGES via Edit; re-dispatch any FAIL'd builder.
   - Verify completion criteria from §4 (pytest counts, grep results, brief artifacts).
   - Update §5 status table from `queued` → `done` and record the new commit SHA.
   - Commit (single commit per D002 step 6); push.
   - Report the lane's completion + the next unblocked lane.

6. **Status-table update is atomic with the lane commit.** Do not commit lane code separately from the status update. The `ROADMAP.md §5` table must always reflect what's at `HEAD`.

7. **Commit trailer canonical form** per CLAUDE.md:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

No other `Co-Authored-By` variant; no `Model-Version` inside the `Co-Authored-By` slot.

## Constraints

- **Rule 34.** If the current time is outside Mon–Fri 09:00–17:00 ET, the harness pauses by default. Override is explicit — Joe types `--override` as an argument to the slash command, and the override is logged in the commit body. Without override, report the lockout and stop.
- **Rule 35.** Lanes that touch the Harlo bridge are read-only or request-only. Compliance Reviewer audits per D002 step 4.
- **Rule 36.** Lane outputs surface observations, never directives.
- **Rule 37.** Never raise patent topics. Zero exceptions.
- **D002 single-commit-per-MoE-execution.** One commit per lane. Status update + lane code + (if applicable) test changes all in the same commit.

## Pairing with `/loop`

For hands-off daily progress: `/loop 24h /hanna-dispatch-next` advances ~1 lane per day. The loop self-terminates when all lanes are `done` (step 3 above returns the "all complete" message; `/loop` reads it as a stop signal).

For a focused buildout sprint: `/loop 4h /hanna-dispatch-next` advances ~6 lanes per day, provided Joe is available to ratify any MoE outputs that hit RECOMMENDED-CHANGES at the reviewer.

## Reporting format

After the dispatch lands, output a single paragraph in this shape:

```
Lane L{N} ({short title}) landed in {SHA}. {1-sentence summary of what changed.}
{Tests/verification result.} Next unblocked lane: L{N+1} ({short title}).
{1-sentence summary of what L{N+1} will do.}
```

Example:

```
Lane L1 (D008 propagation) landed in abc1234. BLUEPRINT §4 table renamed
to "Decision (D008)" with ratified values per row; §5 strikethroughs on
the cut lanes; §10 lane diagram refreshed; README lane mermaid updated;
RULES.md non-active rules annotated. No code changes — docs only. Next
unblocked lane: L2 (substrate hygiene). L2 lands pyproject.toml + Hanna
venv + .gitignore patch + tests/conftest.py + .github/workflows/ci.yml
via Substrate Engineer + Compliance Reviewer MoE dispatch.
```

## See also

- [`docs/ROADMAP.md`](../../docs/ROADMAP.md) — the lane DAG + per-lane spec + status table this command operates on.
- [`docs/DECISIONS.md`](../../docs/DECISIONS.md) D002 — the MoE methodology this command implements.
- [`docs/PRODUCER_LENS.md`](../../docs/PRODUCER_LENS.md) — what the buildout is building toward.
- [`docs/UI_UX_MAP.md`](../../docs/UI_UX_MAP.md) — visual map of the features each lane lands.
