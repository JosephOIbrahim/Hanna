"""Tests for the brief composer sub-renders in scripts/first_hanna_brief.py."""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pytest

from src.harlo_bridge import HarloTimeout, HarloUnreachable
from src.schemas import BriefPayload, ForcingFunction, ProducerPhase, ProductFile, ProductStatus

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "first_hanna_brief.py"

_spec = importlib.util.spec_from_file_location("first_hanna_brief", _SCRIPT_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
_portfolio_line = _module._portfolio_line
_persist = _module._persist
_main = _module.main
_state_line = _module._state_line
_approaching_line = _module._approaching_line
_blockers_line = _module._blockers_line
_compose_brief = _module._compose_brief

# Rule 36 voice: surface, don't direct. These imperatives must NEVER appear
# in any composer sub-render output that addresses Joe.
_DIRECTIVE_IMPERATIVES = (
    "you should",
    "you must",
    "you need to",
    "i recommend",
    "please ",
)


def _assert_no_directives(text: str) -> None:
    lowered = text.lower()
    for directive in _DIRECTIVE_IMPERATIVES:
        assert directive not in lowered, (
            f"Rule 36 violation: directive {directive!r} found in: {text!r}"
        )


def _make(name: str, status: ProductStatus) -> ProductFile:
    return ProductFile(product=name, status=status, last_review_iso="2026-05-22")


def _make_with_ffs(
    name: str, status: ProductStatus, ffs: list[ForcingFunction]
) -> ProductFile:
    return ProductFile(
        product=name,
        status=status,
        last_review_iso="2026-05-22",
        approaching=ffs,
    )


def _make_with_blockers(
    name: str, status: ProductStatus, blockers: list[str]
) -> ProductFile:
    return ProductFile(
        product=name,
        status=status,
        last_review_iso="2026-05-22",
        blockers=blockers,
    )


class TestPortfolioLine:
    def test_empty_ranked(self):
        assert _portfolio_line([], {}, ProducerPhase.MIDDAY) == (
            "The portfolio surface is empty — no product state has been logged yet."
        )

    def test_single_product(self):
        products = {"harlo": _make("harlo", ProductStatus.IN_FLIGHT)}
        result = _portfolio_line(["harlo"], products, ProducerPhase.MORNING)
        assert "1 in flight" in result
        assert "**harlo** (in flight)" in result
        assert "thread" not in result
        assert "other" not in result

    def test_mixed_status_surfaces_counts_by_status(self):
        products = {
            "harlo": _make("harlo", ProductStatus.IN_FLIGHT),
            "octavius": _make("octavius", ProductStatus.EXPLORING),
            "moneta": _make("moneta", ProductStatus.EXPLORING),
            "comfy_cozy": _make("comfy_cozy", ProductStatus.EXPLORING),
        }
        result = _portfolio_line(["harlo", "octavius", "moneta", "comfy_cozy"], products, ProducerPhase.MIDDAY)
        assert "1 in flight" in result
        assert "3 exploring" in result
        assert "**harlo** (in flight)" in result
        assert "threads are in flight" not in result
        assert result.index("1 in flight") < result.index("3 exploring")

    def test_uniform_status(self):
        products = {
            "harlo": _make("harlo", ProductStatus.IN_FLIGHT),
            "octavius": _make("octavius", ProductStatus.IN_FLIGHT),
            "moneta": _make("moneta", ProductStatus.IN_FLIGHT),
        }
        result = _portfolio_line(["harlo", "octavius", "moneta"], products, ProducerPhase.WEEKLY_MONDAY)
        assert "3 in flight" in result
        assert "**harlo** (in flight)" in result

    def test_rule_36_voice_no_directives(self):
        products = {
            "harlo": _make("harlo", ProductStatus.IN_FLIGHT),
            "octavius": _make("octavius", ProductStatus.EXPLORING),
        }
        result = _portfolio_line(["harlo", "octavius"], products, ProducerPhase.MIDDAY)
        for directive in ("you should", "you must", "you need to", "I recommend", "please"):
            assert directive.lower() not in result.lower()


class TestPersistIdempotency:
    """D012: re-invoking _persist with the same BriefPayload is a no-op on disk."""

    def test_double_persist_yields_single_row(self, tmp_path):
        db_path = tmp_path / "hanna_idem.sqlite"
        anchor = BriefPayload.compute_phase_anchor_iso(
            ProducerPhase.MORNING,
            __import__("datetime").date(2026, 5, 22),
        )
        brief_id = BriefPayload.compute_brief_id(
            ProducerPhase.MORNING, anchor, ["harlo", "octavius"]
        )
        brief = BriefPayload(
            phase=ProducerPhase.MORNING,
            composed_at_iso="2026-05-22T09:00:00-04:00",
            body_markdown="# morning",
            referenced_products=["harlo", "octavius"],
            phase_anchor_iso=anchor,
            brief_id=brief_id,
        )
        _persist(brief, harlo_reachable=True, db_path=db_path)
        _persist(brief, harlo_reachable=True, db_path=db_path)
        with sqlite3.connect(db_path) as conn:
            (count,) = conn.execute("SELECT COUNT(*) FROM briefs").fetchone()
        assert count == 1


class TestMainIntegration:
    """End-to-end coverage for scripts/first_hanna_brief.py main().

    Closes the c006 gap: previously only _portfolio_line was exercised.
    These tests drive main() against a tmp_path SQLite DB and assert
    on stdout + on-disk row state across the three observable paths
    (state-blind via HarloUnreachable, FAMILY_LOCKOUT early-exit,
    state-blind via HarloTimeout).
    """

    def _redirect_db(self, monkeypatch, tmp_path):
        db_path = tmp_path / "hanna.sqlite"
        monkeypatch.setattr(_module, "DB_PATH", db_path)
        return db_path

    def _stub_unreachable_bridge(self, monkeypatch):
        """Replace HarloBridge with a context-manager stub whose
        drive_coaching_exchange raises HarloUnreachable. _read_harlo's
        except clause then routes to the state-blind branch."""

        class _StubBridge:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def drive_coaching_exchange(self):
                raise HarloUnreachable("stubbed: subprocess not spawnable")

        monkeypatch.setattr(_module, "HarloBridge", _StubBridge)

    def _stub_timeout_bridge(self, monkeypatch):
        class _StubBridge:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def drive_coaching_exchange(self):
                raise HarloTimeout("stubbed: Harlo did not respond")

        monkeypatch.setattr(_module, "HarloBridge", _StubBridge)

    def test_main_state_blind_path_produces_brief_and_persists(
        self, monkeypatch, tmp_path, capsys
    ):
        db_path = self._redirect_db(monkeypatch, tmp_path)
        self._stub_unreachable_bridge(monkeypatch)
        # Pin the phase so the test does not flap with wall-clock drift.
        monkeypatch.setattr(_module, "_phase_now", lambda: ProducerPhase.MORNING)

        exit_code = _main()

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "# Hanna brief — morning" in captured.out
        assert "state-blind" in captured.out

        # One row, with the state-blind / phase fields the contract requires.
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT phase, harlo_reachable, brief_id, phase_anchor_iso "
                "FROM briefs"
            ).fetchall()
        assert len(rows) == 1
        phase, harlo_reachable, brief_id, anchor_iso = rows[0]
        assert phase == "morning"
        assert harlo_reachable == 0
        assert brief_id  # non-empty (MORNING has a non-empty anchor)
        assert anchor_iso  # non-empty for MORNING

        # D012: a second main() invocation in the same anchor day must
        # not yield a second row (INSERT OR IGNORE on brief_id).
        exit_code_2 = _main()
        assert exit_code_2 == 0
        with sqlite3.connect(db_path) as conn:
            (count,) = conn.execute("SELECT COUNT(*) FROM briefs").fetchone()
        assert count == 1

    def test_main_family_lockout_path_exits_cleanly(
        self, monkeypatch, tmp_path, capsys
    ):
        db_path = self._redirect_db(monkeypatch, tmp_path)
        monkeypatch.setattr(
            _module, "_phase_now", lambda: ProducerPhase.FAMILY_LOCKOUT
        )
        # Defence-in-depth: if the lockout branch ever fell through, this
        # bridge stub would surface the bug rather than spawning `harlo mcp`.
        self._stub_unreachable_bridge(monkeypatch)

        exit_code = _main()

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "FAMILY_LOCKOUT" in captured.out
        assert "paused" in captured.out.lower()
        # No SQLite file should have been created on the lockout branch —
        # _persist is never reached, so the DB parent dir is also untouched.
        assert not db_path.exists()

    def test_main_harlo_timeout_routes_to_state_blind(
        self, monkeypatch, tmp_path, capsys
    ):
        db_path = self._redirect_db(monkeypatch, tmp_path)
        self._stub_timeout_bridge(monkeypatch)
        monkeypatch.setattr(_module, "_phase_now", lambda: ProducerPhase.MORNING)

        exit_code = _main()

        assert exit_code == 0  # degrade, do not crash
        captured = capsys.readouterr()
        assert "# Hanna brief — morning" in captured.out
        assert "state-blind" in captured.out

        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT phase, harlo_reachable FROM briefs"
            ).fetchall()
        assert len(rows) == 1
        assert rows[0] == ("morning", 0)


