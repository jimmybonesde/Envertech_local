"""Sensor platform for Envertech API."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import dt as dt_util

from .const import DEVICE_NAME, DOMAIN, MANUFACTURER
from .period_energy import compute_period_energy

_LOGGER = logging.getLogger(__name__)

DATA_READY_TIMEOUT = 60

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


class InverterSocketCoordinator(DataUpdateCoordinator):
    """Coordinator streaming inverter data via envertech_local."""

    def __init__(self, hass: HomeAssistant, ip: str, port: int, sn: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"envertech_local_{sn}",
            update_interval=timedelta(seconds=30),
        )
        self.ip = ip
        self.port = port
        self.sn = sn
        self.data: dict = {}
        self.number_of_panels = 0
        self.data_ready = False
        self.connected = False
        self.running = True
        self._data_ready_event = asyncio.Event()
        self._stream_task: asyncio.Task | None = hass.async_create_background_task(
            self._stream_loop(),
            name=f"envertech_local_stream_{sn}",
        )

    async def _async_update_data(self) -> dict:
        """Return latest cached stream data for coordinator consumers."""
        return self.data

    async def async_wait_for_data(self, timeout: float = DATA_READY_TIMEOUT) -> bool:
        """Wait until the first successful stream packet arrives."""
        if self.data_ready:
            return True
        try:
            await asyncio.wait_for(self._data_ready_event.wait(), timeout=timeout)
        except TimeoutError:
            return False
        return self.data_ready

    async def async_shutdown(self) -> None:
        """Stop the background stream."""
        self.running = False
        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass

    def _mark_data_ready(self) -> None:
        self.data_ready = True
        self._data_ready_event.set()

    async def _stream_loop(self) -> None:
        from envertech_local import stream_inverter_data

        device = {"ip": self.ip, "port": self.port, "serial_number": self.sn}
        while self.running:
            try:
                async for update in stream_inverter_data(device, interval=5):
                    if not self.running:
                        break
                    if isinstance(update, dict) and "error" in update:
                        self.connected = False
                        continue

                    panel_ids: set[str] = set()
                    for key in update:
                        if "_" in key:
                            prefix = key.split("_", 1)[0]
                            if prefix.isdigit() or prefix.upper().startswith("P"):
                                panel_ids.add(prefix)
                    self.number_of_panels = len(panel_ids)

                    for key, val in update.items():
                        self.data[key] = (
                            round(val, 2) if isinstance(val, (int, float)) else val
                        )

                    self.connected = True
                    self._mark_data_ready()
                    self.async_set_updated_data(self.data)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.connected = False
                _LOGGER.exception("Inverter stream error for %s", self.sn)
                await asyncio.sleep(10)


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
            key_numeric = f"{self._module_index}_{self.entity_description.key}"
            key_p = f"P{self._module_index + 1}_{self.entity_description.key}"
            return self.coordinator.data.get(
                key_numeric, self.coordinator.data.get(key_p)
            )
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict:
        if self._module_index is not None:
            key_numeric = f"{self._module_index}_mi_sn"
            key_p = f"P{self._module_index + 1}_mi_sn"
            return {
                "serial_number": self.coordinator.data.get(
                    key_numeric, self.coordinator.data.get(key_p)
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


def _build_entities(coordinator: InverterSocketCoordinator) -> list[SensorEntity]:
    """Build panel + global sensor entities from current coordinator data."""
    entities: list[SensorEntity] = []

    for i in range(coordinator.number_of_panels):
        for description in SENSOR_TYPES:
            key_numeric = f"{i}_{description.key}"
            key_p = f"P{i + 1}_{description.key}"
            if key_numeric in coordinator.data or key_p in coordinator.data:
                entities.append(
                    InverterSensor(coordinator, description, module_index=i)
                )

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
    """Set up Envertech API sensors without blocking platform setup."""
    coordinator: InverterSocketCoordinator = hass.data[DOMAIN][entry.entry_id]

    async def _async_add_entities_when_ready() -> None:
        if not await coordinator.async_wait_for_data():
            _LOGGER.error(
                "No inverter data within %s seconds for %s (%s)",
                DATA_READY_TIMEOUT,
                coordinator.sn,
                coordinator.ip,
            )
            return
        async_add_entities(_build_entities(coordinator))

    # Return immediately so HA does not warn about >10s platform setup.
    entry.async_create_background_task(
        hass,
        _async_add_entities_when_ready(),
        f"{DOMAIN}_add_entities_{entry.entry_id}",
    )
