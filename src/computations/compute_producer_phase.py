# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
"""Pure function: compute producer phase transitions. Requires tz-aware datetime; normalized to ET."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.schemas import ProducerPhase

_ET = ZoneInfo("America/New_York")


def compute_producer_phase(
    now: datetime,
    prev_phase: ProducerPhase,
    work_start_hour: int = 9,
    work_end_hour: int = 17,
    morning_end_hour: int = 11,
    midday_end_hour: int = 14,
    weekly_monday_hour: int = 9,
    weekly_friday_hour: int = 16,
    monthly_day: int = 1,
) -> ProducerPhase:
    """Return the current ProducerPhase given a tz-aware datetime. Total over the seven enum members."""
    # prev_phase: unused at v1 — no hysteresis per ROADMAP §4 L3a
    if now.tzinfo is None:
        raise ValueError("compute_producer_phase requires a timezone-aware datetime")
    now = now.astimezone(_ET)
    if now.weekday() >= 5 or not (work_start_hour <= now.hour < work_end_hour):
        return ProducerPhase.FAMILY_LOCKOUT
    if now.day == monthly_day:
        return ProducerPhase.MONTHLY
    if now.weekday() == 0 and now.hour == weekly_monday_hour:
        return ProducerPhase.WEEKLY_MONDAY
    if now.weekday() == 4 and now.hour == weekly_friday_hour:
        return ProducerPhase.WEEKLY_FRIDAY
    if now.hour < morning_end_hour:
        return ProducerPhase.MORNING
    if now.hour < midday_end_hour:
        return ProducerPhase.MIDDAY
    return ProducerPhase.EVENING
