# SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-only
import logging

from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST,CONF_USERNAME,CONF_PASSWORD
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN, COORDINATOR
from .data_update_coordinator import SolisWifiApiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up Heamiser Neo components."""
    hass.data.setdefault(DOMAIN, {})

    return True

async def async_setup_entry(hass:HomeAssistantType, entry:ConfigEntry):
    """Set up Solis Wifi Data Logger from a config entry."""

    # Set the Hub up to use and save
    hostname = entry.data[CONF_HOST]
    username=entry.data[CONF_USERNAME]
    password=entry.data[CONF_PASSWORD]


    coordinator = SolisWifiApiDataUpdateCoordinator(
        hass,
        hostname,
        username,
        password
    )

    hass.data[DOMAIN][COORDINATOR] = coordinator

    await coordinator.async_config_entry_first_refresh()
    
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True

async def options_update_listener(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
    