class TestStateLine:
    """Closes c006: _state_line had zero direct unit coverage."""

    def test_state_blind_when_harlo_unreachable(self):
        # harlo_reachable=False routes through the state-blind branch
        # regardless of payload contents.
        result = _state_line(harlo_reachable=False, harlo_payload=None)
        assert "state-blind" in result
        # Rule 36: even in the degraded path, no directive imperatives.
        _assert_no_directives(result)

    def test_state_blind_payload_ignored_when_unreachable(self):
        # If reachable=False, a stale dict payload must still surface
        # state-blind — the unreachability flag is authoritative.
        stale_payload = {"v9": {"state": {"burnout": "RED"}}}
        result = _state_line(harlo_reachable=False, harlo_payload=stale_payload)
        assert "state-blind" in result
        assert "RED" not in result
        _assert_no_directives(result)

    def test_reachable_with_non_red_burnout_surfaces_level_neutrally(self):
        payload = {"v9": {"state": {"burnout": "GREEN"}}}
        result = _state_line(harlo_reachable=True, harlo_payload=payload)
        assert "GREEN" in result
        assert "state-blind" not in result
        # Neutral surfacing — no directive about what to do with GREEN.
        _assert_no_directives(result)

    def test_reachable_with_red_burnout_surfaces_without_directive(self):
        # Rule 18 (burnout-honest) + Rule 36 (no decision): the RED level
        # must be surfaced, but the line must not tell Joe what to do.
        payload = {"v9": {"state": {"burnout": "RED"}}}
        result = _state_line(harlo_reachable=True, harlo_payload=payload)
        assert "RED" in result
        _assert_no_directives(result)
        # No imperative verbs that would constitute a directive.
        for verb in ("stop ", "rest ", "take a break", "shut down"):
            assert verb not in result.lower()

    def test_reachable_with_no_burnout_falls_back_to_neutral_summary(self):
        # Payload reachable but lacks v9/state/burnout entirely.
        result = _state_line(harlo_reachable=True, harlo_payload={})
        assert "state-blind" not in result
        assert "reachable" in result.lower()
        _assert_no_directives(result)


