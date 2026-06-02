# scout-code-quality — findings

**Scope:** Python code quality from first principles across `src/` (4 modules) and
`scripts/first_hanna_brief.py`. Out of scope per delegation: tests, architecture,
docs, ops, security, lanes/schemas.

**Files audited (all read in full):**

- `/home/user/Hanna/src/__init__.py` (empty, 1 line)
- `/home/user/Hanna/src/schemas.py` (137 lines)
- `/home/user/Hanna/src/harlo_bridge.py` (386 lines)
- `/home/user/Hanna/src/computations/__init__.py` (comment only)
- `/home/user/Hanna/src/computations/compute_producer_phase.py` (43 lines)
- `/home/user/Hanna/src/computations/compute_brief_priority.py` (92 lines)
- `/home/user/Hanna/scripts/first_hanna_brief.py` (185 lines)

Total: ~445 lines of behavioral Python. Code is materially clean; findings are
predominantly MINOR. The one MAJOR is a latent input-validation gap in
`ProductFile.parse`.

---

## BLOCKER

*None.* The code does not contain anything that should stop a release. The
known race-risk in `_recv_buffer` was specifically checked (delegation ask) and
is **safely contained**: `_read_frame` is only called from `_rpc` /
`_send_notification` (lines 248, 260), both of which already hold `self._lock`
for the entire read; `close()` also acquires the lock before clearing the
buffer (line 87). The conversion from `@staticmethod` to instance method in
298f50c does not introduce any new concurrency surface.

---

## MAJOR

### M1 — `ProductFile.parse` has multiple silent-coercion / silent-drop input gaps (`src/schemas.py:53–102`)

The parser is a hand-rolled YAML-ish frontmatter reader. The delegation
explicitly asked about YAML escapes / unicode / empty bullet lines; I confirmed
the following are not handled and will silently misbehave rather than raise:

1. **Frontmatter quoting is not stripped.** A canonical YAML file with
   `product: "harlo"` or `product: 'harlo'` will produce a `ProductFile.product`
   field of literal `"harlo"` (with surrounding quotes), which will then never
   match any lookup in `by_name` in `first_hanna_brief.py:108`. Result: that
   product silently disappears from the brief. There is no test asserting
   quoted values are rejected.
2. **Duplicate frontmatter keys silently overwrite.** Line 72
   (`frontmatter[key.strip()] = value.strip()`) takes last-write-wins with no
   warning. A malformed file with two `status:` lines silently keeps the
   second.
3. **Unknown section headers are silently dropped.** Lines 79–83 only honor
   the four entries in `_KNOWN_SECTIONS`; a typo like `## Blocker` (singular)
   produces no warning and the entire body of that section is lost. This is a
   particularly dangerous failure mode because Joe will see a brief that
   *appears* to have parsed correctly.
4. **Empty bullet lines (`- `) become empty strings in `blockers`.** Line 113
   accepts the prefix `"- "` and then `stripped[2:].strip()` yields `""`. The
   composer (`_blockers_line`) will then emit `"<name>: "` — a visible bug in
   the rendered brief.
5. **`_parse_forcing_function` fallback is asymmetric.** Lines 122–128: if a
   bullet has `": "` it uses it; if it has exactly one `":"` (no space) it
   uses that; if it has zero or ≥2 colons with no `": "`, the entire bullet
   becomes `description` with `date_iso=""`. The 298f50c round-3 fix correctly
   handled ISO datetimes with `": "`, but a malformed `2026-13-99: bad date`
   silently lands a forcing function with `date_iso="2026-13-99"`. The
   downstream `compute_brief_priority._min_working_days_to_forcing_function`
   does swallow it via `try: date.fromisoformat(...) except ValueError:
   continue`, but the bad data still persists into `BriefPayload.approaching`
   for any rendering path that uses it (e.g. `_approaching_line` will print
   the malformed date).
6. **Unicode is not explicitly validated.** Practically `text.splitlines()`
   handles Unicode fine, but the file does not normalize (NFC vs. NFD) or
   reject control characters in YAML frontmatter values. A product name with
   trailing whitespace inside the quoted form, or with `​`
   (zero-width-space), will silently mismatch any `by_name` lookup.

