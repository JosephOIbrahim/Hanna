# scout-security-rules — findings

ROLE: critic
MODE: red_team
TASK_ID: scout-security-rules
DATE: 2026-05-29
SCOPE: Rules 1–37 actual-vs-claimed, CI grep coverage, thread safety in `src/harlo_bridge.py`,
       SQLite write-path, input-validation surface, secrets posture.

---

## Executive summary

The currently load-bearing rules (18, 34 layer 1, 35, 36, 37) are enforced in code, and CI greps
cover Rules 1, 35, 37 with the right zero-result semantics. The compliance posture is materially
better than the per-rule annotation in `RULES.md` reads: there is no "Not yet load-bearing"
annotation anywhere on Rules 1–17, 19–33 (the note is collective, not per-rule), and `RULES.md`
ships a check recipe (`grep -r "sleep(" python/hanna/`) that points at a non-existent path while
the *real* check (`grep -rn "sleep(" src/ scripts/`) lives only in CI. That mismatch is the
single biggest documentation/CI drift in this scope.

The Rule 34 (FAMILY_LOCKOUT) layer-1 logic is correct on weekday-hour math but has two latent
gaps: the `monthly_day == 1` branch in `compute_producer_phase` will *only* fire when the 1st is a
weekday *and* falls within 09:00–17:00 ET — fine — but `WEEKLY_MONDAY` and `WEEKLY_FRIDAY` use
`hour == 9` / `hour == 16` equality (not `<` ranges), giving each a 60-minute window and routing
the remaining hours to MORNING/EVENING. That is intentional per the source, but worth surfacing
as a design constraint, not a bug.

The Rule 35 grep posture catches `harlo.write|store|author|mutate` and the named cognitive-twin
methods, but a renamed mutating shim (e.g. `harlo.commit`, `harlo.persist`, `harlo.upsert`,
`harlo.recalibrate`) would slip through both CI nets. The bridge's *public* surface is read-only,
but obfuscation-resistant gating is not (MAJOR; see B-2).

The Harlo-bridge lock discipline is sound for the production path
(`_rpc → _read_frame → _read_frame_with_timeout` runs under `self._lock`), but the drainer
thread reads `_proc.stderr` *without* the lock, and `close()` `_proc = None` under the lock while
the drainer may still hold a reference to the old `_proc.stderr` — race surface is small but
non-zero (MINOR; see B-4). Tests bypass `_rpc` and call `_read_frame()` directly without holding
the lock — that's a test-only seam, not a production violation, but it documents an API the
production path implicitly forbids (MINOR; see B-5).

`override_token` is **spec-only**, openly acknowledged in `docs/REVIEW_2026-05-22.md:90` and
`docs/UI_UX_MAP.md:87`. No HMAC code exists in `src/` or `scripts/`. That is consistent with
D008.7's "applies on the session that lands the constrained component" posture — but it means
RULES.md:187 ("Tests verify all three layers. Bypassing any layer fails CI.") is currently
**aspirational**: only layer 1 is tested, and there is no layer-2/layer-3 test to bypass. MAJOR
documentation-vs-reality drift (B-1).

SQLite write path uses `sqlite3.connect(DB_PATH)` with no `journal_mode=WAL`, no
`PRAGMA synchronous=NORMAL`, default `isolation_level="DEFERRED"`, and no `timeout`. Single-writer
single-process today is fine, but the moment a second process (cron + MCP tool, or two MCP tools)
races on `data/hanna.sqlite`, the default 5-second SQLITE_BUSY timeout will surface as
exceptions. MAJOR for ops, MINOR for current usage (B-3).

Input-validation surface: `ProductFile.parse()` is a hand-rolled markdown frontmatter parser, not
PyYAML — so the "unsafe yaml" risk is structurally avoided. `glob("*.md")` is rooted at
`PRODUCTS_DIR` (no user-controlled path component), and `.private.md` is filtered. No path
traversal opportunity surfaces under the current call shape. (MINOR observation only — B-6.)

