"""Sensor platform for Envertech API."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DEVICE_NAME, DOMAIN, MANUFACTURER
from .coordinator import InverterSocketCoordinator
from .panels import (
    panel_sensor_keys,
    panel_sensor_keys_from_unique_ids,
    panel_value,
)
from .period_energy import compute_period_energy

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="input_voltage",
        translation_key="input_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="power",
        translation_key="power",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="energy",
        translation_key="energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="grid_voltage",
        translation_key="grid_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="frequency",
        translation_key="frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.FREQUENCY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="mi_sn",
        translation_key="module_serial",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

SENSOR_TYPES_SINGLE: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="total_energy",
        translation_key="total_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="total_power",
        translation_key="total_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="energy_daily",
        translation_key="energy_daily",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="energy_monthly",
        translation_key="energy_monthly",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="energy_yearly",
        translation_key="energy_yearly",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
    ),
)

PERIOD_KEYS = {"energy_daily", "energy_monthly", "energy_yearly"}


class InverterSensor(CoordinatorEntity[InverterSocketCoordinator], SensorEntity):
    """Sensor for per-panel or global inverter values."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InverterSocketCoordinator,
        description: SensorEntityDescription,
        module_index: int | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._module_index = module_index
        self._attr_translation_key = description.translation_key

        if module_index is not None:
            self._attr_unique_id = (
                f"{DEVICE_NAME}_{coordinator.sn}_P{module_index}_{description.key}"
            )
            self._attr_name = (
                f"P{module_index + 1} "
                f"{description.translation_key.replace('_', ' ').title()}"
            )
            self._attr_has_entity_name = False
        else:
            self._attr_unique_id = f"{DEVICE_NAME}_{coordinator.sn}_{description.key}"

    @property
    def native_value(self):
        if self._module_index is not None:
            return panel_value(
                self.coordinator.data, self._module_index, self.entity_description.key
            )
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict:
        if self._module_index is not None:
            return {
                "serial_number": panel_value(
                    self.coordinator.data, self._module_index, "mi_sn"
                )
            }
        return {}

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{DEVICE_NAME}_{self.coordinator.sn}")},
            name=f"{DEVICE_NAME} {self.coordinator.sn}",
            manufacturer=MANUFACTURER,
            model="Microinverter",
            sw_version=self.coordinator.data.get("firmware_version"),
        )

    @property
    def available(self) -> bool:
        return self.coordinator.connected and self.coordinator.last_update_success


class InverterPeriodEnergySensor(
    CoordinatorEntity[InverterSocketCoordinator], SensorEntity, RestoreEntity
):
    """Daily / monthly / yearly energy derived from total_energy."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InverterSocketCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DEVICE_NAME}_{coordinator.sn}_{description.key}"
        self._attr_translation_key = description.translation_key
        self._offset: float | None = None
        self._period_marker: str | None = None
        self._last_reset: datetime | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if not last_state:
            return
        try:
            self._offset = float(last_state.attributes.get("offset", 0))
            self._period_marker = last_state.attributes.get("period_marker")
            reset_str = last_state.attributes.get("last_reset")
            if reset_str:
                parsed = dt_util.parse_datetime(reset_str)
                if parsed:
                    self._last_reset = parsed
        except (TypeError, ValueError) as exc:
            _LOGGER.warning("Failed to restore %s: %s", self.entity_id, exc)

    @property
    def native_value(self) -> float | None:
        current_total = self.coordinator.data.get("total_energy")
        if current_total is None:
            return None

        value, self._offset, self._period_marker, reset = compute_period_energy(
            key=self.entity_description.key,
            current_total=float(current_total),
            offset=self._offset,
            marker=self._period_marker,
            now=dt_util.now(),
        )
        if reset is not None:
            self._last_reset = reset
        return value

    @property
    def extra_state_attributes(self) -> dict:
        attrs: dict = {
            "offset": self._offset,
            "period_marker": self._period_marker,
        }
        if self._last_reset is not None:
            attrs["last_reset"] = dt_util.as_local(self._last_reset).isoformat()
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{DEVICE_NAME}_{self.coordinator.sn}")},
            name=f"{DEVICE_NAME} {self.coordinator.sn}",
            manufacturer=MANUFACTURER,
            model="Microinverter",
            sw_version=self.coordinator.data.get("firmware_version"),
        )

    @property
    def available(self) -> bool:
        return self.coordinator.connected and self.coordinator.last_update_success


PANEL_KEYS = tuple(description.key for description in SENSOR_TYPES)
PANEL_DESCRIPTIONS = {description.key: description for description in SENSOR_TYPES}


def _global_entities(coordinator: InverterSocketCoordinator) -> list[SensorEntity]:
    """Build inverter-wide sensors (created immediately, before any data)."""
    entities: list[SensorEntity] = []
    for description in SENSOR_TYPES_SINGLE:
        if description.key in PERIOD_KEYS:
            entities.append(InverterPeriodEnergySensor(coordinator, description))
        else:
            entities.append(InverterSensor(coordinator, description))
    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Envertech API sensors without waiting for the inverter.

    Entities are created right away (unavailable until data arrives):
    inverter-wide sensors always, per-panel sensors for every panel already
    known from the entity registry or current data. Panels that show up later
    in the stream are added dynamically, so a late first packet (inverter
    offline at night, network not ready at boot, ...) no longer results in
    missing entities.
    """
    coordinator: InverterSocketCoordinator = hass.data[DOMAIN][entry.entry_id]

    registry = er.async_get(hass)
    known = panel_sensor_keys_from_unique_ids(
        (
            reg_entry.unique_id
            for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id)
        ),
        f"{DEVICE_NAME}_{coordinator.sn}_",
        PANEL_KEYS,
    )
    added: set[tuple[int, str]] = set()
    firmware: dict[str, str | None] = {"value": None}

    def _panel_entities(keys: set[tuple[int, str]]) -> list[SensorEntity]:
        new = sorted(keys - added)
        added.update(new)
        return [
            InverterSensor(coordinator, PANEL_DESCRIPTIONS[key], module_index=index)
            for index, key in new
        ]

    async_add_entities(
        _global_entities(coordinator)
        + _panel_entities(known | panel_sensor_keys(coordinator.data, PANEL_KEYS))
    )

    @callback
    def _async_on_coordinator_update() -> None:
        new_entities = _panel_entities(panel_sensor_keys(coordinator.data, PANEL_KEYS))
        if new_entities:
            _LOGGER.debug(
                "Adding %s new panel sensor(s) for %s",
                len(new_entities),
                coordinator.sn,
            )
            async_add_entities(new_entities)

        version = coordinator.data.get("firmware_version")
        if version and version != firmware["value"]:
            firmware["value"] = version
            dev_reg = dr.async_get(hass)
            device = dev_reg.async_get_device(
                identifiers={(DOMAIN, f"{DEVICE_NAME}_{coordinator.sn}")}
            )
            if device and device.sw_version != version:
                dev_reg.async_update_device(device.id, sw_version=version)

    entry.async_on_unload(coordinator.async_add_listener(_async_on_coordinator_update))
