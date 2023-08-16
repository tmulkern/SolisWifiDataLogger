import logging
from datetime import timedelta
import async_timeout
from aiohttp.client_exceptions import ClientConnectionError
import aiofiles
import orjson

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .solis_wifi_api import SolisWifiApiManager,SystemData
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

    async def async_update_data(self):
        """Fetch data from the Solis Wifi Data Logger all at once and make it available for
           all devices.
        """
        _LOGGER.debug(f"Executing async_update_data()")

        try:
            async with async_timeout.timeout(20):

                async with SolisWifiApiManager(self._hostname,self._username,self._password) as solis_wifi_api:
                    system_data = await solis_wifi_api.getSystemData()

                    #Cache first time state
                    if self.data == None:
                        await self._cache_system_data(system_data)
                
                _LOGGER.debug(f"inverter_data: {system_data.inverter}")
                _LOGGER.debug(f"wifi_logger_data: {system_data.wifi_logger}")
        except ClientConnectionError:
                #Cache last known state from memory
                if self.data != None and self.data.wifi_logger.online_status:
                        await self._cache_system_data(self.data)

                system_data= await solis_wifi_api.getOffLineData(self.data)

        return system_data
    
    async def _cache_system_data(self,data:SystemData) -> None :
        async with aiofiles.open(JSON_CACHE_FILE, mode='wb') as f:
            await f.write(orjson.dumps(data))