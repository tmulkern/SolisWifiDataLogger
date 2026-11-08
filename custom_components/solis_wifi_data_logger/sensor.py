from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .data_update_coordinator import SolisConfigEntry, SolisWifiApiDataUpdateCoordinator
from .utilities import Utilities

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SolisSensorEntityDescription(SensorEntityDescription):
    """Describes a Solis sensor; `key` is the property name on the data source."""

    data_source: str


SENSOR_DESCRIPTIONS: tuple[SolisSensorEntityDescription, ...] = (
    SolisSensorEntityDescription(
        data_source="inverter",
        key="temperature",
        name="Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SolisSensorEntityDescription(
        data_source="inverter",
        key="current_power",
        name="Current Power",
        icon="mdi:solar-power-variant",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SolisSensorEntityDescription(
        data_source="inverter",
        key="daily_power_yield",
        name="Daily Power Yield",
        icon="mdi:meter-electric",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SolisSensorEntityDescription(
        data_source="wifi_logger",
        key="signal_quality",
        name="Signal Quality",
        icon="mdi:signal",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolisConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:

    coordinator = entry.runtime_data
    systemdata = coordinator.data

    device_infos = {
        data_source: Utilities.GenerateDeviceInfo(hass, entry, systemdata, data_source)
        for data_source in {d.data_source for d in SENSOR_DESCRIPTIONS}
    }

    async_add_entities(
        SolisApiSensor(coordinator, description, device_infos[description.data_source])
        for description in SENSOR_DESCRIPTIONS
    )


class SolisApiSensor(CoordinatorEntity[SolisWifiApiDataUpdateCoordinator], SensorEntity):

    entity_description: SolisSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolisWifiApiDataUpdateCoordinator,
        description: SolisSensorEntityDescription,
        deviceInfo: DeviceInfo | None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        self._attr_device_info = deviceInfo
        # Keep the legacy unique_id format so existing entities/history are preserved
        self._attr_unique_id = Utilities.GenerateUniqueId(
            coordinator, Utilities.FormatSensorName(description.data_source, description.key)
        )

        #Set Initial Value
        self._attr_native_value = self._current_value()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self._current_value()
        self.async_write_ha_state()

    def _data(self):
        return getattr(self.coordinator.data, self.entity_description.data_source, None)

    def _current_value(self):
        return getattr(self._data(), self.entity_description.key, None)

    @property
    def available(self) -> bool:
        return self._current_value() is not None