The class is `@dataclass(frozen=True)` and has good post-parse immutability,
but parse itself is the soft spot. The schema also has no `__post_init__`
validating that `status` is non-empty, `product` is non-empty, or
`last_review_iso` parses as a date — `ProductStatus(...)` will raise on bad
status, but the other two pass through.

This is MAJOR (not BLOCKER) because: (a) inputs are author-controlled by Joe
who writes the `.md` files himself, and (b) the failure mode is "brief is
silently incomplete" rather than crash. But Rule 36 ("surface, don't decide")
*depends* on the brief being a faithful read of the portfolio surface — silent
drops violate that posture.

---

## MINOR

### m1 — `_drain_stderr` catches bare `Exception` (`src/harlo_bridge.py:200`)

```
try:
    text = line.decode("utf-8", errors="replace").rstrip("\r\n")
except Exception:
    text = repr(line)
```

`line.decode(..., errors="replace")` cannot raise — `errors="replace"` is the
infallible path. The `except Exception` here is dead. Either remove the
try/except or narrow it to `UnicodeDecodeError` (which can only fire if the
errors mode is changed). This is the only `except Exception:` in the
codebase, so the exception-hygiene story is otherwise very clean.

### m2 — `ZoneInfo("America/New_York")` is constructed in three places

- `src/computations/compute_producer_phase.py:11` (module-level `_ET`)
- `src/computations/compute_brief_priority.py:10` (module-level `_ET`)
- `scripts/first_hanna_brief.py:46` (inline literal in `_phase_now`)

The literal in `first_hanna_brief.py` should re-use one of the module-level
`_ET` constants (or, better, a shared `src.constants.ET`). Not load-bearing;
purely a refactor opportunity that would prevent a future "we moved off ET"
fix from missing a site.

### m3 — Magic sentinels `99` and `"9999-99-99"` in `first_hanna_brief.py`

- Line 100: `_STATUS_DISPLAY_ORDER.get(kv[0], 99)` — the `99` is a "sort to
  end" sentinel.
- Line 116: `triple[0] or "9999-99-99"` — string-compare sentinel for sorting
  empty `date_iso` to the end.

Both are correct, but they should be named constants (e.g.
`_UNKNOWN_STATUS_SORT_KEY = 99`, `_NO_DATE_SORT_KEY = "9999-99-99"`) — a
future reader has to do non-trivial inference today.

### m4 — `_STATUS_DISPLAY_ORDER` uses `.value` strings rather than enum members (`first_hanna_brief.py:23–28`)

```
_STATUS_DISPLAY_ORDER = {
    ProductStatus.IN_FLIGHT.value: 0,
    ...
}
```

Then at line 100 the key is `kv[0]` which is a string (Counter is keyed by
`p.status.value` at line 99). This works because `ProductStatus(str, Enum)` —
but it's a refactor smell. Keying the dict directly by `ProductStatus`
members and using `Counter(by_name[name].status for name in ranked)` would
preserve the type information end-to-end. Today the value is round-tripped
through strings for no reason.

### m5 — `compute_producer_phase` has an unused parameter (`src/computations/compute_producer_phase.py:14`)

`prev_phase: ProducerPhase` is parameter 2 but the function body never reads
it (the inline comment at line 26 acknowledges this). Two options: (a) prefix
with `_` (`_prev_phase`) per the Python convention for intentionally-unused
parameters, or (b) drop it and document in the docstring that hysteresis is
deferred. Today the signature reads as if hysteresis exists. Callers
(`first_hanna_brief.py:46`) pass a hardcoded `ProducerPhase.MORNING` which
itself is suspicious — looks like a placeholder but is silent.

### m6 — Conditional cascade in `compute_producer_phase` is ordered-dependent and untyped

Lines 30–42 are seven sequential `if` returns. This is fine functionally but
the ordering (monthly > weekly > daily) is load-bearing and undocumented.
Consider a small lookup table or comments at the head of the function noting
the precedence rules. The function is short enough that this is genuinely
MINOR.

### m7 — `_blockers_line` lists *all* blockers across *all* ranked products with no cap (`first_hanna_brief.py:121–131`)

