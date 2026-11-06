from __future__ import annotations
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .data_update_coordinator import SolisConfigEntry

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SolisConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = {}
    data["config_data"] = async_redact_data(entry.as_dict(), TO_REDACT)
    return data


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: SolisConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    data = {}
    data["config_data"] = async_redact_data(entry.as_dict(), TO_REDACT)
    coordinator = entry.runtime_data

    if device.name and device.name.startswith("Solis Wifi"):
        data["device_data"] = vars(coordinator.data.wifi_logger)

    if device.name and device.name.startswith("Solis Inverter"):
        data["device_data"] = vars(coordinator.data.inverter)

    return data
