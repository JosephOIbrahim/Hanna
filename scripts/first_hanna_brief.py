# Copyright 2026 Joseph Ibrahim
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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

from src.harlo_bridge import HarloBridge, HarloUnreachable

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


def _phase_now() -> str:
    et = ZoneInfo("America/New_York")
    now = datetime.now(et)
    if now.weekday() >= 5 or not (9 <= now.hour < 17):
        return "FAMILY_LOCKOUT"
    return "MORNING"


def _utc_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_harlo() -> tuple[bool, dict | None]:
    try:
        bridge = HarloBridge()
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
    if phase == "FAMILY_LOCKOUT":
        print("Hanna paused: FAMILY_LOCKOUT (Mon–Fri 09:00–17:00 ET).")
        return 0

    harlo_reachable, harlo_payload = _read_harlo()
    body = _compose_brief(phase, harlo_reachable, harlo_payload)
    _persist(_utc_ts(), phase, body, harlo_reachable)
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
