# scout-ops — Operational / Production-Readiness Red-Team

ROLE: critic
MODE: red_team
TASK_ID: scout-ops
DATE: 2026-05-29
SCOPE: Hanna's operational posture — observability, scheduling, idempotency, persistence durability, secrets, error reporting, retention, health. Architecture, tests, docs, lanes/schemas, security-rule enforcement covered by sibling scouts.
ARTIFACT: `/home/user/Hanna/state/tasks/scout-ops/findings.md`

---

## Executive Summary

Hanna's substrate ships clean code, hardened bridges and a 74-test green CI — but its operational posture is essentially absent. There is **no logging anywhere in `src/` or `scripts/`** (`grep "import logging|logger|logging\." src/ scripts/` returns 0 hits); there is **no scheduler** of any kind (no cron, no launchd `.plist`, no systemd unit, no `at`, no MCP self-trigger) — the README's headline claim "Always-on AI producer" is structurally false today because the only triggers are (a) a developer typing `python3 scripts/first_hanna_brief.py` and (b) double-clicking `bin/hanna-brief.command`, which opens a static HTML mockup and does not invoke any Python at all. The SQLite stage at `data/hanna.sqlite` ships with an AUTOINCREMENT id and zero idempotency surface (no UID, no dedup key, no UPSERT) — re-running the script inside the same minute produces a duplicate `briefs` row; the schema has no retention policy, no backup hook, no `PRAGMA journal_mode=WAL`, no `fsync` discipline, and no failure recovery when `_persist` hits `OSError` (disk-full or permission-denied unwinds straight to the user with no telemetry). The Harlo bridge degrades silently to "state-blind" on `HarloUnreachable`/`HarloTimeout` — the brief mentions it, but **Joe is never notified out-of-band**; if Harlo is dead for a month, Hanna keeps shipping state-blind briefs and nothing escalates. The `override_token` mechanism mandated by Rule 34 and described in `RULES.md:187` and `HANNA_BLUEPRINT.md:233` is **spec-only — zero implementation, zero tests, zero HMAC key plumbing**, and there is no secrets-management surface at all (no `os.environ` reads, no `.env`, no Keychain hook). The `last_stderr()` ring-buffer in the bridge captures 64 lines from Harlo's stderr but is **never read by any caller** — observability captured then discarded. The future `src/channels/calendar.py` (L4b) calls for a `publish(brief: BriefPayload) -> CalendarEventId` surface but `BriefPayload` carries no idempotency token, so a publish retry after a transient AppleScript failure will create a duplicate event on Joe's calendar with no way to detect it. The good news: surface area is small and the structural fixes (logging shim, launchd `.plist`, BriefPayload UUID, UPSERT-on-UUID, watchdog for stale Harlo) are bounded and orthogonal to the lane DAG.

---

## Findings

### BLOCKERS

#### B-OPS-001 — "Always-on AI producer" is structurally false: no scheduler exists

**Evidence.**
- `README.md:5` — *"Always-on AI producer for a creative portfolio"*.
- `HANNA_BLUEPRINT.md:59` — *"Hanna is an always-on AI producer for Joe's creative portfolio."*
- `HANNA_BLUEPRINT.md` Audit Finding #4 (line 25): *"'Always-on producer' contradicts MCP-tools-only. MCP tools fire only when Joe opens a Claude session. A producer that only speaks when spoken to is a logbook."* — known, named, unresolved.
- `docs/DECISIONS.md:330` — *"The 'always-on' claim becomes real once `src/channels/calendar.py` lands."* That file does not exist.
- `grep -rE "cron|launchd|systemd|\.plist|daemon|crontab|@daily|@hourly"` over the repo returns **zero hits in `scripts/`, `src/`, or any deployable artifact**. The two `daemon=` hits are `threading.Thread(daemon=True)` (stderr drainer) — not a scheduler.
- `bin/hanna-brief.command:34` — `open "$BRIEF_PATH"` opens the static HTML mockup. Does not invoke `python3` or `scripts/first_hanna_brief.py`. Phase-1 launcher and PoC script are **not connected**.
- L4b is "queued"; nothing in `docs/ROADMAP.md` §5 describes how the calendar.py module gets invoked at brief o'clock — `python3 -m src.channels.calendar publish-now` is itself manual.

