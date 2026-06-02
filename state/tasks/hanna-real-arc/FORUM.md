# FORUM.md — append-only deliberation log

**Updated:** 2026-05-25 (DELIBERATE cycle 1)
**Sections in order:** PROPOSAL → CRITIQUE → RESULT (announce wins AND failures) → ANALYSIS (mechanistic).

---

## 2026-05-25 — SKETCH-time standing critiques

(See PLAN.md "Critique-before-build" section — Line A, B, C top-proposals each survived initial critique. Surviving lines proceed to DELIBERATE cycle 1 where per-proposal critiques happen on the FORUM proper.)

---

## CYCLE 1 — DELIBERATE

### Line A top proposal — src/channels/calendar.py + reconciliation columns + tests

**Proposal.** Author `src/channels/__init__.py` + `src/channels/calendar.py` with `publish(brief: BriefPayload) -> CalendarEventId | None` (None on FAMILY_LOCKOUT or HannaCalendarNotAvailable) and `archive(event_id) -> None`. Honor D006 (Hanna iCloud calendar) + D010 (use brief.phase_anchor_iso as event start) + D011 (raise HannaCalendarNotAvailable on non-mac) + D012 (lookup by brief_id before insert). Add `CalendarEventId = NewType("CalendarEventId", str)` + `calendar_event_uid` + `unpublished_reason` columns to the briefs table.

**Critique (severity x likelihood).**
- **R1** AppleScript template fragility — quoting/escaping/newlines in brief body. **medium x high**. Mitigation: use `quoted form` substitution + body via a temp file + `do shell script` read.
- **R2** macOS osascript permissions popup post-launchd. **high x medium**. Mitigation: document required Calendar.app grant in `bin/README.md`; raise `HannaCalendarPermissionRequired` with grant instructions in the message.
- **R3** Calendar-identity ambiguity (multiple "Hanna" calendars). **medium x low**. Mitigation: parameterize name with default `"Hanna"`; first-publish queries `events whose summary contains` to detect duplicates before insert.
- **R4** Sub-templates differ by phase (weekly/monthly background calendar). **low x low**. Defer.
- **R5** `archive()` needs `Hanna · Archive` calendar. **medium x high**. Mitigation: raise `HannaCalendarNotFound("Hanna · Archive")` cleanly; don't auto-create (matches D011 macOS-only stance); document in `bin/README.md`.

**Result.** SURVIVES with R1/R2/R3/R5 mitigations folded into the worker brief. **Rating: 4/5** (high gain on P2 + P6 + P9 partial; medium-high implementation risk).

**Expected effect on champion.** P2 0.80 -> 0.95 (post-Joe-Mac verifier still pending); P6 0.75 -> 0.80; P9 0.65 -> 0.70.

---

### Line B top proposal — D014 LockoutResponse shape ratification

**Proposal.** Ratify D014 closing q002. Rejected: error-with-rich-message (Rule 36 violation if message reads directive); decorator-injected-skip (opaque to Joe); exception-with-structured-payload (conflates success/failure). Chosen: **structured no-op JSON** returned (not raised) with fields `{paused: true, reason, phase, next_anchor_iso, override_path_hint?}`.

**Critique.**
- **R1** Claude Code's MCP client may render arbitrary JSON poorly. **high x medium**. Mitigation: `paused: true` boolean at the top of the JSON for renderers that surface top-level keys; provide a human-readable `message` field with Rule 36 voice.
- **R2** Field shape commits before we've seen Claude Code's renderer. **medium x medium**. Mitigation: scope D014 to JSON SHAPE, not renderer integration; if F6 fires we reverse cleanly.
- **R3** `override_path_hint` overlaps with q014 (secret-storage). **low x low**. Mitigation: mark `override_path_hint` as informational-only — does NOT decide override_token mechanism.

**Result.** SURVIVES. **Rating: 5/5** (unblocks L6 entirely; low implementation risk; substrate-decision class — author-by-main-thread).

---

### Line B 2nd proposal — D015 composition boundary

**Proposal.** Ratify D015: one composition = one MCP-tool body invocation; `begin_composition()` at tool entry, `end_composition()` at tool exit (try/finally); transitively any Harlo `coach` call inside the tool body uses the same composition. Closes q007.

