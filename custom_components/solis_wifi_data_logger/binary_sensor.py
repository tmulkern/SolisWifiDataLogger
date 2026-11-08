from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .data_update_coordinator import SolisConfigEntry, SolisWifiApiDataUpdateCoordinator
from .utilities import Utilities

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SolisBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Solis binary sensor; `key` is the property name on the data source."""

    data_source: str
    attribute_names: tuple[str, ...] = ()


BINARY_SENSOR_DESCRIPTIONS: tuple[SolisBinarySensorEntityDescription, ...] = (
    SolisBinarySensorEntityDescription(
        data_source="inverter",
        key="alerts",
        name="Alerts",
        icon="mdi:alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        attribute_names=("serial_number", "firmware_version", "model"),
    ),
    SolisBinarySensorEntityDescription(
        data_source="wifi_logger",
        key="online_status",
        name="Online Status",
        icon="mdi:wifi-check",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        attribute_names=("last_seen", "serial_number", "firmware_version"),
    ),
    SolisBinarySensorEntityDescription(
        data_source="wifi_logger",
        key="wireless_ap_mode",
        name="Wireless Ap Mode",
        icon="mdi:access-point",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolisBinarySensorEntityDescription(
        data_source="wifi_logger",
        key="wireless_sta_mode",
        name="Wireless Sta Mode",
        icon="mdi:wifi-settings",
        entity_category=EntityCategory.DIAGNOSTIC,
        attribute_names=("router_ssid", "ip_address", "mac_address"),
    ),
    SolisBinarySensorEntityDescription(
        data_source="wifi_logger",
        key="remote_server_a",
        name="Remote Server A",
        icon="mdi:connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolisBinarySensorEntityDescription(
        data_source="wifi_logger",
        key="remote_server_b",
        name="Remote Server B",
        icon="mdi:connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
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
        for data_source in {d.data_source for d in BINARY_SENSOR_DESCRIPTIONS}
    }

    async_add_entities(
        SolisApiBinarySensor(coordinator, description, device_infos[description.data_source])
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class SolisApiBinarySensor(CoordinatorEntity[SolisWifiApiDataUpdateCoordinator], BinarySensorEntity):

    entity_description: SolisBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolisWifiApiDataUpdateCoordinator,
        description: SolisBinarySensorEntityDescription,
        deviceInfo: DeviceInfo | None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        self._attr_device_info = deviceInfo
        # Keep the legacy unique_id format so existing entities/history are preserved
        self._attr_unique_id = Utilities.GenerateUniqueId(
            coordinator, Utilities.FormatSensorName(description.data_source, description.key)
        )

        self._updateValue()
        self._updateAttributes()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._updateValue()
        self._updateAttributes()

        self.async_write_ha_state()

    def _data(self):
        return getattr(self.coordinator.data, self.entity_description.data_source, None)

    def _updateAttributes(self) -> None:

        if self.entity_description.attribute_names:
            self._attr_extra_state_attributes = {
                name: getattr(self._data(), name, None)
                for name in self.entity_description.attribute_names
            }

    def _updateValue(self) -> None:
        self._attr_is_on = getattr(self._data(), self.entity_description.key, None)

    @property
    def available(self) -> bool:
        return getattr(self._data(), self.entity_description.key, None) is not None