**Impact.** The day-zero PoC demonstrates the contracts but no operational substrate fires it. Six daily/weekly cadences advertised in the README (morning brief, midday, evening, Monday 30k, Friday harvest, monthly 50k) are wall-clock concepts with no wall-clock binding. Hanna ships only when Joe types a command — which is the failure mode the README headline explicitly disclaims.

**Why BLOCKER.** The headline marketing claim of the project is operationally unbacked. Every downstream "always-on" promise (calendar publishing, family-first window enforcement, missed-brief recovery) inherits this hole. L4b lands calendar.py but does not solve "what triggers it at 09:01 ET" — that scheduler decision is undocumented and unowned.

---

#### B-OPS-002 — Brief persistence has no idempotency key — duplicates are silent and unbounded

**Evidence.**
- `scripts/first_hanna_brief.py:34-42`:
  ```sql
  CREATE TABLE IF NOT EXISTS briefs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TEXT NOT NULL,
      phase TEXT NOT NULL,
      body TEXT NOT NULL,
      harlo_reachable INTEGER NOT NULL
  )
  ```
  No UNIQUE constraint. No event UUID column. No `phase, day` composite key.
- `scripts/first_hanna_brief.py:163-167` — straight `INSERT`, no `INSERT OR IGNORE`, no `INSERT … ON CONFLICT`, no SELECT-before-INSERT.
- `BriefPayload` (`src/schemas.py:131-136`) carries `phase`, `composed_at_iso`, `body_markdown`, `referenced_products`. **No UUID, no idempotency_key, no event_id.** A future `publish(brief: BriefPayload) -> CalendarEventId` (per `docs/DECISIONS.md:325`) has nothing stable to use as a dedup key for retry.
- `docs/ROADMAP.md:247` describes `archive(event_id: CalendarEventId) -> None` — archive needs the event_id to be stored *somewhere*, but the `briefs` table has no column for it.

**Impact.**
- **Manual reproduction:** running `python3 scripts/first_hanna_brief.py` twice in 09:00–17:00 ET produces two rows with different `composed_at_iso`, different `id`s, semantically duplicate briefs.
- **Calendar retry:** L4b's calendar publish is an AppleScript subprocess that can fail transiently. With no dedup key, any retry produces two events on Joe's calendar for the same rhythm slot. Rule 36 ("surface, do not decide") is violated by spam — Hanna *should* be idempotent at brief identity, not at row identity.
- **Archive contract uncomputable:** `archive(event_id)` requires storing the returned `CalendarEventId` against the brief. The schema today has nowhere to put it.

**Why BLOCKER.** L4b is the next lane; it lands a write surface (the calendar) that has no rollback. Calendar duplicates are visible to Joe — they are the exact "Hanna spammed me" failure mode the calm-typography web design explicitly inverts.

---

### MAJORS

#### M-OPS-001 — Zero logging or structured observability

**Evidence.**
- `grep -rn "import logging\|logger\|logging\." /home/user/Hanna/src/ /home/user/Hanna/scripts/` → **0 hits**.
- The only stdout calls in the entire codebase: `scripts/first_hanna_brief.py:173` (`print("Hanna paused: FAMILY_LOCKOUT …")`) and `:179` (`print(brief.body_markdown)`). Both are the brief itself — not telemetry.
- `bin/hanna-brief.command:27-29` — a single error path that echoes to stdout if the HTML mockup is missing. No timestamp, no error code, no destination.
- `src/harlo_bridge.py:67, 171-202` — `_stderr_ring: collections.deque(maxlen=64)` plus `last_stderr() -> list[str]`. The ring exists, the accessor exists, but **`grep -rn "last_stderr" src/ scripts/ tests/`** returns *only the definition and tests*. No caller in the PoC script ever reads it. Harlo's stderr is captured and silently discarded after 64 lines.
- `.gitignore:39` — `*.log` is ignored, so the intent was logging at some point. No code writes a log.

**Impact.** When a brief fails to compose, when Harlo times out, when SQLite throws — no record. No way to ask "did the 09:01 brief fire?" except by querying the SQLite file. No way to trace *why* a state-blind brief landed (no captured stderr ring). No structured-log pipeline for the inevitable post-mortem.

**Why MAJOR not BLOCKER.** The PoC sits behind a human running `python3` manually, so the lack of logging is currently survivable via the terminal. Becomes a BLOCKER the moment the scheduler in B-OPS-001 lands.