**Critique.**
- **R1** scripts/first_hanna_brief.py already wraps composition implicitly via `drive_coaching_exchange()`. **low x high**. Mitigation: D015 ratifies that the implicit wrap counts as a composition; MCP tools opt into explicit begin/end when they call multiple Harlo methods.
- **R2** Nested compositions (tool A calls into tool B)? **low x low**. Mitigation: nested = error; per-MCP-tool-invocation only.

**Result.** SURVIVES. **Rating: 3/5** (medium gain — semantic clarification + Rule-35-friendly; low risk).

---

### Line B 3rd proposal — JoeStateSnapshot schema only (other schemas deferred)

**Proposal.** Author `JoeStateSnapshot` frozen dataclass in src/schemas.py. Fields mirror Harlo's `read_state()` return shape: `burnout: str`, `prediction: dict | None`, `schedule: dict`, `ts: str`, plus `extra: dict[str, Any] = field(default_factory=dict)` for forward-compat. Plus a `from_harlo_payload(d: dict) -> JoeStateSnapshot` constructor.

**Critique.**
- **R1** Harlo's payload shape may evolve. **medium x low**. Mitigation: `extra` field for unknown keys.
- **R2** No consumer yet (no MCP tool uses it). **medium x medium**. Mitigation: this is the L5 "ship the schema; verify at L1 only" pattern — integration verifier site lands at Line D (L6).

**Result.** SURVIVES with `extra` field mitigation. **Rating: 3/5** (medium gain — one of 4 L5 schemas).

**Deferred from Line B's original queue:**
- `OverrideToken` — needs q014 (secret-storage substrate) closed first.
- `FormationRequest` / `FormationOutput` — needs Line C (Octavius reachability) resolved.

---

### Line C top proposal — *DIED ON THE FORUM*

**Proposal.** Dispatch a critic[evaluate] agent to assess Octavius reachability — does `subprocess.Popen(["octavius", "mcp"])` succeed on this system? Reads the assumed Octavius contract from HANNA_BLUEPRINT §9 / RULES.md.

**Critique.**
- **R1** This Linux container CANNOT run macOS-only binaries or reach Joe's local Octavius even if it exists. The L1 spawn-test verifier is impossible here. **HIGH severity, HIGH likelihood** — fully invalidates.
- **R2** Doc-only survey returns "I don't know" — same information state as today.
- **R3** The information IS available — Joe knows. Cheapest correct verifier: **ask Joe.**

**Result.** **DIED.** Replaced by a free-information move: AskUserQuestion to Joe re Octavius existence + path. Net agent savings: 1.

**Dead-end recorded in DEADENDS.md** — see entry.

**Replacement (Line C, post-DIE).** Ask Joe inline: does Octavius exist as a runnable binary today? if yes, what command spawns it? if no, what's the timeline?

---

## Ranked surviving queue (global, post-critique)

| Rank | Line | Proposal | Rating | Dispatch path |
|---|---|---|---|---|
| 1 | B | D014 LockoutResponse shape ratification | 5/5 | main-thread (D002: decisions author-by-main-thread) |
| 1 | C | Ask Joe re Octavius existence | 5/5 | AskUserQuestion (free; this turn) |
| 3 | A | `src/channels/calendar.py` + reconciliation columns + tests | 4/5 | worker agent + critic[verify] |
| 4 | B | D015 composition boundary ratification | 3/5 | main-thread |
| 5 | B | `JoeStateSnapshot` schema authoring | 3/5 | worker agent (next cycle) |

## Critique-before-build verdict

5 proposals reviewed. 4 survive; 1 died; Line B reordered (Override + Formation schemas deferred). The harness's filtering goal achieved: no agent dispatched on a proposal that didn't survive critique.

## CYCLE 1 — EXECUTE (entering)

Dispatching in this turn:
- Main-thread D014 + D015 ratifications.
- One worker agent on Line A (src/channels/calendar.py).
- One AskUserQuestion to Joe re Octavius.
Held: Line B JoeStateSnapshot (next cycle); Lines D + E (dependency-held).