No Rule 37 hits in code paths the CI grep scans (`src/`, `scripts/`, `tests/`). The CI grep would
not catch `git log -p` content though — commit-message hygiene is enforced only by the
human-author convention in `CLAUDE.md`. Out of scope but noticed (B-7).

Two BLOCKERs, three MAJORs, four MINORs below.

---

## Findings

### BLOCKER

**B-0 [BLOCKER] — RULES.md compliance recipes point at non-existent path; CI greps don't match RULES.md greps.**

- `RULES.md:222–229` ships seven `grep -r "…" python/hanna/` recipes. **There is no `python/hanna/`
  directory in this repo** (`ls /home/user/Hanna` shows `src/`, `scripts/`, `tests/`,
  `crates/` is referenced but does not exist either). Anyone trusting RULES.md to verify
  compliance gets seven false-clean grep results.
- The producer-specific block at `RULES.md:234–236` is *closer* to ground truth (it targets
  `src/`) but still includes `python/hanna/` in the Rule 37 recipe.
- CI (`/.github/workflows/ci.yml:24–55`) implements the *real* checks against `src/ scripts/`
  (and `tests/` for Rule 37), so the binding is fine — but the recipes in RULES.md are wrong, and
  any operator running them manually will be misled.
- This is a BLOCKER because RULES.md is the load-bearing rule document — a wrong recipe in it
  is worse than no recipe at all. Rule documents must self-verify.

Evidence: `RULES.md` lines 222–229 (`python/hanna/` path), `crates/` references at 224–225;
actual layout `ls /home/user/Hanna/{src,scripts,tests}` shows the canonical paths.

**B-1 [BLOCKER] — RULES.md:187 asserts "Tests verify all three layers. Bypassing any layer fails CI." Layers 2 and 3 do not exist.**

- Layer 1 (`compute_producer_phase`) lockout: tested in
  `tests/computations/test_compute_producer_phase.py:17–30` (three boundary cases).
- Layer 2 (`HdProducer` delegate): Cut per D008.1 (load-bearing-rules annotation in
  `RULES.md:15`). No code, no test.
- Layer 3 (per-tool MCP gating): deferred to L6 `mcp_tools` lane (`RULES.md:15`). No code, no
  test.
- `override_token`: spec only (acknowledged at `docs/REVIEW_2026-05-22.md:90`,
  `docs/UI_UX_MAP.md:87`).
- The CI step "Lockout three-layer test (Rule 34) — see tests/test_integration/test_lockout.py"
  in `RULES.md:237` references a test file that **does not exist** (`find tests -name 'test_lockout*'`
  returns nothing).
- This is BLOCKER because the rule document promises a verification that's not in CI. A reader
  trusting RULES.md will believe lockout is hard-gated end-to-end when in fact only the pure
  function `compute_producer_phase` is verified.

Evidence: `RULES.md:187`, `RULES.md:237`, `tests/computations/test_compute_producer_phase.py`,
absence of `tests/test_integration/`.

### MAJOR

**M-1 [MAJOR] — Rule 35 grep is name-anchored; trivial rename defeats it.**

- CI step "Rule 35 — no forbidden Harlo writes" (ci.yml:25–29):
  `grep -rE "harlo\.(write|store|author|mutate)" src/ scripts/`.
- A renamed mutating shim — `harlo.commit`, `harlo.persist`, `harlo.upsert`, `harlo.set_*`,
  `harlo.update`, `harlo.recalibrate`, `harlo.apply`, `harlo.push`, `harlo.send` — passes.
- The cognitive-twin grep (ci.yml:31–35) catches three named methods
  (`stage_reload|resolve_verifications|trigger_cognitive_recalibration`) and `store_reflex` from
  RULES.md:228 — but a forth method added to Harlo's MCP surface is invisible.
- The *real* defense is that the bridge surface (`HarloBridge.read_*`, `recall`, `query_*`,
  `patterns`, `coach`) is enumerated and code-reviewed. The grep is a tripwire, not a contract.
  But RULES.md presents the grep as the contract.
- Confidence: HIGH that this is a documentation hygiene gap; LOW that it's currently exploitable
  (no Harlo write surface exists in code).

Evidence: `.github/workflows/ci.yml:24–35`, `src/harlo_bridge.py` public surface.

