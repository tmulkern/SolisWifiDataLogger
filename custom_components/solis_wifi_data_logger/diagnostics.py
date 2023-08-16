from __future__ import annotations
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN,COORDINATOR
from .data_update_coordinator import SolisWifiApiDataUpdateCoordinator

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = {}
    data["config_data"] = entry.as_dict()
    return data


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    data = {}
    data["config_data"] = entry.as_dict()
    coordinator: SolisWifiApiDataUpdateCoordinator = hass.data[DOMAIN][COORDINATOR]

    if device.name.startswith("Solis Wifi"):
        data["device_data"] = vars(coordinator.data.wifi_logger)

    if device.name.startswith("Solis Inverter"):
        data["device_data"] = vars(coordinator.data.inverter)

    return data