Compare to `_approaching_line` (line 117) which caps to `entries[:3]`.
Inconsistent: a portfolio with 12 in-flight items each with 3 blockers
produces a 36-item single-line dump. Should probably cap to a small N
(consistent with `_approaching_line`) or break across lines.

### m8 — `_state_line` has two near-identical "reachable" branches (`first_hanna_brief.py:85–91`)

The pattern "if reachable and burnout, X; if reachable, Y; else Z" is fine
but the indentation makes the third (else) branch read like a peer of the
inner-`if`. A single match-style dispatch on `(reachable, burnout)` would
read more clearly.

### m9 — `_persist` does not parameterize the table name and re-runs `CREATE TABLE IF NOT EXISTS` every call (`first_hanna_brief.py:159–167`)

Idempotent and harmless, but if this script runs at brief-rhythm cadence
(~6×/workday per BLUEPRINT §12.1) the schema check is wasted I/O. Standard
pattern is to initialize the schema in a separate `_ensure_schema()` callable
once per process. MINOR because this is currently a one-shot PoC script.

### m10 — `_compose_brief` interpolates four sub-render strings whose return contracts are inconsistent

`_state_line`/`_portfolio_line` return non-empty strings; `_approaching_line`
and `_blockers_line` return `""` when they have nothing to say *or* a string
ending in `". "`. The brief body (lines 145–150) then concatenates them with
no separator. This works only because the empty-returners reliably return
`""`, but the implicit contract (each fragment must end with `". "` or be
exactly `""`) is undocumented. A `Fragment` dataclass with a `.render()`
method, or a list-of-strings + `" ".join(filter(None, ...))`, would make this
robust. Testability ask in delegation: each sub-render is currently
straightforward to test in isolation (good), but the integration contract is
fragile.

### m11 — `_recv_buffer: bytearray` exposes mutable state outside the lock in `close()` (`src/harlo_bridge.py:99`)

`close()` does `self._recv_buffer.clear()` inside the lock — correct. But
`_read_frame_with_timeout` at line 322 does `buf = bytearray(self._recv_buffer)`
which makes a copy (good) and at line 323 `self._recv_buffer.clear()` (also
inside the lock-held `_rpc`). The pattern is safe today, but it is fragile
to a future refactor that calls `_read_frame` outside `_rpc`. Consider an
explicit `assert self._lock._is_owned()` (using `RLock._is_owned`, which is
private API but standard for assertions) or factor the buffer access into a
single `_take_recv_buffer()` helper that requires the lock.

### m12 — `_call_tool` swallows `KeyError` from `item["text"]` as a protocol error (`src/harlo_bridge.py:236`)

```
try:
    return json.loads(item["text"])
except (KeyError, json.JSONDecodeError) as e:
    raise HarloProtocolError(...)
```

This is functionally fine but mixes two error classes (missing-key and bad
JSON) under one message. Considering `_call_tool` already checked
`item.get("type") == "text"` at line 233, the absence of `text` is itself a
protocol bug worth a distinct message. MINOR.

### m13 — `_call_tool` returns `dict` but `json.loads` can return any JSON type (`src/harlo_bridge.py:235`)

The return annotation is `dict` but `json.loads(item["text"])` can produce a
list, str, int, bool, or None. If Harlo ever returns a JSON array as a
`tools/call` content body, this function returns a list typed as a dict, and
downstream `result["content"]` accesses will crash with a confusing
`TypeError`. Defensive: wrap with `if not isinstance(parsed, dict): raise
HarloProtocolError(...)`.

### m14 — `_min_working_days_to_forcing_function` early-exit threshold (`compute_brief_priority.py:78–91`)

`_working_days_between` returns early at `days_remaining >
_WORKING_DAYS_HORIZON` (line 89), but the caller at line 73 still does
`if best is None or days < best: best = days`. The early-exit value is
*at least* one past the horizon, which is correct for the
"is this within horizon?" gate at line 40 — but the function's name promises
the true working-day count, which it does not deliver past the horizon. The
name should be `_working_days_between_capped` or the function should
document this in a docstring.

### m15 — `compute_brief_priority` builds five intermediate lists then concatenates (`compute_brief_priority.py:31–58`)

