"""Unit tests for per-panel helpers (no Home Assistant needed)."""

from __future__ import annotations

from tests._loader import load

panels = load("panels")

KEYS = ("input_voltage", "power", "energy", "temperature", "mi_sn")


def test_panel_indices_numeric_and_p_style() -> None:
    data = {
        "0_power": 1.0,
        "1_power": 2.0,
        "P3_power": 3.0,
        "total_power": 6.0,
        "firmware_version": "1/2",
        "P0_bogus": 1,
    }
    assert panels.panel_indices(data) == {0, 1, 2}


def test_panel_indices_empty_packet() -> None:
    assert panels.panel_indices({}) == set()


def test_panel_value_prefers_numeric_key() -> None:
    data = {"0_power": 10.0, "P1_power": 99.0, "P2_power": 20.0}
    assert panels.panel_value(data, 0, "power") == 10.0
    assert panels.panel_value(data, 1, "power") == 20.0
    assert panels.panel_value(data, 5, "power") is None


def test_panel_sensor_keys_only_existing_values() -> None:
    data = {"0_power": 1.0, "0_mi_sn": "abcd", "1_power": 2.0, "total_energy": 3}
    assert panels.panel_sensor_keys(data, KEYS) == {
        (0, "power"),
        (0, "mi_sn"),
        (1, "power"),
    }


def test_panel_sensor_keys_from_unique_ids() -> None:
    prefix = "Envertech API_12345678_"
    unique_ids = [
        "Envertech API_12345678_P0_input_voltage",
        "Envertech API_12345678_P1_mi_sn",
        "Envertech API_12345678_total_energy",
        "Envertech API_87654321_P0_power",
        "Envertech API_12345678_P2_unknown_key",
        None,
    ]
    assert panels.panel_sensor_keys_from_unique_ids(unique_ids, prefix, KEYS) == {
        (0, "input_voltage"),
        (1, "mi_sn"),
    }
