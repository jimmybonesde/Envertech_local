"""Pure helpers to derive per-panel sensors (Home Assistant free)."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping


def panel_indices(data: Mapping[str, object]) -> set[int]:
    """Return zero-based panel indices present in stream data.

    Supports ``"0_power"`` (envertech-local) and ``"P1_power"`` style keys.
    """
    indices: set[int] = set()
    for key in data:
        if "_" not in key:
            continue
        prefix = key.split("_", 1)[0]
        if prefix.isdigit():
            indices.add(int(prefix))
        elif len(prefix) > 1 and prefix[0] in "Pp" and prefix[1:].isdigit():
            number = int(prefix[1:])
            if number >= 1:
                indices.add(number - 1)
    return indices


def panel_value(data: Mapping[str, object], index: int, key: str) -> object:
    """Return the value of ``key`` for panel ``index`` (either key style)."""
    value = data.get(f"{index}_{key}")
    if value is None:
        value = data.get(f"P{index + 1}_{key}")
    return value


def panel_sensor_keys(
    data: Mapping[str, object], keys: Iterable[str]
) -> set[tuple[int, str]]:
    """Return (panel_index, key) pairs for which data is available."""
    keys = tuple(keys)
    return {
        (index, key)
        for index in panel_indices(data)
        for key in keys
        if f"{index}_{key}" in data or f"P{index + 1}_{key}" in data
    }


def panel_sensor_keys_from_unique_ids(
    unique_ids: Iterable[str | None], prefix: str, keys: Iterable[str]
) -> set[tuple[int, str]]:
    """Return (panel_index, key) pairs of already registered panel entities.

    Unique IDs look like ``f"{prefix}P{index}_{key}"``.
    """
    valid = set(keys)
    pattern = re.compile(rf"^{re.escape(prefix)}P(\d+)_(.+)$")
    found: set[tuple[int, str]] = set()
    for unique_id in unique_ids:
        if not unique_id:
            continue
        match = pattern.match(unique_id)
        if match and match.group(2) in valid:
            found.add((int(match.group(1)), match.group(2)))
    return found
