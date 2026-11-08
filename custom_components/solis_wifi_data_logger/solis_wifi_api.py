from __future__ import annotations

from dataclasses import asdict, dataclass
import aiohttp
import time
from datetime import datetime

import logging

from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

@dataclass
class InverterData:
    serial_number: str
    firmware_version: str|None
    model: str
    temperature: float
    current_power: float
    daily_power_yield: float
    alerts: bool|None

    @classmethod
    def from_dict(cls,data:dict):
        return cls(
            serial_number=data["serial_number"],
            firmware_version=data["firmware_version"],
            model=data["model"],
            temperature=data["temperature"],
            current_power=data["current_power"],
            daily_power_yield=data["daily_power_yield"],
            alerts=data["alerts"],    
        )

@dataclass
class WifiDataLoggerData:
    online_status:bool #derived from connectivity to wifi data logger stick over network
    last_seen:datetime
    serial_number:str
    firmware_version:str|None
    wireless_ap_mode:bool|None
    wireless_sta_mode:bool|None
    router_ssid:str|None
    signal_quality:int
    ip_address:str|None
    mac_address:str
    remote_server_a:bool|None
    remote_server_b:bool|None

    @classmethod
    def from_dict(cls,data:dict):
        # last_seen is serialised to an ISO string in the cache; restore it
        # as a timezone-aware datetime (older caches held naive local times).
        last_seen = data["last_seen"]
        if isinstance(last_seen, str):
            last_seen = dt_util.parse_datetime(last_seen) or dt_util.utc_from_timestamp(0)
        if last_seen.tzinfo is None:
            last_seen = dt_util.as_utc(last_seen)
        return cls(
            online_status=data["online_status"],
            last_seen=last_seen,
            serial_number=data["serial_number"],
            firmware_version=data["firmware_version"],
            wireless_ap_mode=data["wireless_ap_mode"],
            wireless_sta_mode=data["wireless_sta_mode"],
            router_ssid=data["router_ssid"],
            signal_quality=data["signal_quality"],
            ip_address=data["ip_address"],
            mac_address=data["mac_address"],
            remote_server_a=data["remote_server_a"],
            remote_server_b=data["remote_server_b"],   
        )
        

@dataclass
class SystemData:

    inverter:InverterData
    wifi_logger:WifiDataLoggerData

    @classmethod
    def from_dict(cls,data:dict):

        return cls(
            inverter=InverterData.from_dict(data["inverter"]),
            wifi_logger=WifiDataLoggerData.from_dict(data["wifi_logger"])
        )

    def to_dict(self) -> dict:
        """JSON-serialisable representation (used for the persistent cache)."""
        data = asdict(self)
        data["wifi_logger"]["last_seen"] = self.wifi_logger.last_seen.isoformat()
        return data

class SolisWifiApi():

    def __init__(self,hostname:str,username:str,password:str,session:aiohttp.ClientSession) -> None:
        
        _LOGGER.debug("Initializing SolisWifiApi for host %s", hostname)
        self._hostname = hostname.rstrip("/")
        self._auth = aiohttp.BasicAuth(username,password)
        # The session is owned (and closed) by Home Assistant
        self._session = session
   
    async def getSystemData(self) -> SystemData:
        inverter_data = await self.getInverterData()
        wifi_logger_data = await self.getWifiDataLoggerData() 

        return SystemData(inverter_data,wifi_logger_data)   

    async def getInverterData(self) -> InverterData:

        inverterDataRaw= await self._loadDataAndParseResponse("inverter","Inverter",8)

        return InverterData(
            inverterDataRaw[0],
            inverterDataRaw[1],
            inverterDataRaw[2],
            float(inverterDataRaw[3]),
            float(inverterDataRaw[4]),
            float(inverterDataRaw[5]),
            #Data in element 6 is 'Total yield' which only show value 'd'??
            True if inverterDataRaw[7] == "YES" else False
        )



    async def getWifiDataLoggerData(self) -> WifiDataLoggerData:    
        
        monitorDataRaw= await self._loadDataAndParseResponse("moniter","Wifi Data Logger",13)

        return WifiDataLoggerData(
            True,
            dt_util.utcnow(),
            monitorDataRaw[0],
            monitorDataRaw[1],
            True if monitorDataRaw[2] == "Enable" else False,
            #Data in elements 3-5 are Null, do not know what they are
            True if monitorDataRaw[6] == "Enable" else False,
            monitorDataRaw[7],
            int(monitorDataRaw[8]),
            monitorDataRaw[9],
            monitorDataRaw[10],
            True if monitorDataRaw[11] == "Connected" else False,
            True if monitorDataRaw[12] == "Connected" else False
        )
    
    @staticmethod
    def getOffLineData(last_known_system_data:SystemData|None) -> SystemData:

        inverter_data = InverterData(
            last_known_system_data.inverter.serial_number if last_known_system_data else "",
            None,
            last_known_system_data.inverter.model if last_known_system_data else "",
            0,
            0,
            0,
            None
        )

        wifi_logger_data=WifiDataLoggerData(
            False,
            last_known_system_data.wifi_logger.last_seen if last_known_system_data else dt_util.utc_from_timestamp(0),
            last_known_system_data.wifi_logger.serial_number if last_known_system_data else "",
            None,
            None,
            None,
            None,
            0,
            last_known_system_data.wifi_logger.ip_address if last_known_system_data else "",
            last_known_system_data.wifi_logger.mac_address if last_known_system_data else "",
            None,
            None
        )

        return SystemData(inverter_data,wifi_logger_data)

    def _generateTimeToken(self) -> str:
        return str(int(time.time()))
    
    async def _loadDataAndParseResponse(self,dataSource:str,dataSourceName:str,dataExpectedLength:int)-> list[str]:
        url = f"{self._hostname}/{dataSource}.cgi?t={self._generateTimeToken()}"
        async with self._session.get(url, auth=self._auth) as response:
            response.raise_for_status()
            responseText = await response.text()

        dataRaw=self._parseResponseText(responseText)
        
        if len(dataRaw) != dataExpectedLength:
            raise SolisWifiApiParseException(f"Could not parse {dataSourceName} data, please check connection")

        return dataRaw

    def _parseResponseText(self,responseText:str)-> list[str]:

        #Removing NUL characters from response
        cleanedup=responseText.replace("\x00","").removesuffix(";\r\n")    

        return cleanedup.split(";")

class SolisWifiApiParseException(Exception):
    """When the response payload cannot be parsed"""
