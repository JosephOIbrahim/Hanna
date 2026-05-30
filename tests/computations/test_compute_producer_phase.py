"""Tests for compute_producer_phase. Covers all seven ProducerPhase branches."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.computations.compute_producer_phase import compute_producer_phase
from src.schemas import ProducerPhase

_ET = ZoneInfo("America/New_York")


class TestComputeProducerPhase:
    def test_family_lockout_friday_boundary(self):
        assert compute_producer_phase(
            datetime(2026, 5, 22, 17, 0, tzinfo=_ET), ProducerPhase.MIDDAY
        ) == ProducerPhase.FAMILY_LOCKOUT

    def test_family_lockout_saturday_interior(self):
        assert compute_producer_phase(
            datetime(2026, 5, 23, 12, 0, tzinfo=_ET), ProducerPhase.MIDDAY
        ) == ProducerPhase.FAMILY_LOCKOUT

    def test_family_lockout_weekday_after_hours(self):
        assert compute_producer_phase(
            datetime(2026, 5, 20, 19, 0, tzinfo=_ET), ProducerPhase.EVENING
        ) == ProducerPhase.FAMILY_LOCKOUT

    def test_naive_datetime_rejected(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            compute_producer_phase(datetime(2026, 5, 23, 12, 0), ProducerPhase.MIDDAY)

    def test_morning_tuesday(self):
        assert compute_producer_phase(
            datetime(2026, 5, 26, 9, 30, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.MORNING

    def test_morning_wednesday(self):
        assert compute_producer_phase(
            datetime(2026, 5, 27, 10, 0, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.MORNING

    def test_morning_thursday_upper_boundary(self):
        assert compute_producer_phase(
            datetime(2026, 5, 28, 10, 59, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.MORNING

    def test_midday_tuesday_lower_boundary(self):
        assert compute_producer_phase(
            datetime(2026, 5, 26, 11, 0, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.MIDDAY

    def test_midday_wednesday(self):
        assert compute_producer_phase(
            datetime(2026, 5, 27, 12, 30, tzinfo=_ET), ProducerPhase.MIDDAY
        ) == ProducerPhase.MIDDAY

    def test_midday_thursday_upper_boundary(self):
        assert compute_producer_phase(
            datetime(2026, 5, 28, 13, 59, tzinfo=_ET), ProducerPhase.MIDDAY
        ) == ProducerPhase.MIDDAY

    def test_evening_tuesday_lower_boundary(self):
        assert compute_producer_phase(
            datetime(2026, 5, 26, 14, 0, tzinfo=_ET), ProducerPhase.MIDDAY
        ) == ProducerPhase.EVENING

    def test_evening_wednesday(self):
        assert compute_producer_phase(
            datetime(2026, 5, 27, 15, 30, tzinfo=_ET), ProducerPhase.EVENING
        ) == ProducerPhase.EVENING

    def test_evening_thursday_upper_boundary(self):
        assert compute_producer_phase(
            datetime(2026, 5, 28, 16, 59, tzinfo=_ET), ProducerPhase.EVENING
        ) == ProducerPhase.EVENING

    def test_weekly_monday_may25(self):
        assert compute_producer_phase(
            datetime(2026, 5, 25, 9, 0, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.WEEKLY_MONDAY

    def test_weekly_monday_june8(self):
        assert compute_producer_phase(
            datetime(2026, 6, 8, 9, 0, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.WEEKLY_MONDAY

    def test_weekly_monday_june15_mid_hour(self):
        assert compute_producer_phase(
            datetime(2026, 6, 15, 9, 30, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.WEEKLY_MONDAY

    def test_weekly_friday_may29(self):
        assert compute_producer_phase(
            datetime(2026, 5, 29, 16, 0, tzinfo=_ET), ProducerPhase.EVENING
        ) == ProducerPhase.WEEKLY_FRIDAY

    def test_weekly_friday_june5(self):
        assert compute_producer_phase(
            datetime(2026, 6, 5, 16, 0, tzinfo=_ET), ProducerPhase.EVENING
        ) == ProducerPhase.WEEKLY_FRIDAY

    def test_weekly_friday_june12_mid_hour(self):
        assert compute_producer_phase(
            datetime(2026, 6, 12, 16, 30, tzinfo=_ET), ProducerPhase.EVENING
        ) == ProducerPhase.WEEKLY_FRIDAY

    def test_monthly_may1(self):
        assert compute_producer_phase(
            datetime(2026, 5, 1, 10, 0, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.MONTHLY

    def test_monthly_july1(self):
        assert compute_producer_phase(
            datetime(2026, 7, 1, 12, 0, tzinfo=_ET), ProducerPhase.MIDDAY
        ) == ProducerPhase.MONTHLY

    def test_monthly_september1(self):
        assert compute_producer_phase(
            datetime(2026, 9, 1, 14, 0, tzinfo=_ET), ProducerPhase.EVENING
        ) == ProducerPhase.MONTHLY


class TestPhasePrecedence:
    """Documents the intentional MONTHLY > WEEKLY_MONDAY/FRIDAY > daily-phase precedence
    encoded by the conditional ordering in compute_producer_phase (per D013).
    When `now.day == monthly_day` AND the date is the first Monday/Friday at the weekly
    trigger hour, MONTHLY wins. The cost is one weekly slot per month gets "promoted" to a
    monthly brief on those days; this preserves the monthly cadence over the weekly slot."""

    def test_monthly_beats_weekly_monday_on_first_monday(self):
        # 2026-06-01 is a Monday AND day-of-month 1 (monthly_day default).
        # At weekly_monday_hour (09:00), MONTHLY must win over WEEKLY_MONDAY.
        assert compute_producer_phase(
            datetime(2026, 6, 1, 9, 0, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.MONTHLY

    def test_monthly_beats_weekly_friday_on_first_friday(self):
        # 2026-05-01 is a Friday AND day-of-month 1 (monthly_day default).
        # At weekly_friday_hour (16:00), MONTHLY must win over WEEKLY_FRIDAY.
        assert compute_producer_phase(
            datetime(2026, 5, 1, 16, 0, tzinfo=_ET), ProducerPhase.EVENING
        ) == ProducerPhase.MONTHLY

    def test_weekly_monday_fires_on_non_monthly_day(self):
        # 2026-06-08 is a Monday but NOT day-of-month 1.
        # WEEKLY_MONDAY fires normally at weekly_monday_hour (09:00).
        assert compute_producer_phase(
            datetime(2026, 6, 8, 9, 0, tzinfo=_ET), ProducerPhase.MORNING
        ) == ProducerPhase.WEEKLY_MONDAY
