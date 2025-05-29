import random
import requests
from src.appConfig import getAppConfig
import datetime as dt
import json


def fetchScadaPntHistData(pntId: str, startTime: dt.datetime, endTime: dt.datetime, samplingSecs: int = 900) -> list[list[float]]:
    
    appConf = getAppConfig()
    pntId = pntId.strip()
    if pntId == "":
        return []
    urlStr = appConf.histDataUrlBase
    paramsObj = {"pnt": pntId,
                 "strtime": startTime.strftime("%d/%m/%Y/%H:%M:%S"),
                 "endtime": endTime.strftime("%d/%m/%Y/%H:%M:%S"),
                 "secs": samplingSecs,
                 "type": 'average'}
    try:
        r = requests.get(url=urlStr, params=paramsObj)
        data = json.loads(r.text)
        r.close()
    except Exception as e:
        print("Error loading data from scada api")
        print(e)
        data = []
    dataRes: list[list[float]] = []
    for sampl in data:
        dataRes.append([
            sampl["dval"],
            int(dt.datetime.strptime(
                sampl["timestamp"], "%Y-%m-%dT%H:%M:%S").timestamp()*1000)
        ])
    return dataRes