class TestApproachingLine:
    """Closes c006: _approaching_line had zero direct unit coverage."""

    def test_no_products_with_forcing_functions_returns_empty(self):
        products = {
            "harlo": _make("harlo", ProductStatus.IN_FLIGHT),
            "octavius": _make("octavius", ProductStatus.EXPLORING),
        }
        result = _approaching_line(["harlo", "octavius"], products)
        # Composer convention: empty string signals "(none)" — the composer
        # concatenates the next line directly. This is the empty-equivalent.
        assert result == ""

    def test_single_forcing_function_surfaces_date_and_description(self):
        ff = ForcingFunction(date_iso="2026-06-01", description="ship 1.0")
        products = {
            "harlo": _make_with_ffs("harlo", ProductStatus.IN_FLIGHT, [ff]),
        }
        result = _approaching_line(["harlo"], products)
        assert "2026-06-01" in result
        assert "ship 1.0" in result
        assert "harlo" in result
        assert result.startswith("Approaching:")
        _assert_no_directives(result)

    def test_multiple_forcing_functions_sorted_by_date(self):
        # Later date placed first in the product to confirm sort-by-date,
        # not sort-by-input-order.
        ff_later = ForcingFunction(date_iso="2026-07-15", description="renewal")
        ff_earlier = ForcingFunction(date_iso="2026-06-02", description="demo")
        products = {
            "harlo": _make_with_ffs(
                "harlo", ProductStatus.IN_FLIGHT, [ff_later, ff_earlier]
            ),
        }
        result = _approaching_line(["harlo"], products)
        assert "2026-06-02" in result
        assert "2026-07-15" in result
        # Earlier date surfaces before the later one in the rendered string.
        assert result.index("2026-06-02") < result.index("2026-07-15")
        _assert_no_directives(result)

    def test_caps_at_three_entries(self):
        # The composer surfaces at most the 3 nearest FFs; a 4th entry
        # further out must NOT be surfaced (the heuristic that bounds
        # how much future Hanna projects into Joe's view).
        ffs = [
            ForcingFunction(date_iso="2026-06-01", description="a"),
            ForcingFunction(date_iso="2026-06-02", description="b"),
            ForcingFunction(date_iso="2026-06-03", description="c"),
            ForcingFunction(date_iso="2099-01-01", description="far_future"),
        ]
        products = {
            "harlo": _make_with_ffs("harlo", ProductStatus.IN_FLIGHT, ffs),
        }
        result = _approaching_line(["harlo"], products)
        assert "a" in result
        assert "b" in result
        assert "c" in result
        # The 4th, far-future FF is intentionally elided.
        assert "far_future" not in result
        assert "2099-01-01" not in result
        _assert_no_directives(result)

    def test_missing_product_in_by_name_is_skipped_gracefully(self):
        # ranked may reference a name not present in by_name (e.g. stale
        # cache); _approaching_line must not raise.
        result = _approaching_line(["ghost_product"], {})
        assert result == ""


