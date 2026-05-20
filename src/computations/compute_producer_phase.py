# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
"""Pure function: compute producer phase transitions."""

from __future__ import annotations

from datetime import datetime

from src.schemas import ProducerPhase


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
    """Compute producer phase. Outside Mon–Fri 09–17 ET → FAMILY_LOCKOUT (Rule 34)."""
    if now.weekday() >= 5 or not (work_start_hour <= now.hour < work_end_hour):
        raise NotImplementedError("Session 03")
    if now.day == monthly_day:
        raise NotImplementedError("Session 03")
    if now.weekday() == 0 and now.hour == weekly_monday_hour:
        raise NotImplementedError("Session 03")
    if now.weekday() == 4 and now.hour == weekly_friday_hour:
        raise NotImplementedError("Session 03")
    if now.hour < morning_end_hour:
        raise NotImplementedError("Session 03")
    if now.hour < midday_end_hour:
        raise NotImplementedError("Session 03")
    raise NotImplementedError("Session 03")
