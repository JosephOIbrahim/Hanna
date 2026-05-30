"""Tests for src.schemas: ProductFile.parse, BriefPayload, ProductStatus."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path

import pytest

from src.schemas import (
    BriefPayload,
    ForcingFunction,
    ProducerPhase,
    ProductFile,
    ProductStatus,
)


_FULL_FILE = """---
product: harlo
status: in_flight
last_review_iso: 2026-05-22
---

## Status

Harlo bridge hardening landed last session.

## Blockers

- D005.3 stderr drainer needs test coverage
- Awaiting Joe ratification on next sprint

## Approaching forcing functions

- 2026-05-30: Q2 review presentation
- 2026-06-15: Vendor contract signing

## Notes

Bridge tests passing on local.
"""


_MINIMAL_STUB = """---
product: octavius
status: exploring
last_review_iso: 2026-05-22
---

## Status

## Blockers

## Approaching forcing functions

## Notes
"""


_MIXED_EMPTY = """---
product: moneta
status: parked
last_review_iso: 2026-05-22
---

## Status

Paused while Hanna stabilizes.

## Blockers

## Approaching forcing functions

- 2026-07-01: Q3 planning

## Notes
"""


class TestProductFile:
    def test_parse_full_file(self):
        pf = ProductFile.parse(_FULL_FILE)
        assert pf.product == "harlo"
        assert pf.status == ProductStatus.IN_FLIGHT
        assert pf.last_review_iso == "2026-05-22"
        assert "bridge hardening" in pf.status_text.lower()
        assert len(pf.blockers) == 2
        assert pf.blockers[0].startswith("D005.3")
        assert len(pf.approaching) == 2
        assert pf.approaching[0] == ForcingFunction("2026-05-30", "Q2 review presentation")
        assert pf.notes == "Bridge tests passing on local."

    def test_parse_minimal_stub(self):
        pf = ProductFile.parse(_MINIMAL_STUB)
        assert pf.product == "octavius"
        assert pf.status == ProductStatus.EXPLORING
        assert pf.status_text == ""
        assert pf.blockers == []
        assert pf.approaching == []
        assert pf.notes == ""

    def test_parse_mixed_empty_sections(self):
        pf = ProductFile.parse(_MIXED_EMPTY)
        assert pf.status == ProductStatus.PARKED
        assert "Paused" in pf.status_text
        assert pf.blockers == []
        assert len(pf.approaching) == 1
        assert pf.approaching[0].date_iso == "2026-07-01"
        assert pf.notes == ""

    def test_parse_records_path(self):
        target = Path("/tmp/harlo.md")
        pf = ProductFile.parse(_FULL_FILE, path=target)
        assert pf.path == target

    def test_parse_missing_frontmatter_raises(self):
        with pytest.raises(ValueError):
            ProductFile.parse("no frontmatter at all\n## Status\n")

    def test_parse_forcing_function_without_colon(self):
        text = """---
product: comfy_cozy
status: in_flight
last_review_iso: 2026-05-22
---

## Approaching forcing functions

- naked description without a date
"""
        pf = ProductFile.parse(text)
        assert pf.approaching[0].date_iso == ""
        assert "naked description" in pf.approaching[0].description

    def test_parse_forcing_function_with_iso_datetime(self):
        text = """---
product: harlo
status: in_flight
last_review_iso: 2026-05-22
---

## Approaching forcing functions