class TestBlockersLine:
    """Closes c006: _blockers_line had zero direct unit coverage."""

    def test_no_blockers_anywhere_returns_empty(self):
        products = {
            "harlo": _make("harlo", ProductStatus.IN_FLIGHT),
            "octavius": _make("octavius", ProductStatus.EXPLORING),
        }
        result = _blockers_line(["harlo", "octavius"], products)
        assert result == ""

    def test_single_blocker_surfaces_product_and_text(self):
        products = {
            "harlo": _make_with_blockers(
                "harlo", ProductStatus.IN_FLIGHT, ["awaiting Anthropic review"]
            ),
        }
        result = _blockers_line(["harlo"], products)
        assert "harlo" in result
        assert "awaiting Anthropic review" in result
        assert result.startswith("Blockers:")
        _assert_no_directives(result)

    def test_two_products_with_blockers_both_attributed(self):
        products = {
            "harlo": _make_with_blockers(
                "harlo", ProductStatus.IN_FLIGHT, ["api key rotation"]
            ),
            "octavius": _make_with_blockers(
                "octavius", ProductStatus.EXPLORING, ["sandbox quota"]
            ),
        }
        result = _blockers_line(["harlo", "octavius"], products)
        # Both blockers surface, each attributed to its product.
        assert "harlo: api key rotation" in result
        assert "octavius: sandbox quota" in result
        _assert_no_directives(result)

    def test_multiple_blockers_on_one_product_all_surface(self):
        products = {
            "harlo": _make_with_blockers(
                "harlo",
                ProductStatus.IN_FLIGHT,
                ["blocker_one", "blocker_two"],
            ),
        }
        result = _blockers_line(["harlo"], products)
        assert "blocker_one" in result
        assert "blocker_two" in result
        _assert_no_directives(result)

    def test_missing_product_in_by_name_is_skipped_gracefully(self):
        # Same defensive contract as _approaching_line: a stale ranked entry
        # must not raise.
        result = _blockers_line(["ghost_product"], {})
        assert result == ""


