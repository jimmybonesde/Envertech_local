"""Unit tests for period energy helpers."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from custom_components.envertech_local.period_energy import (
    compute_period_energy,
    period_marker_for,
)

TZ = ZoneInfo("Europe/Berlin")


def test_period_marker_daily_monthly_yearly() -> None:
    now = datetime(2026, 9, 11, 10, 0, tzinfo=TZ)
    assert period_marker_for("energy_daily", now) == "2026-09-11"
    assert period_marker_for("energy_monthly", now) == "2026-09"
    assert period_marker_for("energy_yearly", now) == "2026"


def test_period_marker_rejects_unknown_key() -> None:
    now = datetime(2026, 9, 11, tzinfo=TZ)
    with pytest.raises(ValueError):
        period_marker_for("energy_weekly", now)


def test_compute_initializes_offset_on_first_read() -> None:
    now = datetime(2026, 9, 11, 10, 0, tzinfo=TZ)
    value, offset, marker, last_reset = compute_period_energy(
        key="energy_daily",
        current_total=100.0,
        offset=None,
        marker=None,
        now=now,
    )
    assert value == 0.0
    assert offset == 100.0
    assert marker == "2026-09-11"
    assert last_reset == now


def test_compute_accumulates_within_same_period() -> None:
    now = datetime(2026, 9, 11, 15, 0, tzinfo=TZ)
    value, offset, marker, last_reset = compute_period_energy(
        key="energy_daily",
        current_total=112.5,
        offset=100.0,
        marker="2026-09-11",
        now=now,
    )
    assert value == 12.5
    assert offset == 100.0
    assert marker == "2026-09-11"
    assert last_reset is None


def test_compute_resets_on_new_day() -> None:
    now = datetime(2026, 9, 12, 0, 5, tzinfo=TZ)
    value, offset, marker, last_reset = compute_period_energy(
        key="energy_daily",
        current_total=120.0,
        offset=100.0,
        marker="2026-09-11",
        now=now,
    )
    assert value == 0.0
    assert offset == 120.0
    assert marker == "2026-09-12"
    assert last_reset == now


def test_compute_never_negative() -> None:
    now = datetime(2026, 9, 11, 12, 0, tzinfo=TZ)
    value, offset, marker, last_reset = compute_period_energy(
        key="energy_monthly",
        current_total=90.0,
        offset=100.0,
        marker="2026-09",
        now=now,
    )
    assert value == 0.0
    assert offset == 100.0
    assert marker == "2026-09"
    assert last_reset is None
