"""Tests for the brief composer sub-renders in scripts/first_hanna_brief.py."""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pytest

from src.schemas import BriefPayload, ProducerPhase, ProductFile, ProductStatus

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "first_hanna_brief.py"

_spec = importlib.util.spec_from_file_location("first_hanna_brief", _SCRIPT_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
_portfolio_line = _module._portfolio_line
_persist = _module._persist


def _make(name: str, status: ProductStatus) -> ProductFile:
    return ProductFile(product=name, status=status, last_review_iso="2026-05-22")


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