**M-2 [MAJOR] — `RULES.md` "Currently load-bearing rules" note is a single paragraph; no per-rule "Not yet load-bearing" annotation.**

- D008.7 (referenced at `RULES.md:13, 15`) ratified selective re-adoption: a rule is "Not yet
  load-bearing — applies on the session that lands the constrained component." That language is
  *referenced* in the prose but never *applied* to Rules 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14,
  15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33 individually.
- A reader scanning a single rule (say Rule 8 JSON BARRIER) sees no marker that it is currently
  inert in Hanna. They must read the meta-note at the top.
- This is MAJOR because the per-rule "Not yet load-bearing" annotation is what D008.7 promised.
  It's a discoverable-state problem: rules that look in force are not.
- Confidence: HIGH.

Evidence: `RULES.md:15` collective list; rules 1–33 carry no inline annotation.

**M-3 [MAJOR] — SQLite write path has no concurrency hardening.**

- `scripts/first_hanna_brief.py:159–167`: `sqlite3.connect(DB_PATH)` with no `timeout=`, no
  `isolation_level=` override, no `journal_mode=WAL` PRAGMA, no `synchronous=NORMAL` PRAGMA.
- Default `isolation_level="DEFERRED"` + rollback journal mode means: (a) a second writer (or a
  cron-driven brief that races with an MCP-driven brief) will see `sqlite3.OperationalError:
  database is locked` after 5 seconds; (b) the `with sqlite3.connect(...)` context manager
  commits *on success*, but `conn.execute(SCHEMA)` and `conn.execute("INSERT ...")` are inside
  a single implicit transaction, so a crash between them leaves a half-applied state if the
  schema migration evolves.
- Currently single-writer per session, so not exploitable today. But the moment Hanna grows a
  second writer (MCP `surface_brief` tool, scheduled DMN-style synthesis, a daemon), this is the
  next failure mode.
- Confidence: HIGH that this is a near-term ops gap; MEDIUM that it materializes in current usage.

Evidence: `scripts/first_hanna_brief.py:161–167`.

### MINOR

**B-4 [MINOR] — Drainer thread accesses `_proc.stderr` without `self._lock`; `close()` mutates `_proc` under lock.**

- `_drain_stderr` (harlo_bridge.py:187–202) reads `self._proc.stderr.readline()` on a hot loop,
  outside any lock.
- `close()` (harlo_bridge.py:86–99) sets `_drainer_stop`, terminates the process, then sets
  `self._proc = None` under `self._lock`.
- Race window: drainer is between `if self._proc is None` and `stderr = self._proc.stderr` —
  trivially `self._proc` could go None mid-line, raising `AttributeError`. Mitigated in practice
  because the drainer captures `stderr` once at line 190 *before* the loop. But if a future patch
  re-reads `self._proc.stderr` inside the loop, the race opens.
- Confidence: MEDIUM. Current code is safe-by-coincidence; the invariant (drainer captures
  `stderr` once, then never touches `self._proc`) is undocumented.

Evidence: `src/harlo_bridge.py:187–202` vs `:86–99`.

**B-5 [MINOR] — `_read_frame()` tests bypass `self._lock`; documents an API the production path implicitly forbids.**

- `tests/test_harlo_bridge.py:190, 202, 212, 221, 231, 240` call `HarloBridge()._read_frame(proc,
  timeout=...)` directly. No lock acquired. Production callers always enter through `_rpc()`
  (harlo_bridge.py:243–248) which holds the lock for both `_write_frame` and `_read_frame`.
- This is fine for the tests in isolation (no concurrent access), but it means `_read_frame_with_timeout`
  mutates `self._recv_buffer` (harlo_bridge.py:322–323, 359) without a held lock when called
  test-side. If a future test adds concurrency, this becomes a data race.
- Confidence: LOW for an immediate bug; MEDIUM that the test API will be reused unsafely.

Evidence: `src/harlo_bridge.py:243–248` (lock-held production path), `:322–323, 359`
(buffer mutation), `tests/test_harlo_bridge.py:190` (lock-free test call).

