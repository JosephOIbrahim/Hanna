"""`python3 -m src` health-probe entry point.

Surfaces operational state as JSON on stdout. State-blind is operational,
not failure; exit 0 covers both Harlo reachable and unreachable paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src._log import get_logger
from src.computations.compute_producer_phase import compute_producer_phase
from src.harlo_bridge import HarloBridge, HarloProtocolError, HarloTimeout, HarloUnreachable
from src.schemas import ProducerPhase

_ET = ZoneInfo("America/New_York")
logger = get_logger("hanna.status")


def _phase_now() -> ProducerPhase:
    return compute_producer_phase(datetime.now(_ET), ProducerPhase.MORNING)


def _next_phase_boundary_eta_minutes(now_et: datetime, phase: ProducerPhase) -> int | None:
    """Cheap upper-bound ETA in whole minutes to the next phase boundary.

    Uses the same hour cutoffs compute_producer_phase keys off of:
      MORNING ends at 11:00 ET, MIDDAY ends at 14:00 ET, EVENING ends at
      17:00 ET (which is FAMILY_LOCKOUT). FAMILY_LOCKOUT / WEEKLY_* /
      MONTHLY return None — boundary is calendar-dependent and not cheap.
    """
    boundary_hour: int | None
    if phase == ProducerPhase.MORNING:
        boundary_hour = 11
    elif phase == ProducerPhase.MIDDAY:
        boundary_hour = 14
    elif phase == ProducerPhase.EVENING:
        boundary_hour = 17
    else:
        return None
    boundary = now_et.replace(hour=boundary_hour, minute=0, second=0, microsecond=0)
    delta = boundary - now_et
    minutes = int(delta.total_seconds() // 60)
    return max(minutes, 0)


def _probe_harlo() -> tuple[bool, str | None]:
    """Attempt a cheap read_state() call with a tight startup timeout.

    Returns (reachable, burnout). burnout is None when unreachable or when
    Harlo returned a payload without a burnout slot.
    """
    try:
        with HarloBridge(startup_timeout_seconds=2.0) as bridge:
            state = bridge.read_state()
        if isinstance(state, dict):
            inner = state.get("state")
            if isinstance(inner, dict):
                burnout = inner.get("burnout")
                if isinstance(burnout, str):
                    return True, burnout
        return True, None
    except (HarloUnreachable, HarloTimeout, HarloProtocolError) as exc:
        logger.info("status probe: harlo unreachable (%s: %s)", type(exc).__name__, exc)
        return False, None


def _cmd_status() -> int:
    now_et = datetime.now(_ET)
    phase = compute_producer_phase(now_et, ProducerPhase.MORNING)
    reachable, burnout = _probe_harlo()
    payload = {
        "hanna": "ok",
        "harlo_reachable": reachable,
        "harlo_burnout": burnout,
        "ts": datetime.now(timezone.utc).isoformat(),
        "phase": phase.name.lower(),
        "next_phase_boundary_eta_minutes": _next_phase_boundary_eta_minutes(now_et, phase),
    }
    logger.info(
        "status phase=%s harlo_reachable=%s burnout=%s",
        payload["phase"],
        payload["harlo_reachable"],
        payload["harlo_burnout"],
    )
    print(json.dumps(payload))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m src",
        description="Hanna operational probes.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status", help="emit JSON health snapshot to stdout")
    args = parser.parse_args(argv)
    if args.command == "status":
        return _cmd_status()
    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
