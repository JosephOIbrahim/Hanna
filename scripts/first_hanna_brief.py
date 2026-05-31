# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
"""scripts/first_hanna_brief.py — smaller day-zero PoC per HANNA_BLUEPRINT.md §11.1.

End-to-end: inline phase compute, one Harlo `coach` read via the bridge,
one persisted SQLite row, one composed brief to stdout. State-blind on
HarloUnreachable or HarloTimeout. No-op on FAMILY_LOCKOUT.

Sub-render contract
-------------------
Each sub-render helper (`_state_line`, `_portfolio_line`, `_approaching_line`,
`_blockers_line`) returns a plain string that the composer joins with a space
into the brief body. Trailing-period punctuation is caller-managed: the
composer appends `.` periods at join boundaries inside each sub-render
return value (see e.g. `f"Approaching: ...; {last}. "` and the period inside
`_state_line`), and the surrounding paragraph layout is composed in
`_compose_brief`. Sub-renders that produce an empty signal (no entries) return
an empty string `""`; the composer's space-join then collapses cleanly.

This contract is empirical — derived from the current `_compose_brief`
template — and exists so future extensions of the composer (more lines, new
phases) don't accidentally double-punctuate or drop separators. Anyone adding
a new sub-render helper appends trailing punctuation inside the helper and
returns `""` when there is nothing to surface; the composer then concatenates
without further punctuation work.
"""

from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from src._log import get_logger
from src.channels.calendar import (
    HannaCalendarError,
    HannaCalendarNotAvailable,
    publish as calendar_publish,
)
from src.computations.compute_brief_priority import compute_brief_priority
from src.computations.compute_producer_phase import compute_producer_phase
from src.harlo_bridge import HarloBridge, HarloTimeout, HarloUnreachable
from src.schemas import BriefPayload, ProducerPhase, ProductFile, ProductStatus

logger = get_logger("hanna.brief")

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
    phase_anchor_iso TEXT NOT NULL DEFAULT '',
    calendar_event_uid TEXT,
    unpublished_reason TEXT
)
"""

# D006/D011/D012 reconciliation columns added in L4b. The migrations below
# allow older `data/hanna.sqlite` files (created before L4b landed) to gain
# the new columns without losing existing rows; each ALTER is wrapped in a
# try/except sqlite3.OperationalError so re-runs are idempotent.
_RECONCILIATION_MIGRATIONS = (
    "ALTER TABLE briefs ADD COLUMN calendar_event_uid TEXT",
    "ALTER TABLE briefs ADD COLUMN unpublished_reason TEXT",
)


def _apply_reconciliation_migrations(conn: sqlite3.Connection) -> None:
    """Add the L4b reconciliation columns to legacy schemas in-place.

    Each ALTER is idempotent — sqlite3 raises OperationalError when the
    column already exists, which is the steady-state for any fresh schema
    created by ``SCHEMA`` above. The try/except swallows that specific
    duplicate-column case and surfaces every other operational error.
    """
    for stmt in _RECONCILIATION_MIGRATIONS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Durability + concurrency hardening for the briefs SQLite store.

    PRAGMAs are idempotent — safe to re-apply on every connection. Set on each
    new connect() because journal_mode persists per-database but the others
    (busy_timeout, foreign_keys) are per-connection.
    """
    conn.execute("PRAGMA journal_mode=WAL")        # concurrent-reader safety
    conn.execute("PRAGMA synchronous=NORMAL")      # durable for WAL, no per-commit fsync
    conn.execute("PRAGMA busy_timeout=5000")       # 5s wait on contended locks
    conn.execute("PRAGMA foreign_keys=ON")         # future-proof; no FKs today


def _phase_now() -> ProducerPhase:
    phase = compute_producer_phase(datetime.now(ZoneInfo("America/New_York")), ProducerPhase.MORNING)
    logger.info("phase=%s", phase.name.lower())
    return phase


def _utc_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_harlo() -> tuple[bool, dict | None]:
    bridge = HarloBridge()
    try:
        with bridge:
            payload = bridge.drive_coaching_exchange()
            logger.info("harlo_reachable=true coach=ok")
            return True, payload
    except HarloUnreachable as exc:
        tail = getattr(bridge, "last_stderr", lambda: [])()
        logger.warning("harlo_reachable=false reason=unreachable detail=%s", exc)
        for line in tail[-10:]:
            logger.warning("harlo stderr [_read_harlo:unreachable]: %s", line)
        return False, None
    except HarloTimeout as exc:
        tail = getattr(bridge, "last_stderr", lambda: [])()
        logger.warning("harlo_reachable=false reason=timeout detail=%s", exc)
        for line in tail[-10:]:
            logger.warning("harlo stderr [_read_harlo:timeout]: %s", line)
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
    logger.info("compose start phase=%s harlo_reachable=%s", phase.name.lower(), harlo_reachable)
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
    logger.info(
        "compose done phase=%s brief_id=%s products=%d",
        phase.name.lower(),
        brief_id or "(none)",
        len(ranked),
    )
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
        _apply_pragmas(conn)
        conn.execute(SCHEMA)
        # L4b: bring legacy DBs up to the reconciliation schema before the
        # insert. Idempotent on already-migrated and fresh-created tables.
        _apply_reconciliation_migrations(conn)
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


