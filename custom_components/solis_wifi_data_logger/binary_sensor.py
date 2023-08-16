import logging
from .solis_wifi_api import SystemData

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import callback
from .utilities import Utilities
from .data_update_coordinator import SolisWifiApiDataUpdateCoordinator
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN,COORDINATOR

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):

    coordinator: SolisWifiApiDataUpdateCoordinator = hass.data[DOMAIN][COORDINATOR]

    systemdata:SystemData = coordinator.data

    sensors = []

    filteredSystemData = { k:v for (k,v) in systemdata.__dict__.items()}
    for dataSource, value in filteredSystemData.items():
        propertyNames=[a for a in dir(value) if not a.startswith('__') and not callable(getattr(value, a))]
        for propertyName in propertyNames:
            deviceInfo = Utilities.GenerateDeviceInfo(systemdata,dataSource)
            sensor=SolisApiBinarySensor.factory(coordinator,deviceInfo,dataSource,propertyName)
            if(sensor):
                sensors.append(sensor)

    async_add_entities(sensors)


class SolisApiBinarySensor(CoordinatorEntity[SolisWifiApiDataUpdateCoordinator],BinarySensorEntity):
    
    @staticmethod
    def factory(coordinator: SolisWifiApiDataUpdateCoordinator,deviceInfo:DeviceInfo,dataSource:str,propertyName:str):

        mapping = {
            "inverter" : {
               "alerts" : [BinarySensorDeviceClass.PROBLEM,EntityCategory.DIAGNOSTIC,"mdi:alert",[
                    "serial_number","firmware_version","model"
               ]] 
            },
            "wifi_logger" : {
               "online_status" : [BinarySensorDeviceClass.CONNECTIVITY,None,"mdi:wifi-check",[
                    "last_seen","serial_number","firmware_version"
               ]],
               "wireless_ap_mode" : [None,EntityCategory.CONFIG,"mdi:access-point",None],
               "wireless_sta_mode" : [None,EntityCategory.CONFIG,"mdi:wifi-settings",[
                    "router_ssid","ip_address","mac_address"     
               ]],
               "remote_server_a" : [BinarySensorDeviceClass.CONNECTIVITY,None,"mdi:connection",None,None],
               "remote_server_b" : [BinarySensorDeviceClass.CONNECTIVITY,None,"mdi:connection",None,None]
            }
        }
        if mapping.get(dataSource) and mapping[dataSource].get(propertyName):
           configuration=mapping[dataSource][propertyName]     
        else:
            return None
        
        return SolisApiBinarySensor(coordinator,deviceInfo,dataSource,propertyName,configuration[0],configuration[1],configuration[2],configuration[3])


    def __init__(self,coordinator: SolisWifiApiDataUpdateCoordinator,deviceInfo:DeviceInfo,dataSource:str,propertyName:str,binarySensorDeviceClass:BinarySensorDeviceClass|None,entityCategory:EntityCategory|None,icon:str,attributeNames:list[str]|None):
        super().__init__(coordinator)

        self._dataSource=dataSource
        self._propertyName=propertyName
        self._attr_icon=icon
        
        self._attr_entity_category=entityCategory
        self._attr_device_class=binarySensorDeviceClass
        self._attr_should_poll=False

        self._attr_name=Utilities.FormatSensorName(dataSource,propertyName)
        self._attr_device_info=deviceInfo
        self._attr_unique_id=Utilities.GenerateUniqueId(coordinator,self._attr_name)

        self._attributeNames = attributeNames
        
        self._updateValue()
        self._updateAttributes()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._updateValue()
        self._updateAttributes()

        self.async_write_ha_state()

    def _data(self)->SystemData | None:
        return getattr(self.coordinator.data,self._dataSource,None) 

    def _updateAttributes(self):

        if self._attributeNames:
            attributes = {}
            for attributeName in self._attributeNames:
                attributes[attributeName] = getattr(self._data(),attributeName)
            self._attr_extra_state_attributes = attributes

    def _updateValue(self):
        if self._propertyName:
            self._attr_is_on=getattr(self._data(),self._propertyName)
        else:
            self._attr_is_on=self._data()    
        
    @property
    def available(self) -> bool:
        return self._data() is not None and getattr(self._data(),self._propertyName,None) is not None

    