from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, STORAGE_VERSION
from .solis_wifi_api import SolisWifiApi, SolisWifiApiParseException, SystemData


_LOGGER = logging.getLogger(__name__)

type SolisConfigEntry = ConfigEntry[SolisWifiApiDataUpdateCoordinator]


class SolisWifiApiDataUpdateCoordinator(DataUpdateCoordinator[SystemData]):

    config_entry: SolisConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: SolisConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            # Name of the data. For logging purposes.
            name="solis_wifi_api",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=10)
        )
        self._api = SolisWifiApi(
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_PASSWORD],
            async_get_clientsession(hass),
        )
        # Persists the last known state across restarts (per config entry)
        self._store: Store[dict] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_{config_entry.entry_id}"
        )

    async def _async_update_data(self) -> SystemData:
        """Fetch data from the Solis Wifi Data Logger all at once and make it available for
           all devices.
        """
        _LOGGER.debug("Executing _async_update_data()")

        try:
            async with asyncio.timeout(20):
                system_data = await self._api.getSystemData()
        except (ClientConnectionError, TimeoutError):
            # Logger is unreachable (e.g. inverter asleep at night): report offline state
            if self.data is not None and self.data.wifi_logger.online_status:
                await self._store.async_save(self.data.to_dict())

            last_known = self.data if self.data is not None else await self._load_cached_data()
            return self._api.getOffLineData(last_known)
        except (ClientResponseError, SolisWifiApiParseException) as err:
            raise UpdateFailed(f"Error communicating with Solis Wifi Data Logger: {err}") from err

        _LOGGER.debug("inverter_data: %s", system_data.inverter)
        _LOGGER.debug("wifi_logger_data: %s", system_data.wifi_logger)

        # Cache first time state
        if self.data is None:
            await self._store.async_save(system_data.to_dict())

        return system_data

    async def _load_cached_data(self) -> SystemData | None:
        """Load the last known state from storage, if any."""
        stored = await self._store.async_load()
        if not stored:
            return None
        try:
            return SystemData.from_dict(stored)
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.debug("Could not load cached data: %s", err)
            return None
