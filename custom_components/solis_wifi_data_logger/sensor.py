
import logging
from .solis_wifi_api import SystemData

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from .utilities import Utilities
from .data_update_coordinator import SolisWifiApiDataUpdateCoordinator

from .const import DOMAIN,COORDINATOR
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry:ConfigEntry, async_add_entities):

    coordinator: SolisWifiApiDataUpdateCoordinator = hass.data[DOMAIN][COORDINATOR]

    systemdata:SystemData = coordinator.data
    sensors = []

    filteredSystemData = { k:v for (k,v) in systemdata.__dict__.items()}
    for dataSource, value in filteredSystemData.items():
        propertyNames=[a for a in dir(value) if not a.startswith('__') and not callable(getattr(value, a))]
        for propertyName in propertyNames:
            deviceInfo = Utilities.GenerateDeviceInfo(hass, systemdata, dataSource)
            sensor=SolisApiSensor.factory(coordinator,dataSource,propertyName,deviceInfo)
            if(sensor):
                sensors.append(sensor)

    async_add_entities(sensors)

class SolisApiSensor(CoordinatorEntity[SolisWifiApiDataUpdateCoordinator],SensorEntity):

    @staticmethod
    def factory(coordinator: SolisWifiApiDataUpdateCoordinator,dataSource:str,propertyName:str,deviceInfo:DeviceInfo):

        mapping = {
            "inverter" : {
               "temperature" : [SensorDeviceClass.TEMPERATURE, "mdi:thermometer", None, UnitOfTemperature.CELSIUS, SensorStateClass.MEASUREMENT],
               "current_power" : [SensorDeviceClass.POWER, "mdi:solar-power-variant", None, UnitOfPower.WATT, SensorStateClass.MEASUREMENT],
               "daily_power_yield" : [SensorDeviceClass.ENERGY, "mdi:meter-electric", None, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.TOTAL_INCREASING]
            },
            "wifi_logger" : {
               "signal_quality" : [None, "mdi:signal", EntityCategory.DIAGNOSTIC, PERCENTAGE, SensorStateClass.MEASUREMENT],
            }
        }
        if mapping.get(dataSource) and mapping[dataSource].get(propertyName):
           configuration=mapping[dataSource][propertyName]
        
        else:
            return None
        
        return SolisApiSensor(coordinator,dataSource,propertyName,configuration[0],configuration[1],configuration[2],configuration[3],configuration[4],deviceInfo)

    def __init__(self, coordinator: SolisWifiApiDataUpdateCoordinator,dataSource:str,propertyName:str,deviceClass:SensorDeviceClass|None,icon:str,entityCategory:EntityCategory|None,native_unit_of_measurement:str, stateClass:SensorStateClass,deviceInfo:DeviceInfo) -> None:
        super().__init__(coordinator)

        self._dataSource=dataSource
        self._propertyName=propertyName
        self._attr_device_class=deviceClass
        self._attr_icon=icon
        self._attr_state_class=stateClass
        self._attr_entity_category=entityCategory
        self._attr_native_unit_of_measurement=native_unit_of_measurement
        self._attr_should_poll=False

        self._attr_name=Utilities.FormatSensorName(dataSource,propertyName)
        self._attr_device_info=deviceInfo
        self._attr_unique_id=Utilities.GenerateUniqueId(coordinator,self._attr_name)

        #Set Initial Value
        self._attr_native_value=getattr(self._data(),self._propertyName)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value=getattr(self._data(),self._propertyName)
        self.async_write_ha_state()

    def _data(self)->SystemData | None:
        return getattr(self.coordinator.data,self._dataSource,None)    

    @property
    def available(self) -> bool:
        return self._data() is not None and getattr(self._data(),self._propertyName,None) is not None
    
