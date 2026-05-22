"""Tests for compute_brief_priority. Covers ranking heuristic and phase gating."""

from __future__ import annotations

from datetime import date

from src.computations.compute_brief_priority import compute_brief_priority
from src.schemas import ForcingFunction, ProducerPhase, ProductFile, ProductStatus


def _make(
    product: str,
    status: ProductStatus,
    approaching: list[ForcingFunction] | None = None,
) -> ProductFile:
    return ProductFile(
        product=product,
        status=status,
        last_review_iso="2026-05-22",
        approaching=approaching or [],
    )


_TODAY = date(2026, 5, 22)  # Friday


class TestComputeBriefPriority:
    def test_empty_product_list_returns_empty(self):
        assert compute_brief_priority([], ProducerPhase.MORNING, today=_TODAY) == []

    def test_all_in_flight_no_deadlines_sort_by_name(self):
        products = [
            _make("octavius", ProductStatus.IN_FLIGHT),
            _make("harlo", ProductStatus.IN_FLIGHT),
            _make("comfy_cozy", ProductStatus.IN_FLIGHT),
            _make("moneta", ProductStatus.IN_FLIGHT),
        ]
        result = compute_brief_priority(products, ProducerPhase.MORNING, today=_TODAY)
        assert result == ["comfy_cozy", "harlo", "moneta", "octavius"]

    def test_in_flight_before_exploring(self):
        products = [
            _make("octavius", ProductStatus.EXPLORING),
            _make("harlo", ProductStatus.IN_FLIGHT),
        ]
        result = compute_brief_priority(products, ProducerPhase.MORNING, today=_TODAY)
        assert result == ["harlo", "octavius"]

    def test_near_forcing_function_ranks_first(self):
        # 3 working days from Friday 2026-05-22 is Wed 2026-05-27
        products = [
            _make("harlo", ProductStatus.IN_FLIGHT),
            _make(
                "moneta",
                ProductStatus.IN_FLIGHT,
                approaching=[ForcingFunction("2026-05-27", "deadline")],
            ),
            _make("octavius", ProductStatus.IN_FLIGHT),
        ]
        result = compute_brief_priority(products, ProducerPhase.MORNING, today=_TODAY)
        assert result[0] == "moneta"
        assert set(result[1:]) == {"harlo", "octavius"}

    def test_near_forcing_function_sorted_by_proximity(self):
        # closer deadline ranks ahead of farther one
        products = [
            _make(
                "harlo",
                ProductStatus.IN_FLIGHT,
                approaching=[ForcingFunction("2026-05-28", "thursday")],
            ),
            _make(
                "moneta",
                ProductStatus.IN_FLIGHT,
                approaching=[ForcingFunction("2026-05-26", "tuesday")],
            ),
        ]
        result = compute_brief_priority(products, ProducerPhase.MORNING, today=_TODAY)
        assert result == ["moneta", "harlo"]

    def test_parked_and_shipped_excluded_for_daily_phases(self):
        products = [
            _make("harlo", ProductStatus.IN_FLIGHT),
            _make("moneta", ProductStatus.PARKED),
            _make("octavius", ProductStatus.SHIPPED),
        ]
        for phase in (
            ProducerPhase.MORNING,
            ProducerPhase.MIDDAY,
            ProducerPhase.EVENING,
        ):
            result = compute_brief_priority(products, phase, today=_TODAY)
            assert result == ["harlo"], f"phase {phase} should drop parked + shipped"

    def test_parked_and_shipped_included_for_long_phases(self):
        products = [
            _make("harlo", ProductStatus.IN_FLIGHT),
            _make("moneta", ProductStatus.PARKED),
            _make("octavius", ProductStatus.SHIPPED),
        ]
        for phase in (
            ProducerPhase.WEEKLY_MONDAY,
            ProducerPhase.WEEKLY_FRIDAY,
            ProducerPhase.MONTHLY,
        ):
            result = compute_brief_priority(products, phase, today=_TODAY)
            assert result == ["harlo", "moneta", "octavius"], f"phase {phase} should keep tail"

    def test_family_lockout_returns_empty(self):
        products = [_make("harlo", ProductStatus.IN_FLIGHT)]
        assert compute_brief_priority(products, ProducerPhase.FAMILY_LOCKOUT, today=_TODAY) == []

    def test_far_forcing_function_not_treated_as_near(self):
        # 2026-07-01 is > 5 working days out; product stays in the "far" bucket
        products = [
            _make("alpha", ProductStatus.IN_FLIGHT),
            _make(
                "zeta",
                ProductStatus.IN_FLIGHT,
                approaching=[ForcingFunction("2026-07-01", "Q3 planning")],
            ),
        ]
        result = compute_brief_priority(products, ProducerPhase.MORNING, today=_TODAY)
        # No "near" bucket entry, so simple name sort applies
        assert result == ["alpha", "zeta"]

    def test_exploring_excluded_from_near_bucket(self):
        # Even with a near forcing function, EXPLORING never ranks above IN_FLIGHT
        products = [
            _make("zeta", ProductStatus.IN_FLIGHT),
            _make(
                "alpha",
                ProductStatus.EXPLORING,
                approaching=[ForcingFunction("2026-05-26", "soon")],
            ),
        ]
        result = compute_brief_priority(products, ProducerPhase.MORNING, today=_TODAY)
        assert result == ["zeta", "alpha"]

    def test_phase_changes_result_with_same_today(self):
        products = [
            _make("harlo", ProductStatus.IN_FLIGHT),
            _make("moneta", ProductStatus.PARKED),
        ]
        daily = compute_brief_priority(products, ProducerPhase.MORNING, today=_TODAY)
        weekly = compute_brief_priority(products, ProducerPhase.WEEKLY_MONDAY, today=_TODAY)
        assert daily == ["harlo"]
        assert weekly == ["harlo", "moneta"]
