import datetime as dt
import requests
from src.appConfig import getAppConfig

class ReForecastService:
    def __init__(self):
        pass
        
    
    def fetchReForecastData(self, startTime: dt.datetime, endTime: dt.datetime, stateCode: str, genType: str, revisionNo: str):
        """
        Fetch data from the REMC API
        """
        startTime = startTime.replace(tzinfo=None, microsecond=0)
        endTime = endTime.replace(tzinfo=None, microsecond=0)
        appConfig = getAppConfig()
        remcApiBaseUrl= appConfig.remcApiBaseUrl
        remcRevisionHistEndpoint= f"{remcApiBaseUrl}/api/hist/revisions"
        stateReForecastData= []
        try:
            response = requests.get(remcRevisionHistEndpoint, params={"startDatetime": startTime, "endDatetime": endTime, "stateCode": stateCode, "genType": genType, "revisionNo": revisionNo, "fspID":"FSP00005" })
            if response.ok:
                responseData= response.json()
                stateReForecastData = responseData['responseData']
            else:
                responseData= response.json()
                print(responseData['responseData'])
        except Exception as err:
            print(f"API call failed with error -> {err}")
        return stateReForecastData
        