Five status-keyed buckets is clear; consider whether a `defaultdict(list)`
keyed by status with a single ordered render at the end would be more
maintainable. The current shape works fine for four statuses; if more land,
the bucket-per-status pattern will start to repeat itself.

### m16 — Trailer hygiene: all four cloned files carry the canonical trailer; `src/schemas.py` correctly does not

Per D003/D004 + CONVENTIONS §2: confirmed clean. `harlo_bridge.py`,
`compute_producer_phase.py`, `first_hanna_brief.py`, and
`compute_brief_priority.py` all need a trailer (cloned content); only the
first three have one. **`compute_brief_priority.py` is missing the
attribution trailer** despite importing from `src.schemas` (fresh seed) but
landing computation logic that's plausibly Harlo-shaped per
ROADMAP §4 L4a. Out-of-scope for code quality and surfaced for the security/
trailer-hygiene scout (scout-security-rules); flagging here because the file
audit surfaced it. Note: `compute_brief_priority.py` may legitimately be a
fresh seed if L4a authored it from scratch rather than cloning — this needs
a session-log check, not a code-only judgment.

### m17 — `Path | None = None` for `ProductFile.path` is correct but the parse return discards info on failure

`parse()` raises `ValueError` with no `path` context. A caller iterating
multiple product files (e.g. `_read_product_files` at
`first_hanna_brief.py:74–82`) that hits a parse error gets `ValueError:
ProductFile.parse: missing closing frontmatter delimiter` with no indication
of which file. Wrap-and-rethrow with the path would help operators.

---

## Belief deltas (proposed)

1. **claim:** Hanna's behavioral Python (~445 LOC) has clean exception
   hygiene at the bridge boundary and pure-function discipline in
   `src/computations/`. The single MAJOR is in input parsing
   (`ProductFile.parse`), not in I/O or compute.
   **confidence:** 0.88
   **provenance:** Read all 7 .py files in full;
   exception audit at `src/harlo_bridge.py:93,194,200,217,236,271,297,306,315,336,338,349,369,371,378,383`
   shows 0 bare `except:` and 1 `except Exception:` (m1 — provably dead).
   `src/computations/compute_producer_phase.py` and
   `src/computations/compute_brief_priority.py` are referentially transparent
   modulo the documented `datetime.now(_ET)` default in
   `compute_brief_priority:29` (only fires when caller passes
   `today=None`).

2. **claim:** The frame-coalescing patch in 298f50c is correctly synchronized.
   `_recv_buffer` is mutated only in `_read_frame_with_timeout` (called from
   `_rpc`/`_send_notification`, both lock-held) and `close()` (lock-held).
   The static-to-instance method conversion did not introduce a race.
   **confidence:** 0.92
   **provenance:** `src/harlo_bridge.py:243` (`with self._lock` wraps both
   `_write_frame` and `_read_frame`), `:258` (same in
   `_send_notification`), `:87` (lock in `close()`). The bytearray is the
   sole shared mutable; all call sites are accounted for.

3. **claim:** `ProductFile.parse` is the structurally weakest module in the
   codebase. It silently coerces / drops at 6 distinct points (M1.1–M1.6),
   none of which are caught by the schemas' otherwise-strong
   `@dataclass(frozen=True)` posture. The composer downstream
   (`first_hanna_brief.py`) trusts the parser implicitly.
   **confidence:** 0.85
   **provenance:** `src/schemas.py:53–102` source + composer code paths at
   `first_hanna_brief.py:108–113,121–131` — composer does `by_name.get(name)`
   which silently returns `None` when names mismatch (line 108), and
   `_blockers_line` will format empty strings as `"<name>: "`.

4. **claim:** The codebase shows consistent use of modern Python idioms —
   `from __future__ import annotations` everywhere, `pathlib.Path` over
   `os.path`, `@dataclass(frozen=True)`, `IntEnum`/`str, Enum` mixins,
   `zoneinfo` over `pytz`, context managers for sqlite + subprocess. Type
   hints are present on every public signature. **The codebase is idiomatic
   modern Python.** Refactor opportunities are improvements, not corrections.
   **confidence:** 0.95
   **provenance:** Reviewed every import block; reviewed every function
   signature in all 7 files; reviewed `__enter__`/`__exit__` on `HarloBridge`
   (`src/harlo_bridge.py:75–84`) and `with sqlite3.connect(...)` at
   `scripts/first_hanna_brief.py:161`.

