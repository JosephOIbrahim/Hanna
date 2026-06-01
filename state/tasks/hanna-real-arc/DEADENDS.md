# DEADENDS.md — append-only registry of rejected directions

**Updated:** 2026-05-25 (DELIBERATE cycle 1)
**Format per row:** `axis | direction | observed change | rejection reason | (date)`
**Rule:** read this file before proposing. Never re-pay for a known dead end.

| axis | direction | observed change | rejection reason | date |
|---|---|---|---|---|
| external-system reachability verification | use an LLM agent in a Linux sandbox to verify a macOS-only external binary's existence | no information delta possible — verifier inaccessible from this context | the agent cannot reach the target; the human who has access can answer it for free in one question | 2026-05-25 (DELIBERATE cycle 1, Line C) |
| external-system reachability verification (generalized) | use an LLM agent + Linux sandbox + restricted GitHub MCP scope to reach external GitHub repos outside `josephoibrahim/hanna` | no information possible — both osascript binary (macOS-only) AND mcp__github__* reads of out-of-scope repos are blocked from this env | extension of the cycle-1 row — applies whenever the target is outside Hanna's MCP scope; q017 surfaces three resolution paths | 2026-05-25 (cycle 1 EXECUTE; c035) |
