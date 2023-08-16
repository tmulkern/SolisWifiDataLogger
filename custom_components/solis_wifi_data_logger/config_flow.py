"""Config flow for the Solis Wifi Data Logger platform."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from aiohttp.client_exceptions import ClientConnectionError,ClientResponseError

from .const import DOMAIN,DEFAULT_HOST,DEFAULT_USERNAME
from .solis_wifi_api import(
    SolisWifiApiManager,
    WifiDataLoggerData,
    SolisWifiApiParseException
) 

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST,default=f"http://{DEFAULT_HOST}/"):str,
        vol.Required(CONF_USERNAME,default=DEFAULT_USERNAME,):str,
        vol.Required(CONF_PASSWORD):str
    }
)


@config_entries.HANDLERS.register("SolisWifiDataLogger")
class FlowHandler(config_entries.ConfigFlow,domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the Solis Wifi Data Logger flow."""
        self.host = None

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        if user_input is not None:
            user_input.get(CONF_HOST), user_input.get(CONF_USERNAME),user_input.get(CONF_PASSWORD)
            
            data=await self._attempt_connection(
                user_input.get(CONF_HOST), user_input.get(CONF_USERNAME),user_input.get(CONF_PASSWORD)
            )

            if type(data) is dict:
                return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA,errors=data)
            else:
                return await self._create_entry(data.wifi_logger,user_input.get(CONF_HOST), user_input.get(CONF_USERNAME),user_input.get(CONF_PASSWORD))

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    async def _create_entry(self,data:WifiDataLoggerData, hostname:str, username:str, password:str):
        """Register new entry."""

        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if not self.unique_id:
            await self.async_set_unique_id(f"SolisWifiDataLogger_{data.serial_number}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="SolisWifiDataLogger",
            data={CONF_HOST: hostname, CONF_USERNAME: username, CONF_PASSWORD: password},
        )

    async def _attempt_connection(self, hostname,username, password):
        """Create device."""
        async with SolisWifiApiManager(hostname,username,password) as solr_wifi_api:

            try:
                return await solr_wifi_api.getSystemData()
                #
            except SolisWifiApiParseException as e:
                _LOGGER.error(e)
                return {CONF_HOST:"incorrect_host"}
            except ClientConnectionError as e:
                _LOGGER.error(e)
                return {CONF_HOST:"cannot_connect"}
            except ClientResponseError as e:
                _LOGGER.error(e)

                if e.status==401:
                   return {CONF_PASSWORD:"invalid_auth"}
                if e.status==404:
                   return {CONF_PASSWORD:"incorrect_host"}
                return {"base":"unknown"}


    