import asyncio
import logging
from datetime import timedelta
from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError
import aiofiles
import orjson

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .solis_wifi_api import SolisWifiApiManager, SolisWifiApiParseException, SystemData
from .const import JSON_CACHE_FILE


_LOGGER = logging.getLogger(__name__)

class SolisWifiApiDataUpdateCoordinator(DataUpdateCoordinator[SystemData]):

    def __init__(self, hass:HomeAssistant, hostname:str,username:str,password:str):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="solis_wifi_api",
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=10)
        )
        self._hostname=hostname
        self._username=username
        self._password=password

    async def async_update_data(self) -> SystemData:
        """Fetch data from the Solis Wifi Data Logger all at once and make it available for
           all devices.
        """
        _LOGGER.debug("Executing async_update_data()")

        async with SolisWifiApiManager(self._hostname, self._username, self._password) as solis_wifi_api:
            try:
                async with asyncio.timeout(20):
                    system_data = await solis_wifi_api.getSystemData()

                    # Cache first time state
                    if self.data is None:
                        await self._cache_system_data(system_data)

                _LOGGER.debug("inverter_data: %s", system_data.inverter)
                _LOGGER.debug("wifi_logger_data: %s", system_data.wifi_logger)
            except (ClientConnectionError, TimeoutError):
                # Cache last known state from memory
                if self.data is not None and self.data.wifi_logger.online_status:
                    await self._cache_system_data(self.data)

                system_data = await solis_wifi_api.getOffLineData(self.data)
            except (ClientResponseError, SolisWifiApiParseException) as err:
                raise UpdateFailed(f"Error communicating with Solis Wifi Data Logger: {err}") from err

        return system_data
    
    async def _cache_system_data(self,data:SystemData) -> None :
        async with aiofiles.open(JSON_CACHE_FILE, mode='wb') as f:
            await f.write(orjson.dumps(data))