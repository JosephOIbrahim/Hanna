"""Hanna producer-rhythm schemas. ProducerPhase + per-D007 input/output dataclasses."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum, IntEnum
from pathlib import Path
from zoneinfo import ZoneInfo

_ET = ZoneInfo("America/New_York")

# Per D010 phase→anchor table (ET):
#   MORNING=09:00, MIDDAY=12:00, EVENING=17:00,
#   WEEKLY_MONDAY=09:30, WEEKLY_FRIDAY=16:00,
#   MONTHLY=09:00 first weekday of month.
# FAMILY_LOCKOUT has no publish path → empty anchor.
_PHASE_ANCHOR_TIME: dict[int, time] = {
    1: time(9, 0),   # MORNING
    2: time(12, 0),  # MIDDAY
    3: time(17, 0),  # EVENING
    4: time(9, 30),  # WEEKLY_MONDAY
    5: time(16, 0),  # WEEKLY_FRIDAY
    6: time(9, 0),   # MONTHLY
}


class ProducerPhase(IntEnum):
    FAMILY_LOCKOUT = 0
    MORNING = 1
    MIDDAY = 2
    EVENING = 3
    WEEKLY_MONDAY = 4
    WEEKLY_FRIDAY = 5
    MONTHLY = 6


class ProductStatus(str, Enum):
    IN_FLIGHT = "in_flight"
    PARKED = "parked"
    SHIPPED = "shipped"
    EXPLORING = "exploring"


@dataclass(frozen=True)
class ForcingFunction:
    date_iso: str
    description: str


_KNOWN_SECTIONS = {
    "status": "status",
    "blockers": "blockers",
    "approaching forcing functions": "approaching",
    "notes": "notes",
}


@dataclass(frozen=True)
class ProductFile:
    product: str
    status: ProductStatus
    last_review_iso: str
    status_text: str = ""
    blockers: list[str] = field(default_factory=list)
    approaching: list[ForcingFunction] = field(default_factory=list)
    notes: str = ""
    path: Path | None = None

    @classmethod
    def parse(cls, text: str, path: Path | None = None) -> "ProductFile":
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            raise ValueError("ProductFile.parse: missing opening frontmatter delimiter")
        close_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                close_idx = i
                break
        if close_idx is None:
            raise ValueError("ProductFile.parse: missing closing frontmatter delimiter")
        frontmatter: dict[str, str] = {}
        for line in lines[1:close_idx]:
            stripped = line.strip()
            if not stripped:
                continue
            if ":" not in stripped:
                raise ValueError(f"ProductFile.parse: malformed frontmatter line: {stripped!r}")
            key, _, value = stripped.partition(":")
            frontmatter[key.strip()] = value.strip()
        for required in ("product", "status", "last_review_iso"):
            if required not in frontmatter:
                raise ValueError(f"ProductFile.parse: missing frontmatter key {required!r}")
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for line in lines[close_idx + 1:]:
            if line.startswith("## "):
                header = line[3:].strip().lower()
                current = _KNOWN_SECTIONS.get(header)
                if current is not None:
                    sections.setdefault(current, [])
            elif current is not None:
                sections[current].append(line)
        status_text = _join_section(sections.get("status", []))
        notes = _join_section(sections.get("notes", []))
        blockers = _parse_bullets(sections.get("blockers", []))
        approaching = [
            _parse_forcing_function(bullet)
            for bullet in _parse_bullets(sections.get("approaching", []))
        ]
        return cls(
            product=frontmatter["product"],
            status=ProductStatus(frontmatter["status"]),
            last_review_iso=frontmatter["last_review_iso"],
            status_text=status_text,
            blockers=blockers,
            approaching=approaching,
            notes=notes,
            path=path,
        )


def _join_section(body_lines: list[str]) -> str:
    return "\n".join(body_lines).strip()


def _parse_bullets(body_lines: list[str]) -> list[str]:
    bullets: list[str] = []
    for line in body_lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def _parse_forcing_function(bullet: str) -> ForcingFunction:
    # ISO datetimes contain `:` (e.g. `2026-06-01T10:30:00-04:00`); split on
    # the canonical `: ` delimiter first to preserve them. Fall back to a
    # single `:` only when no space follows (legacy/simple `YYYY-MM-DD:desc`).
    if ": " in bullet:
        date_part, description = bullet.split(": ", 1)
        return ForcingFunction(date_iso=date_part.strip(), description=description.strip())
    if bullet.count(":") == 1:
        date_part, description = bullet.split(":", 1)
        return ForcingFunction(date_iso=date_part.strip(), description=description.strip())
    return ForcingFunction(date_iso="", description=bullet.strip())


@dataclass(frozen=True)
class BriefPayload:
    phase: ProducerPhase
    composed_at_iso: str
    body_markdown: str
    referenced_products: list[str] = field(default_factory=list)
    # D010: ET-anchored ISO timestamp for the brief's rhythm-anchor (event start).
    phase_anchor_iso: str = ""
    # D012: SHA256-derived dedup key (16-char prefix); empty when phase_anchor_iso is empty.
    brief_id: str = ""

    @staticmethod
    def compute_phase_anchor_iso(phase: ProducerPhase, compose_date: date) -> str:
        """Return the ET-anchored ISO 8601 timestamp for the given phase + compose_date.

        Per D010 phase→anchor table. For MONTHLY, anchors to the first weekday of
        compose_date's month. For FAMILY_LOCKOUT, returns empty string (no publish).
        """
        if phase == ProducerPhase.FAMILY_LOCKOUT:
            return ""
        anchor_time = _PHASE_ANCHOR_TIME.get(int(phase))
        if anchor_time is None:
            return ""
        if phase == ProducerPhase.MONTHLY:
            anchor_date = _first_weekday_of_month(compose_date)
        else:
            anchor_date = compose_date
        return datetime.combine(anchor_date, anchor_time, tzinfo=_ET).isoformat()

    @staticmethod
    def compute_brief_id(
        phase: ProducerPhase,
        phase_anchor_iso: str,
        referenced_products: list[str],
    ) -> str:
        """Return the 16-char SHA256 prefix dedup key per D012.

        Key = sha256(phase.name + "|" + anchor_date_iso + "|" +
                     "|".join(sorted(referenced_products))).hexdigest()[:16]
        where anchor_date_iso is the date-portion (first 10 chars) of phase_anchor_iso.
        Returns empty string when phase_anchor_iso is empty (FAMILY_LOCKOUT path).
        """
        if not phase_anchor_iso:
            return ""
        anchor_date_iso = phase_anchor_iso[:10]
        sorted_products = "|".join(sorted(referenced_products))
        payload = f"{phase.name}|{anchor_date_iso}|{sorted_products}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _first_weekday_of_month(d: date) -> date:
    """Return the first Mon–Fri date of d's month."""
    candidate = date(d.year, d.month, 1)
    # weekday(): Mon=0 … Sun=6; weekday < 5 is Mon–Fri.
    while candidate.weekday() >= 5:
        candidate = date(candidate.year, candidate.month, candidate.day + 1)
    return candidate
