from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .solis_wifi_api import SystemData
from .data_update_coordinator import SolisWifiApiDataUpdateCoordinator

class Utilities:

    @staticmethod
    def FormatSensorName(dataSourceName:str,propertyName:str) -> str:
        dataSourceNameFormated=dataSourceName.lower()
        
        if propertyName:
            propertyNameFormated=propertyName.lower()
            return f"{dataSourceNameFormated}_{propertyNameFormated}"
        else:
            return f"{dataSourceNameFormated}"
        
    @staticmethod
    def GenerateUniqueId(coordinator: DataUpdateCoordinator,sensorName:str) -> str:
        return f"{DOMAIN}_{coordinator.data.wifi_logger.serial_number}_{sensorName}"
    
    @staticmethod
    def GenerateDeviceInfo(systemData:SystemData,dataSource:str) -> DeviceInfo|None:

        if dataSource == "wifi_logger":
            return DeviceInfo(
                configuration_url= f"http://{systemData.wifi_logger.ip_address}",
                model="",
                sw_version=systemData.wifi_logger.firmware_version,
                hw_version=systemData.wifi_logger.serial_number,
                manufacturer="Solis",
                name="Solis Wifi Data Logger Stick",
                identifiers={(DOMAIN, f"solis_wifi_data_logger_{systemData.wifi_logger.serial_number}")},
                connections={(DOMAIN,f"http://{systemData.wifi_logger.ip_address}")},
            )

        if dataSource == "inverter":     
            return DeviceInfo(
                model=systemData.inverter.model,
                sw_version=systemData.inverter.firmware_version,
                hw_version=systemData.inverter.serial_number,
                manufacturer="Solis",
                name=f"Solis Inverter",
                identifiers={(DOMAIN, f"solis_{systemData.inverter.model}_{systemData.inverter.serial_number}")},
                via_device=(DOMAIN, f"solis_wifi_data_logger_{systemData.wifi_logger.serial_number}")
            )
        
        return None