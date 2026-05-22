"""Pure function: rank product names by deadline-proximity x in-flight-count per REVIEW §3.6."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from src.schemas import ProducerPhase, ProductFile, ProductStatus

_ET = ZoneInfo("America/New_York")
_WORKING_DAYS_HORIZON = 5
_DAILY_PHASES = {ProducerPhase.MORNING, ProducerPhase.MIDDAY, ProducerPhase.EVENING}
_LONG_PHASES = {
    ProducerPhase.WEEKLY_MONDAY,
    ProducerPhase.WEEKLY_FRIDAY,
    ProducerPhase.MONTHLY,
}


def compute_brief_priority(
    products: list[ProductFile],
    phase: ProducerPhase,
    today: date | None = None,
) -> list[str]:
    """Return product names ordered by priority for the given phase."""
    if phase == ProducerPhase.FAMILY_LOCKOUT:
        return []
    if today is None:
        today = datetime.now(_ET).date()

    near_in_flight: list[tuple[int, str]] = []
    far_in_flight: list[str] = []
    exploring: list[str] = []
    parked: list[str] = []
    shipped: list[str] = []

    for product in products:
        if product.status == ProductStatus.IN_FLIGHT:
            near_days = _min_working_days_to_forcing_function(product, today)
            if near_days is not None and near_days <= _WORKING_DAYS_HORIZON:
                near_in_flight.append((near_days, product.product))
            else:
                far_in_flight.append(product.product)
        elif product.status == ProductStatus.EXPLORING:
            exploring.append(product.product)
        elif product.status == ProductStatus.PARKED:
            parked.append(product.product)
        elif product.status == ProductStatus.SHIPPED:
            shipped.append(product.product)

    near_sorted = [name for _, name in sorted(near_in_flight, key=lambda pair: (pair[0], pair[1]))]
    far_sorted = sorted(far_in_flight)
    exploring_sorted = sorted(exploring)

    result = near_sorted + far_sorted + exploring_sorted
    if phase in _LONG_PHASES:
        result = result + sorted(parked) + sorted(shipped)
    return result


def _min_working_days_to_forcing_function(product: ProductFile, today: date) -> int | None:
    best: int | None = None
    for ff in product.approaching:
        if not ff.date_iso:
            continue
        try:
            ff_date = date.fromisoformat(ff.date_iso[:10])
        except ValueError:
            continue
        days = _working_days_between(today, ff_date)
        if days is None:
            continue
        if best is None or days < best:
            best = days
    return best


def _working_days_between(today: date, target: date) -> int | None:
    if target < today:
        return None
    if target == today:
        return 0
    days_remaining = 0
    cursor = today
    while cursor < target:
        cursor = cursor + timedelta(days=1)
        if cursor.weekday() < 5:
            days_remaining += 1
        if days_remaining > _WORKING_DAYS_HORIZON:
            return days_remaining
    return days_remaining
