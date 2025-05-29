from dataclasses import dataclass, field
import json


@dataclass
class AppConfig:
    flaskSecret: str = field(default="")
    flaskHost: str = field(default="localhost")
    flaskPort: int = field(default=8080)
    histDataUrlBase:str = field(default="")
    conStringMisWarehouse:str = field(default="")
    wbesApiUrl:str = field(default="")
    wbesRevNoUrl:str = field(default="")
    WbesApiUser:str = field(default="")
    WbesApiPass:str = field(default="")
    wbesApikey:str = field(default="")
    Maharashtra:dict = field(default="")
    Gujarat:dict = field(default="")
    MP:dict = field(default="")
    WR:dict = field(default="")
    Chattisgarh:dict = field(default="")
    RaDbName:str = field(default="")
    RaDbUsername:str = field(default="")
    RaDbPwd:str = field(default="")
    RaDbHost:str= field(default="")
    RaDbPort:int = field(default=8080)
    remcApiBaseUrl:str = field(default="")
    

def loadAppConfig(fName="config/config.json") -> AppConfig:
    global jsonConfig
    with open(fName) as f:
        data = json.load(f)
        jsonConfig = AppConfig(**data)
        return jsonConfig


def getAppConfig() -> AppConfig:
    global jsonConfig
    return jsonConfig