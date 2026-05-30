# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
"""scripts/first_hanna_brief.py — smaller day-zero PoC per HANNA_BLUEPRINT.md §11.1.

End-to-end: inline phase compute, one Harlo `coach` read via the bridge,
one persisted SQLite row, one composed brief to stdout. State-blind on
HarloUnreachable or HarloTimeout. No-op on FAMILY_LOCKOUT.
"""

from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from src.computations.compute_brief_priority import compute_brief_priority
from src.computations.compute_producer_phase import compute_producer_phase
from src.harlo_bridge import HarloBridge, HarloTimeout, HarloUnreachable
from src.schemas import BriefPayload, ProducerPhase, ProductFile, ProductStatus

# D011: catch HannaCalendarNotAvailable from L4b's future Calendar channel.
# Until src/channels/calendar.py lands, define a local stub class so the
# except-clause in main() is always wired and importable.
try:
    from src.channels.calendar import HannaCalendarNotAvailable  # type: ignore[import-not-found]
except ImportError:
    class HannaCalendarNotAvailable(Exception):
        """Stub: L4b's real exception class will replace this on import."""

_STATUS_DISPLAY_ORDER = {
    ProductStatus.IN_FLIGHT.value: 0,
    ProductStatus.EXPLORING.value: 1,
    ProductStatus.PARKED.value: 2,
    ProductStatus.SHIPPED.value: 3,
}

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "hanna.sqlite"
PRODUCTS_DIR = REPO_ROOT / "data" / "products"

SCHEMA = """
CREATE TABLE IF NOT EXISTS briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    phase TEXT NOT NULL,
    body TEXT NOT NULL,
    harlo_reachable INTEGER NOT NULL,
    brief_id TEXT UNIQUE,
    phase_anchor_iso TEXT NOT NULL DEFAULT ''
)
"""


def _phase_now() -> ProducerPhase:
    return compute_producer_phase(datetime.now(ZoneInfo("America/New_York")), ProducerPhase.MORNING)


def _utc_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_harlo() -> tuple[bool, dict | None]:
    try:
        with HarloBridge() as bridge:
            return True, bridge.drive_coaching_exchange()
    except (HarloUnreachable, HarloTimeout):
        return False, None


def _extract_burnout(harlo_payload: dict | None) -> str | None:
    if not isinstance(harlo_payload, dict):
        return None
    v9 = harlo_payload.get("v9")
    if not isinstance(v9, dict):
        return None
    state = v9.get("state")
    if not isinstance(state, dict):
        return None
    burnout = state.get("burnout")
    return burnout if isinstance(burnout, str) else None


def _read_product_files() -> list[ProductFile]:
    if not PRODUCTS_DIR.exists():
        return []
    products: list[ProductFile] = []
    for path in sorted(PRODUCTS_DIR.glob("*.md")):
        if path.name.endswith(".private.md"):
            continue
        products.append(ProductFile.parse(path.read_text(), path=path))
    return products


def _state_line(harlo_reachable: bool, harlo_payload: dict | None) -> str:
    if harlo_reachable:
        burnout = _extract_burnout(harlo_payload)
        if burnout:
            return f"Harlo edge reachable; burnout reads **{burnout}**."
        return "Harlo edge reachable; coaching context in hand."
    return "Harlo edge unreachable — Hanna is operating **state-blind**."


def _portfolio_line(ranked: list[str], by_name: dict[str, ProductFile], phase: ProducerPhase) -> str:
    if not ranked:
        return "The portfolio surface is empty — no product state has been logged yet."
    top_name = ranked[0]
    top_status = by_name[top_name].status.value.replace("_", " ")
    counts = Counter(by_name[name].status.value for name in ranked)
    ordered = sorted(counts.items(), key=lambda kv: _STATUS_DISPLAY_ORDER.get(kv[0], 99))
    breakdown = ", ".join(f"{count} {status.replace('_', ' ')}" for status, count in ordered)
    return f"Across the portfolio: {breakdown}. Today's top read is **{top_name}** ({top_status})."


