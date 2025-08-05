from flask import Blueprint, jsonify, request
from src.appConfig import getAppConfig
from src.services.scadaFetcher import fetchScadaPntHistData
from src.helperFunctions import adjustToNearestQuarter, filterSchBwTwoTimestamp
from src.services.stateDeficitDataService import StateDeficitDataService
from flask_cors import CORS
from dateutil import tz
import datetime as dt


stateDeficitCompDashApiController = Blueprint('stateDeficitCompDashApiController', __name__, template_folder='templates', url_prefix="/grafana/api/stateDeficitComp")
# Enable CORS for this Blueprint, since "/" health check api was not working properly when using bluprint, first it is a preflight option resquest, then get request
CORS(stateDeficitCompDashApiController)

@stateDeficitCompDashApiController.route("/", methods=["GET"])
def healthCheck():
    return "",200


@stateDeficitCompDashApiController.route("/metrics", methods=["POST"])
def getMetrics():
    return jsonify(["Refresh1", "Refresh2"])

@stateDeficitCompDashApiController.route("/variable", methods=["POST"])
def getVariables():
    appConfig=getAppConfig()
    requestBodyData= request.get_json()
    payload = requestBodyData.get('payload', "")
    timeRange = requestBodyData.get('range', "")
    #setting default values starttime, endtime, and revision type
    endTime= dt.datetime.now()
    allRevisionsList= []
    revisionType= "DayAhead"
    # checking if from and to keys present in timeRange
    if "from" in timeRange and "to" in timeRange:
        endTime = dt.datetime.strptime(
            timeRange["to"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    # converting only endTime for fetching deficit revision no.
    targetDate= endTime.date()
    stateDeficitDataService= StateDeficitDataService(appConfig.RaDbHost, appConfig.RaDbPort, appConfig.RaDbName, appConfig.RaDbUsername, appConfig.RaDbPwd)
   
    # checking if revisionType, state variable in payload dictionary
    if "revisionType" in payload:
        revisionType = payload.get('revisionType', "")
    if revisionType== 'DayAhead':
        stateDeficitDataService.connect()
        deficitRevisionNos = stateDeficitDataService.fetchDeficitRevisionNo(targetDate, 'DA')
        stateDeficitDataService.disconnect()
        allRevList= [ {"__text": f"{revision['def_rev_no']} | {revision['time']}", "__value":revision['def_rev_no'] } for revision in deficitRevisionNos]
        return jsonify(allRevList)
    elif revisionType== 'Intraday':
        stateDeficitDataService.connect()
        deficitRevisionNos = stateDeficitDataService.fetchDeficitRevisionNo(targetDate, 'INTRADAY')
        stateDeficitDataService.disconnect()
        allRevList= [ {"__text": f"{revision['def_rev_no']} | {revision['time']}", "__value":revision['def_rev_no'] } for revision in deficitRevisionNos]
        return jsonify(allRevList)
    else:
        stateDeficitDataService.connect()
        deficitRevisionNos = stateDeficitDataService.fetchDeficitRevisionNo(targetDate, 'INTRADAY')
        stateDeficitDataService.disconnect()
        allRevList= [ {"__text": f"{revision['def_rev_no']} | {revision['time']}", "__value":revision['def_rev_no'] } for revision in deficitRevisionNos]
        return jsonify(allRevList)

@stateDeficitCompDashApiController.route("/query", methods=["POST"])
def queryData():
    appConfig =getAppConfig()
    queryData = request.get_json()
    startTime = dt.datetime.strptime(
        queryData["range"]["from"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    endTime = dt.datetime.strptime(
        queryData["range"]["to"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    startTime = adjustToNearestQuarter(startTime).replace(second=0)
    endTime = adjustToNearestQuarter(endTime).replace(second=0)
    targetDate= endTime.date()
    scopedVars = queryData["scopedVars"]
    stateName = scopedVars['States']['text'] #Maharashtra
    revisionType = scopedVars['revisionType']['value']# Intraday,DayAhead
    deficitRevNo = scopedVars['deficitRevisionNo']['value']# DA1,DA2, INT1, INT2...
    raStateName= getattr(appConfig, stateName)['raStateName']
    deviationScadaPoint= getattr(appConfig, stateName)['deviationScadaPoint']
       
    stateDeficitDataService= StateDeficitDataService(appConfig.RaDbHost, appConfig.RaDbPort, appConfig.RaDbName, appConfig.RaDbUsername, appConfig.RaDbPwd)
    stateDeficitDataService.connect()
    stateDcAndNormDcSumTotalBlockwise= stateDeficitDataService.fetchStateDeficitData(startTime, endTime, raStateName, deficitRevNo )
    allParamsRevNo = stateDeficitDataService.fetchAllParamsRevisionNo(targetDate, deficitRevNo)
    stateDeficitDataService.disconnect()
  
    #Getting deviation data from scada
    stateDeviationData = fetchScadaPntHistData(pntId=deviationScadaPoint, startTime=startTime, endTime=endTime, samplingSecs=900)
    defRevNo = (allParamsRevNo or {}).get("def_rev_no", "")
    forecastRevNo = (allParamsRevNo or {}).get("forecast_rev_no", "")
    schRevNo = (allParamsRevNo or {}).get("sch_rev_no", "")
    dcRevNo = (allParamsRevNo or {}).get("dc_rev_no", "")
    reForecastRevNo = (allParamsRevNo or {}).get("reforecast_rev_no", "")
    defTrace = {
    "target": f'Deficit-{defRevNo}',
    "datapoints": [[row["def_val"], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    forecastTrace = {
    "target": f'DemForecast-{forecastRevNo}',
    "datapoints": [[row["forecast_val"], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    wbesSdlTrace = {
    "target": f'WBES-SDL-{schRevNo}',
    "datapoints": [[row["sdl_val"], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    dcTrace = {
    "target": f'DC-{dcRevNo}',
    "datapoints": [[row["dc_val"], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    windForecastTrace = {
    "target": f'Wind-Fore-{reForecastRevNo}',
    "datapoints": [[row["wind_fore_val"], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    solarForecastTrace = {
    "target": f'Solar-Fore-{reForecastRevNo}',
    "datapoints": [[row["solar_fore_val"], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    othersTrace = {
    "target": 'Others',
    "datapoints": [[row["others_val"], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    deviationTrace = {
    "target": 'Deviation',
    "datapoints": stateDeviationData
    }
    response = []
    #adding above 3 targets to final response
    response.append(defTrace)
    response.append(forecastTrace)
    response.append(wbesSdlTrace)
    response.append(dcTrace)
    response.append(windForecastTrace)
    response.append(solarForecastTrace)
    response.append(othersTrace)
    response.append(deviationTrace)
    return jsonify(response)