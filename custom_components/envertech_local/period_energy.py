"""Pure helpers for period energy sensors (daily/monthly/yearly)."""

from __future__ import annotations

from datetime import datetime


def period_marker_for(key: str, now: datetime) -> str:
    """Return the period marker string for a given energy sensor key."""
    if key == "energy_daily":
        return now.date().isoformat()
    if key == "energy_monthly":
        return now.strftime("%Y-%m")
    if key == "energy_yearly":
        return str(now.year)
    raise ValueError(f"Unsupported period key: {key}")


def compute_period_energy(
    *,
    key: str,
    current_total: float,
    offset: float | None,
    marker: str | None,
    now: datetime,
) -> tuple[float, float, str, datetime | None]:
    """Compute period energy and updated offset/marker/last_reset.

    Returns (value_kwh, new_offset, new_marker, last_reset_or_none_if_unchanged).
    last_reset is only set when the period rolls or offset is initialized.
    """
    current_marker = period_marker_for(key, now)
    last_reset: datetime | None = None
    new_offset = offset

    if marker != current_marker:
        new_offset = float(current_total)
        last_reset = now
    elif new_offset is None:
        new_offset = float(current_total)
        last_reset = now

    assert new_offset is not None
    value = round(max(0.0, float(current_total) - new_offset), 2)
    return value, new_offset, current_marker, last_reset
