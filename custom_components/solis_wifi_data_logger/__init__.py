# SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-only
import logging

from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, COORDINATOR
from .data_update_coordinator import SolisWifiApiDataUpdateCoordinator
from .utilities import Utilities

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

async def async_setup(hass, config):
    """Set up Solis Wifi Data Logger components."""
    hass.data.setdefault(DOMAIN, {})

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solis Wifi Data Logger from a config entry."""

    # Set the Hub up to use and save
    hostname = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    coordinator = SolisWifiApiDataUpdateCoordinator(
        hass,
        hostname,
        username,
        password
    )

    hass.data.setdefault(DOMAIN, {})[COORDINATOR] = coordinator

    await coordinator.async_config_entry_first_refresh()

    # Ensure hub device exists in the device registry so child devices can reference its via_device_id
    hub_info = Utilities.GenerateDeviceInfo(hass, coordinator.data, "wifi_logger")
    if hub_info:
        dev_reg = dr.async_get(hass)
        dev_reg.async_get_or_create(config_entry_id=entry.entry_id, **hub_info)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def options_update_listener(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
    

