"""Hanna producer-rhythm schemas. ProducerPhase + per-D007 input/output dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from pathlib import Path


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
    if ":" in bullet:
        date_part, _, description = bullet.partition(":")
        return ForcingFunction(date_iso=date_part.strip(), description=description.strip())
    return ForcingFunction(date_iso="", description=bullet.strip())


@dataclass(frozen=True)
class BriefPayload:
    phase: ProducerPhase
    composed_at_iso: str
    body_markdown: str
    referenced_products: list[str] = field(default_factory=list)
