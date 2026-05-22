"""Tests for compute_producer_phase. Non-lockout branches land in Session 03."""

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

    def test_morning(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 20, 10, 0, tzinfo=_ET), ProducerPhase.MORNING)

    def test_midday(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 20, 13, 0, tzinfo=_ET), ProducerPhase.MIDDAY)

    def test_evening(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 20, 15, 0, tzinfo=_ET), ProducerPhase.EVENING)

    def test_weekly_monday(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 18, 9, 0, tzinfo=_ET), ProducerPhase.WEEKLY_MONDAY)

    def test_weekly_friday(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 22, 16, 0, tzinfo=_ET), ProducerPhase.WEEKLY_FRIDAY)

    def test_monthly(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 6, 1, 10, 0, tzinfo=_ET), ProducerPhase.MONTHLY)