**B-6 [MINOR] — `ProductFile.parse` has no size/line cap; large or pathological inputs run unbounded.**

- `scripts/first_hanna_brief.py:81` calls `path.read_text()` then `ProductFile.parse(text)`.
- `ProductFile.parse` (`src/schemas.py:53–102`) splits lines, walks frontmatter to find the
  closing `---`, then walks sections. No max-line count, no max-file-size guard.
- A 10 MB `.md` file in `data/products/` would be fully loaded into RAM and parsed. Single-user
  workstation context: not currently exploitable. But the surface accepts arbitrary file content
  on the assumption Joe wrote it.
- Glob safety: `PRODUCTS_DIR.glob("*.md")` is anchored — no user-controlled prefix — so no path
  traversal opportunity. `path.name.endswith(".private.md")` is a substring filter, not a regex,
  so `comfy_cozy.private.md.md` would be processed (`.private.md` is not at end). Theoretical, not
  exploitable.
- Confidence: LOW for exploitability; MEDIUM as a posture observation.

Evidence: `src/schemas.py:53–102`, `scripts/first_hanna_brief.py:74–82`.

**B-7 [MINOR] — Rule 37 patent silence: code surface clean; commit-message grep not in CI.**

- CI step (ci.yml:36–41) greps `src/ scripts/ tests/` for `patent|provisional|uspto|claim
  language`. Returns clean today (verified by `grep -rEi "patent|…" src/ scripts/` — 0 hits).
- The grep does NOT scan `docs/`, `*.md` at root, or commit-message history. RULES.md:236 does
  list `docs/` in the manual recipe, but CI does not enforce it.
- `CLAUDE.md` declares Rule 37 covers commit messages, but there's no `prepare-commit-msg` hook
  or CI step that greps `git log -p` for the forbidden terms.
- Currently clean — only finding in `*.md` files is `PATENTS.md` referenced as a literal Harlo
  filename in `docs/SESSION_01_RECON.md:148`, which is a meta-reference (the substrate's own
  doc), not a topic.
- Confidence: HIGH that the surface is clean today; MEDIUM that the CI net is narrower than the
  rule claims.

Evidence: `.github/workflows/ci.yml:36–41`, `RULES.md:209–213, 236`, `CLAUDE.md` Patent topics
section.

---

## Rule-by-rule actual-vs-claimed (load-bearing only)