def _update_reconciliation(
    brief_id: str,
    *,
    calendar_event_uid: str | None = None,
    unpublished_reason: str | None = None,
    db_path: Path | None = None,
) -> None:
    """Update the L4b reconciliation columns for an already-persisted brief.

    Either *calendar_event_uid* or *unpublished_reason* may be set; per the
    P6 invariant exactly one of them is meaningful for any non-lockout row.
    The reconciliation is keyed on ``brief_id`` which is the D012 dedup
    handle. Briefs with an empty ``brief_id`` (e.g. FAMILY_LOCKOUT briefs
    whose phase_anchor_iso is empty) are matched on ``phase`` + ``ts`` as
    a fallback so the invariant still holds for lockout rows persisted
    through helper code paths.
    """
    target = db_path if db_path is not None else DB_PATH
    if not target.exists():
        return
    with sqlite3.connect(target) as conn:
        _apply_pragmas(conn)
        _apply_reconciliation_migrations(conn)
        if brief_id:
            conn.execute(
                "UPDATE briefs SET calendar_event_uid = ?, "
                "unpublished_reason = ? WHERE brief_id = ?",
                (calendar_event_uid, unpublished_reason, brief_id),
            )
        else:
            # Fallback for briefs without a stable brief_id (FAMILY_LOCKOUT
            # rows produced by helper code paths). Touches the most-recent
            # NULL-brief_id row so the invariant has somewhere to land.
            conn.execute(
                "UPDATE briefs SET calendar_event_uid = ?, "
                "unpublished_reason = ? WHERE id = ("
                "  SELECT id FROM briefs WHERE brief_id IS NULL "
                "  ORDER BY id DESC LIMIT 1"
                ")",
                (calendar_event_uid, unpublished_reason),
            )
        conn.commit()


def main() -> int:
    phase = _phase_now()
    if phase == ProducerPhase.FAMILY_LOCKOUT:
        logger.info("main exit=0 reason=family_lockout")
        print("Hanna paused: FAMILY_LOCKOUT (Mon–Fri 09:00–17:00 ET).")
        return 0

    harlo_reachable, harlo_payload = _read_harlo()
    brief = _compose_brief(phase, harlo_reachable, harlo_payload)
    _persist(brief, harlo_reachable)
    logger.info(
        "persist done phase=%s brief_id=%s harlo_reachable=%s",
        brief.phase.name.lower(),
        brief.brief_id or "(none)",
        harlo_reachable,
    )
    # D011 / D006 reconciliation: try to publish; on non-mac or other
    # calendar-channel failures, persist the failure reason rather than
    # crashing — the brief stays composed + persisted, exit-0 lockout-style.
    try:
        event_id = calendar_publish(brief)
    except HannaCalendarNotAvailable as exc:
        logger.info("calendar unavailable (non-mac); brief persisted only. %s", exc)
        _update_reconciliation(brief.brief_id, unpublished_reason="non_macos")
        print(f"Calendar channel unavailable (non-mac); brief persisted only. {exc}")
    except HannaCalendarError as exc:
        logger.warning(
            "calendar publish failed (%s); brief persisted only. %s",
            type(exc).__name__,
            exc,
        )
        _update_reconciliation(
            brief.brief_id,
            unpublished_reason=f"publish_failed: {type(exc).__name__}",
        )
    else:
        if event_id is None:
            # publish() returned a graceful no-op for an empty anchor (D010/D011);
            # FAMILY_LOCKOUT exits earlier, so this path is the empty-anchor case.
            _update_reconciliation(brief.brief_id, unpublished_reason="no_anchor")
        else:
            _update_reconciliation(brief.brief_id, calendar_event_uid=str(event_id))
    print(brief.body_markdown)
    logger.info("main exit=0 phase=%s harlo_reachable=%s", phase.name.lower(), harlo_reachable)
    return 0


if __name__ == "__main__":
    sys.exit(main())