- 2026-06-01T10:30:00-04:00: launch window
- 2026-06-15: simpler date
"""
        pf = ProductFile.parse(text)
        assert len(pf.approaching) == 2
        # ISO datetime with `:` characters in the time portion is preserved
        # by splitting on `: ` (canonical delimiter), not on first `:`.
        assert pf.approaching[0].date_iso == "2026-06-01T10:30:00-04:00"
        assert pf.approaching[0].description == "launch window"
        # Legacy YYYY-MM-DD case still works.
        assert pf.approaching[1].date_iso == "2026-06-15"
        assert pf.approaching[1].description == "simpler date"


class TestProductStatus:
    def test_in_flight_value(self):
        assert ProductStatus.IN_FLIGHT.value == "in_flight"

    def test_parked_value(self):
        assert ProductStatus.PARKED.value == "parked"

    def test_shipped_value(self):
        assert ProductStatus.SHIPPED.value == "shipped"

    def test_exploring_value(self):
        assert ProductStatus.EXPLORING.value == "exploring"

    def test_membership(self):
        assert {s.value for s in ProductStatus} == {
            "in_flight",
            "parked",
            "shipped",
            "exploring",
        }


class TestBriefPayload:
    def test_minimal_construction(self):
        payload = BriefPayload(
            phase=ProducerPhase.MORNING,
            composed_at_iso="2026-05-22T09:00:00-04:00",
            body_markdown="# Morning",
        )
        assert payload.phase == ProducerPhase.MORNING
        assert payload.body_markdown == "# Morning"
        assert payload.referenced_products == []

    def test_with_referenced_products(self):
        payload = BriefPayload(
            phase=ProducerPhase.MIDDAY,
            composed_at_iso="2026-05-22T13:00:00-04:00",
            body_markdown="midday body",
            referenced_products=["harlo", "octavius"],
        )
        assert payload.referenced_products == ["harlo", "octavius"]

    def test_frozen_immutability(self):
        payload = BriefPayload(
            phase=ProducerPhase.EVENING,
            composed_at_iso="2026-05-22T18:00:00-04:00",
            body_markdown="evening body",
        )
        with pytest.raises(FrozenInstanceError):
            payload.body_markdown = "mutated"  # type: ignore[misc]


class TestComputePhaseAnchorIso:
    """D010: rhythm-anchor ISO timestamps per phase, anchored in ET."""

    def test_morning_anchors_at_0900_et_on_compose_date(self):
        compose_date = date(2026, 5, 22)  # Friday — irrelevant for MORNING anchor
        anchor = BriefPayload.compute_phase_anchor_iso(ProducerPhase.MORNING, compose_date)
        # ET on 2026-05-22 is EDT (-04:00).
        assert anchor == "2026-05-22T09:00:00-04:00"
        assert anchor.startswith("2026-05-22")  # date portion preserved
        assert "-04:00" in anchor or "-05:00" in anchor  # ET-anchored

    def test_midday_anchors_at_1200_et(self):
        compose_date = date(2026, 5, 22)
        anchor = BriefPayload.compute_phase_anchor_iso(ProducerPhase.MIDDAY, compose_date)
        assert anchor == "2026-05-22T12:00:00-04:00"

    def test_evening_anchors_at_1700_et_and_preserves_compose_date(self):
        compose_date = date(2026, 1, 15)  # winter → EST (-05:00)
        anchor = BriefPayload.compute_phase_anchor_iso(ProducerPhase.EVENING, compose_date)
        assert anchor == "2026-01-15T17:00:00-05:00"
        # Date portion matches input compose_date.
        assert anchor[:10] == "2026-01-15"


class TestComputeBriefId:
    """D012: SHA256-derived dedup keys."""

    def test_different_products_yield_different_ids(self):
        anchor = "2026-05-22T09:00:00-04:00"
        id_a = BriefPayload.compute_brief_id(ProducerPhase.MORNING, anchor, ["harlo"])
        id_b = BriefPayload.compute_brief_id(ProducerPhase.MORNING, anchor, ["octavius"])
        assert id_a != id_b
        assert len(id_a) == 16
        assert len(id_b) == 16

    def test_same_inputs_yield_same_id(self):
        anchor = "2026-05-22T09:00:00-04:00"
        products = ["harlo", "octavius", "moneta"]
        id_first = BriefPayload.compute_brief_id(ProducerPhase.MIDDAY, anchor, products)
        id_second = BriefPayload.compute_brief_id(ProducerPhase.MIDDAY, anchor, list(products))
        assert id_first == id_second
        # Product ordering is normalized via sort — different input order, same key.
        id_reordered = BriefPayload.compute_brief_id(
            ProducerPhase.MIDDAY, anchor, ["moneta", "harlo", "octavius"]
        )
        assert id_first == id_reordered