---

#### M-OPS-002 — Harlo bridge failures degrade silently to state-blind with no escalation

**Evidence.**
- `scripts/first_hanna_brief.py:53-58`:
  ```python
  def _read_harlo() -> tuple[bool, dict | None]:
      try:
          with HarloBridge() as bridge:
              return True, bridge.drive_coaching_exchange()
      except (HarloUnreachable, HarloTimeout):
          return False, None
  ```
- `scripts/first_hanna_brief.py:91` — *"Harlo edge unreachable — Hanna is operating **state-blind**."* The brief body announces the degradation, but only Joe seeing the brief learns about it.
- `_read_harlo` swallows `HarloUnreachable` and `HarloTimeout` and silently drops `HarloProtocolError` (which is *not* caught) — a `HarloProtocolError` crashes the script entirely with a traceback to stdout and no SQLite row. There is no `except HarloProtocolError` arm.
- The brief lands in SQLite with `harlo_reachable=0`, but **no monitor, no nagios check, no Joe-facing alert** queries that column. If Harlo is down for a week, Hanna ships 30 state-blind briefs and no escalation fires.
- `src/harlo_bridge.py:173` `last_stderr()` is precisely the diagnostic surface for "what did Harlo say before it died" — and `_read_harlo()` discards the bridge object without reading it.

**Impact.** Silent degradation is the worst observable mode for a Rule 18 / Rule 35 system: Hanna keeps producing without the cognitive-state signal that makes the brief honest. Joe has no out-of-band way to learn that Harlo is dead.

**Why MAJOR.** Production observability gap; not a contract violation today because the contract explicitly allows state-blind degradation. Becomes a BLOCKER if Hanna ships briefs that imply Joe's state when state is missing.

---

#### M-OPS-003 — `override_token` (Rule 34) is spec-only — no implementation, no tests, no key plumbing

**Evidence.**
- `RULES.md:187` — *"Override path exists for true exceptions: explicit `override_token` with TTL (HMAC-signed, single-use). This is a deliberate friction surface, not a flag. Tests verify all three layers. **Bypassing any layer fails CI.**"*
- `HANNA_BLUEPRINT.md:233` — same claim, *"requiring an explicit `override_token` with TTL. Not a flag."*
- `README.md:98` — *"Override exists for true exceptions — explicit `override_token`, HMAC-signed, single-use, TTL-bounded."*
- `grep -rn "override_token\|HMAC\|hmac"` over `src/ scripts/` — **0 hits in code.** Only `RULES.md`, `HANNA_BLUEPRINT.md`, and `README.md` reference it.
- No `os.environ` reads, no Keychain access, no `.env.example`, no `cryptography` dependency in `pyproject.toml` (checked: `setup-python` + `pip install -e .[dev]` in `.github/workflows/ci.yml:19-21`; no crypto extra anywhere).
- `compute_producer_phase` has no `allow_outside_window` or `override_token` parameter — its signature in `scripts/first_hanna_brief.py:46` is two positional args (`datetime`, `default_phase`). No bypass surface.
- The "Bypassing any layer fails CI" claim is unenforceable because the layer doesn't exist.

**Impact.** A documented friction-surface that does not exist is worse than no override at all — it tells reviewers "the bypass is governed" when in fact there is no bypass and no governance. Layer 3 (per-tool MCP gating) is deferred to L6 per `RULES.md:15`; the override is downstream of that, but the cryptographic primitives (HMAC key storage, single-use replay protection, TTL clock) need design now.

**Why MAJOR.** Rule 34 is "currently load-bearing" per `RULES.md:15` and is one of the four producer-specific addenda. A spec-only enforcement surface is the kind of latent contradiction belief c003 names — passing tests would not catch it.

---

#### M-OPS-004 — No health check, no self-test, no liveness probe — only way to know Hanna is alive is to invoke a brief

**Evidence.**
- `grep -rn "health\|/healthz\|liveness\|readiness\|self_test\|status_check"` over `src/ scripts/` returns 0 hits.
- No `--health` flag on `scripts/first_hanna_brief.py`. No `python3 -m src.harlo_bridge --ping` mode.
- The bridge's `_ensure_proc → initialize` handshake (`src/harlo_bridge.py:220-225`) is the only liveness signal — but it requires spawning a full subprocess and writing two RPC frames. Not a probe; an exchange.
- `HarloBridge.last_stderr()` exists but is the post-mortem surface, not a probe.

