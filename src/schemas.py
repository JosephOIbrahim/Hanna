"""Hanna producer-rhythm schemas. Seed: ProducerPhase only (per NEXT.md option b)."""

from __future__ import annotations
from enum import IntEnum


class ProducerPhase(IntEnum):
    FAMILY_LOCKOUT = 0
    MORNING = 1
    MIDDAY = 2
    EVENING = 3
    WEEKLY_MONDAY = 4
    WEEKLY_FRIDAY = 5
    MONTHLY = 6