| Rule | Claimed | Actual | Status |
|------|---------|--------|--------|
| 18 (RED override) | "load-bearing via `read_burnout_level`" | `HarloBridge.read_burnout_level()` exists (harlo_bridge.py:126); no callers use the value to gate anything in `src/` or `scripts/` yet. The *exposure* is load-bearing, the *enforcement* is not. | PARTIAL |
| 34 layer 1 | "landed in `compute_producer_phase`" | Verified at `compute_producer_phase.py:30–31`; FAMILY_LOCKOUT returned for `weekday >= 5 or not (9 <= hour < 17)`. Test coverage: 3 lockout cases. | OK |
| 34 layer 2 | "Cut per D008.1" | No code; matches the Cut posture. | OK (Cut) |
| 34 layer 3 | "deferred to L6 `mcp_tools` lane" | No code; matches deferred posture. RULES.md:187 promise about CI is overstated (see B-1). | DEFERRED |
| 35 (cross-substrate writes) | "gated by Harlo bridge surface" | Bridge surface is read-only + coach (D001 carve-out). CI grep covers named methods only (M-1). | OK + tripwire-only |
| 36 (surface, don't decide) | "encoded in pure-enum returns" | `compute_brief_priority` returns `list[str]`; `compute_producer_phase` returns `ProducerPhase` enum. Composer voice in `first_hanna_brief.py:85–131`: I checked `_state_line`, `_portfolio_line`, `_approaching_line`, `_blockers_line` for directive imperatives — none found. "Surfacing this as observation — the call on what to pick up first is yours." at line 149 is the closing frame. | OK |
| 37 (patent silence) | "zero exceptions" | Code surface clean (verified by grep). Commit-message channel not CI-enforced (B-7). | OK in scope |

---

## Open questions

1. **Should `RULES.md` recipe paths be auto-synchronized with CI?** RULES.md:222–229 ships
   recipes pointed at `python/hanna/`. CI uses `src/ scripts/`. A single source of truth (likely
   CI as canonical, with RULES.md regenerated or stripped of paths) avoids B-0 recurring.
2. **What is the layer-2 / layer-3 / override-token roadmap?** RULES.md:187 currently asserts
   verification that does not exist. Is the right move (a) downgrade the language until L6 lands,
   (b) ship a stub `tests/test_integration/test_lockout.py` that documents the gap, or (c)
   accelerate L6? Surfacing — director's call.
3. **Multi-writer SQLite posture.** When the second writer surfaces (cron + MCP), what's the
   ordering: WAL + per-connection `timeout=`, or a single-writer mailbox process? Worth deciding
   before the second writer lands, not after.

---

## Proposed belief deltas (D003 evaluate-mode proposals; orchestrator integrates)

1. **claim:** "RULES.md compliance recipes are stale relative to CI"; **confidence:** 0.95;
   **provenance:** `RULES.md:222–229` references `python/hanna/`, repo has no such directory;
   `.github/workflows/ci.yml:24–55` uses `src/ scripts/`.
2. **claim:** "Rule 34 verification is one-layer, not three"; **confidence:** 0.92;
   **provenance:** `tests/computations/test_compute_producer_phase.py` (layer 1 only); no
   `tests/test_integration/test_lockout.py`; `override_token` documented as spec-only at
   `docs/REVIEW_2026-05-22.md:90`.
3. **claim:** "Bridge lock discipline is sound for the production path; tests document an unsafe
   seam"; **confidence:** 0.80; **provenance:** `src/harlo_bridge.py:243–248` (lock held over
   `_read_frame`), `tests/test_harlo_bridge.py:190` and siblings (direct call without lock).
4. **claim:** "SQLite write path will fail under concurrent writers without PRAGMA hardening";
   **confidence:** 0.85; **provenance:** `scripts/first_hanna_brief.py:161` — default
   `sqlite3.connect` with no timeout/journal_mode override.
5. **claim:** "Rule 35 CI grep is name-anchored and trivially defeated by rename"; **confidence:**
   0.90; **provenance:** `.github/workflows/ci.yml:24–35` grep regex enumerates four verbs +
   three named methods; no allow-list or audit on the bridge's exported names.

---

## Out-of-scope noticed (forwarded to other scouts)

- **scout-code-quality:** `_read_frame_blocking` is a `@staticmethod` but the dispatch from
  `_read_frame` at line 280 calls it via `HarloBridge._read_frame_blocking(proc)` — the
  static-vs-instance inconsistency (blocking is static, with-timeout is instance because of
  `_recv_buffer`) is a code-shape smell, not a bug.
- **scout-tests:** No test exercises `_read_frame_with_timeout` with a non-empty `_recv_buffer`
  seed (the frame-coalescing path D005.2 exists to defend). The body of the round-3 patch is
  not regression-tested.
- **scout-docs:** `RULES.md` would benefit from a tabular per-rule status column (load-bearing /
  not yet / Cut). The current single-paragraph note at line 15 is dense.
- **scout-ops:** No log line, no metric, no audit-trail entry on Rule 35 / Rule 37 grep failures
  beyond `::error::` annotations. Worth pairing with an audit log when ops layer lands.
- **scout-architecture:** `compute_producer_phase`'s `prev_phase` parameter is unused (line 26).
  D-ratified as "no hysteresis at v1" but still an arity smell.

---

## Audit trailer hygiene

- `src/harlo_bridge.py:1`, `src/computations/compute_producer_phase.py:1`,
  `scripts/first_hanna_brief.py:1` carry the canonical attribution trailer
  ("Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.") per D003/D004.
  OK.
- `src/computations/compute_brief_priority.py` and `src/schemas.py` have no clone trailer — they
  are fresh seeds per D004, which is consistent. OK.
- No model-id strings (e.g. `claude-opus-4-7`, `opus 4.7`) detected in committed artifacts within
  scope.

---

## End of findings.
