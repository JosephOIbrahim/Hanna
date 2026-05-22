# Cloned from Harlo (github.com/JosephOIbrahim/Harlo). Specialized for Hanna.
"""scripts/first_hanna_brief.py — smaller day-zero PoC per HANNA_BLUEPRINT.md §11.1.

End-to-end: inline phase compute, one Harlo `coach` read via the bridge,
one persisted SQLite row, one composed brief to stdout. State-blind on
HarloUnreachable. No-op on FAMILY_LOCKOUT.
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from src.computations.compute_producer_phase import compute_producer_phase
from src.harlo_bridge import HarloBridge, HarloUnreachable
from src.schemas import ProducerPhase

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "hanna.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    phase TEXT NOT NULL,
    body TEXT NOT NULL,
    harlo_reachable INTEGER NOT NULL
)
"""


def _phase_now() -> ProducerPhase:
    now = datetime.now(ZoneInfo("America/New_York"))
    try:
        return compute_producer_phase(now, ProducerPhase.MORNING)
    except NotImplementedError:
        if now.hour < 11:
            return ProducerPhase.MORNING
        if now.hour < 14:
            return ProducerPhase.MIDDAY
        return ProducerPhase.EVENING


def _utc_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_harlo() -> tuple[bool, dict | None]:
    try:
        with HarloBridge() as bridge:
            return True, bridge.drive_coaching_exchange()
    except HarloUnreachable:
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


def _compose_brief(phase: str, harlo_reachable: bool, harlo_payload: dict | None) -> str:
    if harlo_reachable:
        burnout = _extract_burnout(harlo_payload)
        state_line = (
            f"Harlo edge reachable; burnout reads **{burnout}**."
            if burnout
            else "Harlo edge reachable; coaching context in hand."
        )
    else:
        state_line = (
            "Harlo edge unreachable — Hanna is operating **state-blind**. "
            "No cognitive snapshot was read; nothing about Joe's state is being inferred."
        )
    return (
        f"# Hanna brief — {phase.lower()}\n\n"
        f"Across the portfolio you have several threads in flight and a small "
        f"handful approaching their next checkpoint. Nothing is on fire; nothing "
        f"is silent either. The shape of the day is steady. {state_line}\n\n"
        f"Approaching this morning: the open lanes from yesterday's session are "
        f"still where you left them, and the next forcing function on the horizon "
        f"is days out rather than hours. Surfacing this as observation — the call "
        f"on what to pick up first is yours."
    )


def _persist(ts: str, phase: str, body: str, harlo_reachable: bool) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(SCHEMA)
        conn.execute(
            "INSERT INTO briefs (ts, phase, body, harlo_reachable) VALUES (?, ?, ?, ?)",
            (ts, phase, body, 1 if harlo_reachable else 0),
        )
        conn.commit()


def main() -> int:
    phase = _phase_now()
    if phase == ProducerPhase.FAMILY_LOCKOUT:
        print("Hanna paused: FAMILY_LOCKOUT (Mon–Fri 09:00–17:00 ET).")
        return 0

    phase_name = phase.name.lower()
    harlo_reachable, harlo_payload = _read_harlo()
    body = _compose_brief(phase_name, harlo_reachable, harlo_payload)
    _persist(_utc_ts(), phase_name, body, harlo_reachable)
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