def _approaching_line(ranked: list[str], by_name: dict[str, ProductFile]) -> str:
    entries: list[tuple[str, str, str]] = []
    for name in ranked:
        product = by_name.get(name)
        if product is None:
            continue
        for ff in product.approaching:
            if ff.date_iso or ff.description:
                entries.append((ff.date_iso, ff.description, name))
    if not entries:
        return ""
    entries.sort(key=lambda triple: (triple[0] or "9999-99-99", triple[2]))
    pieces = [f"{date_iso} — {description} ({name})" for date_iso, description, name in entries[:3]]
    return f"Approaching: {'; '.join(pieces)}. "


def _blockers_line(ranked: list[str], by_name: dict[str, ProductFile]) -> str:
    pieces: list[str] = []
    for name in ranked:
        product = by_name.get(name)
        if product is None:
            continue
        for blocker in product.blockers:
            pieces.append(f"{name}: {blocker}")
    if not pieces:
        return ""
    return f"Blockers: {'; '.join(pieces)}. "


def _compose_brief(phase: ProducerPhase, harlo_reachable: bool, harlo_payload: dict | None) -> BriefPayload:
    products = _read_product_files()
    ranked = compute_brief_priority(products, phase)
    by_name = {p.product: p for p in products}
    composed_at = datetime.now(timezone.utc).isoformat()

    state_line = _state_line(harlo_reachable, harlo_payload)
    portfolio_line = _portfolio_line(ranked, by_name, phase)
    approaching_line = _approaching_line(ranked, by_name)
    blockers_line = _blockers_line(ranked, by_name)

    body = (
        f"# Hanna brief — {phase.name.lower()}\n\n"
        f"{portfolio_line} {state_line}\n\n"
        f"{approaching_line}{blockers_line}"
        f"Surfacing this as observation — the call on what to pick up first is yours."
    )
    # D010: compute rhythm-anchor against the current ET compose-date.
    compose_date = datetime.now(ZoneInfo("America/New_York")).date()
    phase_anchor_iso = BriefPayload.compute_phase_anchor_iso(phase, compose_date)
    # D012: derive idempotency key from phase + anchor day + product set.
    brief_id = BriefPayload.compute_brief_id(phase, phase_anchor_iso, list(ranked))
    return BriefPayload(
        phase=phase,
        composed_at_iso=composed_at,
        body_markdown=body,
        referenced_products=list(ranked),
        phase_anchor_iso=phase_anchor_iso,
        brief_id=brief_id,
    )


def _persist(brief: BriefPayload, harlo_reachable: bool, db_path: Path | None = None) -> None:
    """Persist a BriefPayload to SQLite. D012: INSERT OR IGNORE for on-disk idempotency."""
    target = db_path if db_path is not None else DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as conn:
        conn.execute(SCHEMA)
        conn.execute(
            "INSERT OR IGNORE INTO briefs "
            "(ts, phase, body, harlo_reachable, brief_id, phase_anchor_iso) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                brief.composed_at_iso,
                brief.phase.name.lower(),
                brief.body_markdown,
                1 if harlo_reachable else 0,
                brief.brief_id or None,
                brief.phase_anchor_iso,
            ),
        )
        conn.commit()


def main() -> int:
    phase = _phase_now()
    if phase == ProducerPhase.FAMILY_LOCKOUT:
        print("Hanna paused: FAMILY_LOCKOUT (Mon–Fri 09:00–17:00 ET).")
        return 0

    harlo_reachable, harlo_payload = _read_harlo()
    brief = _compose_brief(phase, harlo_reachable, harlo_payload)
    _persist(brief, harlo_reachable)
    # D011: future L4b publish() may raise on non-macOS; brief stays composed + persisted,
    # exit-0 lockout-style so the SQLite row is preserved across non-mac environments.
    try:
        pass  # L4b publish() lands here in a later commit.
    except HannaCalendarNotAvailable as exc:
        print(f"Calendar channel unavailable (non-mac); brief persisted only. {exc}")
    print(brief.body_markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