class TestComposeBrief:
    """Closes c006: _compose_brief had zero direct unit coverage.

    These tests drive _compose_brief against the live data/products/ tree
    (4 product files exist). _compose_brief is a pure render — no SQLite,
    no Harlo subprocess — so the state-blind path is exercised by simply
    passing harlo_reachable=False without any monkeypatching.
    """

    def test_state_blind_morning_returns_populated_brief(self):
        brief = _compose_brief(
            phase=ProducerPhase.MORNING,
            harlo_reachable=False,
            harlo_payload=None,
        )
        assert isinstance(brief, BriefPayload)
        assert brief.phase == ProducerPhase.MORNING
        # Body is non-empty and includes the morning header + state-blind line.
        assert brief.body_markdown
        assert "# Hanna brief — morning" in brief.body_markdown
        assert "state-blind" in brief.body_markdown
        # D010: MORNING anchors to 09:00 ET on compose date — non-empty ISO.
        assert brief.phase_anchor_iso
        assert "T09:00" in brief.phase_anchor_iso
        # D012: brief_id is a non-empty 16-char SHA256 prefix.
        assert brief.brief_id
        assert len(brief.brief_id) == 16
        # referenced_products tracks the four on-disk product files.
        assert sorted(brief.referenced_products) == [
            "comfy_cozy",
            "harlo",
            "moneta",
            "octavius",
        ]
        # Rule 36: composed brief must not directive Joe.
        _assert_no_directives(brief.body_markdown)
        # Composer's closing line surfaces the choice as Joe's, not Hanna's.
        assert "yours" in brief.body_markdown.lower()

    def test_family_lockout_phase_yields_empty_anchor_and_brief_id(self):
        # Per D010 + D012: FAMILY_LOCKOUT has no publish path, so the
        # rhythm-anchor and the derived brief_id are both empty strings.
        brief = _compose_brief(
            phase=ProducerPhase.FAMILY_LOCKOUT,
            harlo_reachable=False,
            harlo_payload=None,
        )
        assert isinstance(brief, BriefPayload)
        assert brief.phase == ProducerPhase.FAMILY_LOCKOUT
        assert brief.phase_anchor_iso == ""
        assert brief.brief_id == ""
        # Body still composes (header reflects family_lockout) — _compose_brief
        # is a pure render; the lockout no-op decision lives in main().
        assert brief.body_markdown
        assert "family_lockout" in brief.body_markdown
        _assert_no_directives(brief.body_markdown)

    def test_state_blind_with_harlo_reachable_true_but_empty_payload(self):
        # Reachable + empty payload exercises the _state_line fallback
        # branch through _compose_brief (no burnout surfaced).
        brief = _compose_brief(
            phase=ProducerPhase.MIDDAY,
            harlo_reachable=True,
            harlo_payload={},
        )
        assert isinstance(brief, BriefPayload)
        assert "state-blind" not in brief.body_markdown
        assert "reachable" in brief.body_markdown.lower()
        # D010: MIDDAY anchors to 12:00 ET.
        assert "T12:00" in brief.phase_anchor_iso
        _assert_no_directives(brief.body_markdown)
