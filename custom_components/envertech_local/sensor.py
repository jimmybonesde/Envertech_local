import logging
import asyncio
from datetime import datetime
from .const import DOMAIN, MANUFACTURER, DEVICE_NAME
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfElectricPotential,
    UnitOfFrequency,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

# Per-panel (per-module) sensors
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
    ),
)

# Global sensors (inkl. Tages-/Monats-/Jahresenergie)
SENSOR_TYPES_SINGLE: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
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


class InverterSocketCoordinator(DataUpdateCoordinator):
    """Coordinator using envertech_local.stream_inverter_data()."""

    def __init__(self, hass: HomeAssistant, ip: str, port: int, sn: str):
        super().__init__(hass, _LOGGER, name="inverter_stream")
        self.ip = ip
        self.port = port
        self.sn = sn
        self.data = {}
        self.number_of_panels = 0
        self.data_ready = False
        self.connected = False
        self.running = True
        asyncio.create_task(self._stream_loop())

    async def _stream_loop(self):
        from envertech_local import stream_inverter_data
        device = {"ip": self.ip, "port": self.port, "serial_number": self.sn}
        while self.running:
            try:
                async for update in stream_inverter_data(device, interval=5):
                    if isinstance(update, dict) and "error" in update:
                        self.connected = False
                        continue

                    parsed_data = update

                    # Panels dynamisch zählen
                    panel_ids = [
                        key.split("_")[0] for key in parsed_data.keys() if "_" in key and key[0].isdigit()
                    ]
                    self.number_of_panels = len(set(panel_ids))

                    # Alle Werte speichern
                    for key, val in parsed_data.items():
                        self.data[key] = round(val, 2) if isinstance(val, (int, float)) else val

                    self.connected = True
                    self.data_ready = True
                    self.async_set_updated_data(self.data)

            except Exception:
                self.connected = False
                _LOGGER.exception("Fehler im Inverter-Stream")
                await asyncio.sleep(10)


class InverterSensor(CoordinatorEntity, SensorEntity):
    """Sensor für einzelne Panels oder globale Werte"""

    def __init__(self, coordinator, description: SensorEntityDescription, module_index: int = None):
        super().__init__(coordinator)
        self.entity_description = description
        self._module_index = module_index

        if module_index is not None:
            self._attr_name = f"P{module_index + 1} {description.translation_key.replace('_', ' ').title()}"
            self._attr_unique_id = f"{DEVICE_NAME}_{coordinator.sn}_P{module_index}_{description.key}"
        else:
            self._attr_name = description.translation_key.replace('_', ' ').title()
            self._attr_unique_id = f"{DEVICE_NAME}_{coordinator.sn}_{description.key}"

        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_state_class = description.state_class
        self._attr_device_class = description.device_class
        self._attr_entity_category = description.entity_category

    @property
    def native_value(self):
        if self._module_index is not None:
            return self.coordinator.data.get(f"{self._module_index}_{self.entity_description.key}")
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def extra_state_attributes(self):
        if self._module_index is not None:
            return {"serial_number": self.coordinator.data.get(f"{self._module_index}_mi_sn")}
        return {}

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{DEVICE_NAME}_{self.coordinator.sn}")},
            name=f"{DEVICE_NAME} {self.coordinator.sn}",
            manufacturer=MANUFACTURER,
        )

    @property
    def available(self) -> bool:
        return self.coordinator.connected and self.coordinator.last_update_success


class InverterPeriodEnergySensor(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Berechnet Tages-, Monats- und Jahresenergie auf Basis von total_energy mit Persistenz"""

    def __init__(self, coordinator, description: SensorEntityDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DEVICE_NAME}_{coordinator.sn}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_translation_key = description.translation_key

        self._offset: float | None = None
        self._period_marker: str | None = None
        self._last_reset: datetime | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            try:
                self._offset = float(last_state.attributes.get("offset", 0))
                self._period_marker = last_state.attributes.get("period_marker")
                reset_str = last_state.attributes.get("last_reset")
                if reset_str:
                    parsed = dt_util.parse_datetime(reset_str)
                    if parsed:
                        self._last_reset = parsed
                _LOGGER.debug(
                    "Restored %s: offset=%.2f, marker=%s, last_reset=%s",
                    self.name or self.entity_id,
                    self._offset or 0,
                    self._period_marker or "None",
                    self._last_reset,
                )
            except Exception as exc:
                _LOGGER.warning("Restore fehlerhaft für %s: %s", self.name or self.entity_id, exc)

    @property
    def native_value(self) -> float | None:
        current_total = self.coordinator.data.get("total_energy")
        if current_total is None:
            return None

        now = dt_util.now()

        if self.entity_description.key == "energy_daily":
            current_marker = now.date().isoformat()
        elif self.entity_description.key == "energy_monthly":
            current_marker = now.strftime("%Y-%m")
        else:  # yearly
            current_marker = str(now.year)

        # Periodenwechsel erkennen
        if self._period_marker != current_marker:
            _LOGGER.info(
                "Neuer Zeitraum für %s: %s → %s",
                self.entity_description.key,
                self._period_marker or "initial",
                current_marker
            )
            self._offset = current_total
            self._period_marker = current_marker
            self._last_reset = now

        # Erste Initialisierung
        if self._offset is None:
            self._offset = current_total
            self._last_reset = now

        value = max(0.0, current_total - self._offset)
        return round(value, 2)

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {
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
        )

    @property
    def available(self) -> bool:
        return self.coordinator.connected and self.coordinator.last_update_success


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Warten auf erste gültige Daten
    for _ in range(60):
        if coordinator.data_ready:
            break
        await asyncio.sleep(1)

    if not coordinator.data_ready:
        _LOGGER.error("Keine Inverter-Daten innerhalb von 60 Sekunden erhalten")
        return

    entities = []

    # Per-Panel-Sensoren
    for i in range(coordinator.number_of_panels):
        for description in SENSOR_TYPES:
            entities.append(InverterSensor(coordinator, description, module_index=i))

    # Globale Sensoren
    for description in SENSOR_TYPES_SINGLE:
        if description.key in ["energy_daily", "energy_monthly", "energy_yearly"]:
            entities.append(InverterPeriodEnergySensor(coordinator, description))
        else:
            entities.append(InverterSensor(coordinator, description))

    async_add_entities(entities, True)
