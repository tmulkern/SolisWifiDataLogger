"""Integration platform for recorder."""
from __future__ import annotations

from homeassistant.core import HomeAssistant, callback

from .const import (
    ATTR_SERIAL_NUMBER,
    ATTR_FIRMWARE_VERSION,
    ATTR_MAC_ADDRESS,
    ATTR_MODEL
)


@callback
def exclude_attributes(hass: HomeAssistant) -> set[str]:
    """Exclude static attributes from being recorded in the database."""
    return {
        ATTR_SERIAL_NUMBER,
        ATTR_FIRMWARE_VERSION,
        ATTR_MAC_ADDRESS,
        ATTR_MODEL
    }