**Impact.** When the scheduler in B-OPS-001 lands, there is no way for an external monitor (a launchd `KeepAlive`, a cron'd `curl`, even a `bash` smoke test) to ask "is Hanna ok?" without firing a full brief and writing a row to SQLite. Every probe is also a write.

**Why MAJOR.** Standard operational hygiene gap. Trivial to add (`--dry-run` flag + zero-side-effect health output) but currently nowhere on the roadmap.

---

#### M-OPS-005 — SQLite durability is undefended: no WAL, no fsync discipline, no disk-full recovery, no retention

**Evidence.**
- `scripts/first_hanna_brief.py:159-167` — `_persist` uses `sqlite3.connect(DB_PATH)` with **no `PRAGMA journal_mode=WAL`, no `PRAGMA synchronous=NORMAL`, no `PRAGMA foreign_keys=ON`**. Default journal mode is rollback journal; default synchronous is FULL. Crash-safe by default but slow and not tuned.
- No `try/except OSError` around the `INSERT`. If the disk is full, `conn.commit()` raises `sqlite3.OperationalError` straight to the user's terminal. No fallback to stdout-only mode, no in-memory ring, no defer-and-retry queue.
- No retention policy. The `briefs` table grows unbounded. At 6 briefs/workday × ~2KB body × 250 workdays/year ≈ 3MB/year of brief bodies — not catastrophic, but no policy means no cleanup audit when it matters (e.g., if Joe wants "delete everything before 2026 because I'm pivoting").
- No backup hook. `data/hanna.sqlite` is gitignored (`.gitignore:43`). There is no `scripts/backup_hanna.sh`, no Time Machine exclusion guidance, no documented "this is the file you'd lose."
- `docs/DECISIONS.md:447` audit verdict: workload sized for "~10 briefs/week × ~2KB, 6 events/day on a wall clock" — small enough that the cost of WAL+retention is trivial, but neither is in place.

**Impact.** Disk-full during morning brief composition crashes Hanna and produces no row, no telemetry, no recovery. Joe loses the day's first brief and has no signal it happened.

**Why MAJOR.** Workload is small enough that the issue is operationally minor today; it becomes the recovery-time-objective question the moment Hanna is real (post-L4b).

---

### MINORS

#### N-OPS-001 — `bin/hanna-brief.command` and `scripts/first_hanna_brief.py` are not wired together

**Evidence.**
- `bin/hanna-brief.command:24, 34` — opens `web/templates/morning_brief.html` (static design reference), never invokes the PoC script.
- `docs/ROADMAP.md:250` — *"`bin/hanna-brief.command` — Phase-2 swap target: replace the static-HTML `open` with `python3 -m src.channels.calendar publish-now`."* Acknowledged but not done.
- The launcher comment (`bin/hanna-brief.command:5-10`) describes Phase-1 and Phase-2 but the swap is queued behind L4b.

**Impact.** A user double-clicking the launcher today does *not* compose a brief, does *not* persist, does *not* call Harlo — only opens a design mockup. The launcher's name is operationally misleading.

**Why MINOR.** Documented as Phase-1; swap lane is scoped. Worth flagging because the launcher's name implies a working brief and is the only desktop-discoverable surface.

---

#### N-OPS-002 — `data/products/*.md` parsing has no error reporting

**Evidence.**
- `scripts/first_hanna_brief.py:74-82` — `_read_product_files` calls `ProductFile.parse(path.read_text(), path=path)` inside a loop with no try/except.
- `src/schemas.py:52-102` — `ProductFile.parse` raises `ValueError` for missing frontmatter, malformed lines, or missing required keys.
- One malformed product file kills the entire brief composition. There is no per-file error containment, no "skip this product, warn about it" path.

**Impact.** A typo in `data/products/moneta.md` takes down all six rhythms until Joe edits the file. With no logging (M-OPS-001), Joe sees a Python traceback and has to read it to find the offending file.

**Why MINOR.** Input layer is human-curated and small; rare failure mode. But the absence of a fail-soft path is structurally inconsistent with the bridge's fail-soft posture for Harlo (M-OPS-002).

---

#### N-OPS-003 — Brief body construction is not deterministic across runs in the same minute

**Evidence.**
- `scripts/first_hanna_brief.py:138` — `composed_at_iso = datetime.now(timezone.utc).isoformat()`. Sub-second precision: `2026-05-29T14:23:41.123456+00:00`.
- Two runs within the same minute produce two different `composed_at_iso` values → two different rows → two different briefs that say nearly the same thing.

**Impact.** Tied to B-OPS-002 (no idempotency key). Worth surfacing separately because the *cause* is a now()-call on the hot path of brief construction, not a row-insert decision. A UUID derived from `(phase, day-bucket)` would solve both.

**Why MINOR.** Symptom of B-OPS-002.

---

#### N-OPS-004 — `last_stderr()` ring is captured but never surfaced

**Evidence.**
- `src/harlo_bridge.py:67` — `self._stderr_ring: collections.deque[str] = collections.deque(maxlen=64)`.
- `src/harlo_bridge.py:173-174` — `last_stderr() -> list[str]: return list(self._stderr_ring)`.
- `grep -rn "last_stderr" /home/user/Hanna/scripts/ /home/user/Hanna/src/` returns only the definition; no caller. Tests under `tests/test_harlo_bridge.py` presumably cover it, but no production code path reads it.

**Impact.** D005.3's investment in a stderr drainer is wasted — the surface exists but is unread. When `_read_harlo` swallows `HarloUnreachable`, the captured stderr is collected, returned via `__exit__` cleanup … and dropped.

**Why MINOR.** Bug-shaped — the infrastructure is there, the caller is missing.

---

#### N-OPS-005 — `data/products/` filename is the product identity but is not validated against frontmatter

**Evidence.**
- `scripts/first_hanna_brief.py:78-82` iterates `PRODUCTS_DIR.glob("*.md")` and parses each. The frontmatter `product:` field is the identity used downstream (`by_name = {p.product: p for p in products}` at line 137).
- A file `data/products/moneta.md` whose frontmatter says `product: monet` will silently bind under the wrong name. No check that the filename stem matches the frontmatter key.

**Impact.** Hand-typed product files drift; the brief composer references a product Joe doesn't recognize. Low probability, but no validation.

**Why MINOR.** Hygiene issue; trivial 3-line check.

---

## Out-of-Scope (noticed but not owned by scout-ops)

- **Documentation drift on the "always-on" claim.** `README.md:5` and `HANNA_BLUEPRINT.md:59` are stale relative to `docs/DECISIONS.md:330` — scout-docs territory. Surfaced here only because the *operational* consequence is severe (B-OPS-001).
- **`src/channels/calendar.py` design.** L4b lane definition (`docs/ROADMAP.md:239-271`) does not currently specify retry semantics, dedup keys, or rollback for the AppleScript subprocess call. Architectural concern; scout-architecture / scout-lanes-schemas. Surfaced here because B-OPS-002 will recur in the calendar surface.
- **Compliance grep coverage.** `.github/workflows/ci.yml:24-55` checks Rule 35 / 37 / 1 via `grep`. No grep checks that `override_token` is implemented if `RULES.md:187` references it. Out of scope for ops; surfaces in scout-security-rules.
- **`compute_producer_phase` timezone discipline** (Read at `src/computations/compute_producer_phase.py:28` — requires tz-aware datetime). Looks correct; flagged for scout-code-quality / scout-tests.

---

## Proposed belief deltas

(orchestrator validates and writes to `state/beliefs.md`; subagent never writes that file)

- **claim:** Hanna's headline operational claim ("always-on AI producer") is structurally unbacked today — there is no scheduler in the repository (no cron, launchd, systemd, or self-trigger); both `scripts/first_hanna_brief.py` and `bin/hanna-brief.command` are manual-invocation only. The claim becomes real only when L4b ships AND a scheduling substrate is chosen (not currently in any lane).
  **suggested_confidence:** 0.95
  **evidence:** `grep -rE "cron|launchd|systemd|\.plist|daemon|crontab"` returns no scheduler hits; `bin/hanna-brief.command:34` opens HTML mockup only; `HANNA_BLUEPRINT.md:25` Audit Finding #4 acknowledges the contradiction; `docs/DECISIONS.md:330` defers the operationalization to "once `src/channels/calendar.py` lands" without naming the trigger mechanism.

- **claim:** Hanna has no observability infrastructure — zero `logging` imports, zero structured-log surface, zero metrics, no health probe, no callable status check; the only diagnostic data captured (HarloBridge `_stderr_ring`) is never read by any production caller.
  **suggested_confidence:** 0.95
  **evidence:** `grep -rn "import logging|logger|logging\." src/ scripts/` returns 0 hits; `grep -rn "last_stderr" src/ scripts/` returns only definition + tests; no `--health` or `--ping` mode exists on any script; M-OPS-001 + M-OPS-004 + N-OPS-004 in this artifact.

- **claim:** `BriefPayload` lacks an idempotency token and `briefs` SQLite schema lacks a UNIQUE constraint, so the inbound L4b calendar publish surface has no safe retry semantics. Duplicate brief rows and duplicate calendar events are the default failure mode of any retry.
  **suggested_confidence:** 0.9
  **evidence:** `src/schemas.py:131-136` `BriefPayload` fields; `scripts/first_hanna_brief.py:34-42` schema (AUTOINCREMENT id only); `scripts/first_hanna_brief.py:163-167` plain INSERT; `docs/ROADMAP.md:247` `publish(brief: BriefPayload) -> CalendarEventId` signature with no dedup-key input; B-OPS-002 in this artifact.

- **claim:** Rule 34's `override_token` mechanism is spec-only — there is no implementation, no HMAC key, no secrets-management surface, and no test surface in the repository. The "Bypassing any layer fails CI" claim in RULES.md is unenforceable.
  **suggested_confidence:** 0.9
  **evidence:** `grep -rn "override_token|HMAC|hmac" src/ scripts/` returns 0 hits; `grep -rn "os.environ|getenv" src/ scripts/` returns 0 hits; no crypto dependency in `pyproject.toml`; M-OPS-003 in this artifact. (Confidence not 1.0 because Layer 3 is deferred to L6 per `RULES.md:15`, so the absence may be deliberate. The unenforceable CI claim is still active.)

- **claim:** The Harlo-bridge failure path degrades silently to state-blind with no out-of-band notification to Joe and no alerting surface that watches `harlo_reachable=0` rows.
  **suggested_confidence:** 0.85
  **evidence:** `scripts/first_hanna_brief.py:53-58` swallows `HarloUnreachable` + `HarloTimeout`; line 91 announces degradation only in brief body; no notification, alerting, or escalation surface exists in the repo; `HarloProtocolError` is not caught and crashes the script entirely; M-OPS-002 in this artifact.

---

## Open questions surfaced

- **q-ops-1:** What is Hanna's chosen scheduling substrate (launchd plist on macOS / Apple Shortcuts automation / a `Hanna.app` LaunchAgent / a cron line)? L4b ships calendar.py but the trigger mechanism that fires `publish-now` at 09:01 ET is unowned. Closing this question is a precondition for B-OPS-001 resolution and for the README's headline claim to be true.

- **q-ops-2:** What is the idempotency-key shape for `BriefPayload` — is it (phase, calendar-day, timezone) deterministic, or a UUID4 stored alongside the row? Either resolves B-OPS-002; the decision dictates the SQLite schema migration and the `publish(brief) -> CalendarEventId` retry contract.

- **q-ops-3:** Does Rule 34's `override_token` mechanism ship before, with, or after L6 (`mcp_tools`)? RULES.md:15 says Layer 3 (per-tool gating) is deferred to L6, but the override token is the bypass for *all three layers*. If L6 lands without an override implementation, Hanna goes operational with a documented bypass surface that doesn't exist — a compliance artifact contradicting code.

---

## Methodology / scope notes

- Audited against `RULES.md` Rules 18, 34, 35, 36, 37; `docs/DECISIONS.md` D001/D005/D006/D008; `HANNA_BLUEPRINT.md` §7, §11.1, §12 Audit Log; the compliance greps in `RULES.md:222-237`.
- Audit trailer hygiene: spot-checked `scripts/first_hanna_brief.py:1` (cloned trailer present), `src/harlo_bridge.py:1` (cloned trailer present), `src/schemas.py:1` (fresh seed, no trailer — correct per D003/D004). No model-id strings found in committed artifacts.
- Read-only. No source modifications. Findings artifact is the sole write.