5. **claim:** Sub-renders in `first_hanna_brief.py` are *unit-testable* in
   isolation (each takes pure data and returns a string), but the
   *integration contract* between them (the trailing `". "` convention) is
   undocumented and fragile. A future composer rewrite will be hard to
   regression-test against today's output without a snapshot.
   **confidence:** 0.78
   **provenance:** `_state_line`, `_portfolio_line`, `_approaching_line`,
   `_blockers_line` at `first_hanna_brief.py:85–131`. Each accepts
   pure-data args (`bool`, `dict | None`, `list[str]`, `dict[str,
   ProductFile]`); `_compose_brief:145–150` concatenates with no separator
   and relies on each fragment's trailing space/period.

---

## Open questions surfaced

1. **Q-CQ-1: Should `ProductFile.parse` raise on unknown section headers,
   or silently drop them?** Today it silently drops. Rule 36 ("surface,
   don't decide") arguably requires the parser to surface
   "unknown section ## Blocker — did you mean ## Blockers?" rather than
   silently produce an incomplete brief. Resolves in tension with: the
   author's freedom to add notes/draft sections that aren't expected to
   render.

2. **Q-CQ-2: Is `compute_brief_priority._working_days_between`'s
   horizon-capped return value a feature or a bug?** Today it returns the
   first count past the horizon, which works for the boolean
   "within-horizon?" gate but lies about the count for ranking ties at
   exactly horizon+1. If two products both return `_WORKING_DAYS_HORIZON +
   1` for different reasons, they currently sort as equal-distance even
   when one is 6 working days out and the other is 30. Likely not yet
   load-bearing (only 4 products in the MVS) but worth resolving before the
   portfolio grows.

3. **Q-CQ-3: Should `HarloBridge._call_tool` validate that
   `json.loads(text)` returns a `dict` (m13), or is "Harlo always returns
   dicts at the tools/call boundary" a contract Hanna can rely on per the
   SPIKE_HARLO_EDGE doc?** If the latter, document the assumption inline;
   if the former, add the isinstance check. Same question applies to
   `_call_tool`'s annotated `-> dict` return.

---

## Out-of-scope but noticed (route to other scouts)

- **`compute_brief_priority.py` is missing the canonical attribution trailer**
  per D003/D004 + CONVENTIONS §2. Surfaced for **scout-security-rules** (or
  whichever scout owns trailer hygiene). May be intentional if L4a authored
  it as a fresh seed rather than cloning from Harlo — needs a session log
  check. (m16)

- **No test surface checked here.** All findings are about implementation
  code; whether tests catch these gaps belongs to **scout-tests**. Notable
  examples for that scout to verify: does any test exercise quoted YAML
  frontmatter values (M1.1)? Empty bullet lines (M1.4)? Unknown section
  headers (M1.3)?

- **`first_hanna_brief.py`'s `_phase_now` always passes
  `ProducerPhase.MORNING` as `prev_phase`** (`scripts/first_hanna_brief.py:46`).
  This is a placeholder that survived because m5 (unused parameter) made it
  harmless. Belongs to **scout-architecture** as a "v1 PoC inline does not
  yet plumb prev_phase from the persisted briefs table" gap.

- **No structured logging anywhere in the codebase.** `HarloBridge` has a
  stderr ring buffer (good) but no operational `logging`/`structlog`
  surface — falls to **scout-ops** for the lifecycle gap.

- **`_recv_buffer` and the `RLock` choice (`src/harlo_bridge.py:61`).**
  The `RLock` is justified inline ("first _rpc('initialize') is recursively
  invoked from _ensure_proc"). The recursion path is `_rpc → _ensure_proc →
  _rpc("initialize")`. This is a small architectural smell — startup is a
  recursive RPC — but is correctly handled. Surface to
  **scout-architecture** if they want to consider an unrolled startup.
