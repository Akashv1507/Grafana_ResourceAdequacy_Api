from flask import Blueprint, jsonify, request
from src.appConfig import getAppConfig
from src.services.scadaFetcher import fetchScadaPntHistData
from src.helperFunctions import adjustToNearestQuarter
from src.services.stateDcDataService import StateDcDataService
from flask_cors import CORS
from dateutil import tz
import datetime as dt


stateDcCompDashApiController = Blueprint('stateDcCompDashApiController', __name__, template_folder='templates', url_prefix="/grafana/api/stateDc")

# Enable CORS for this Blueprint, since "/" health check api was not working properly when using bluprint, first it is a preflight option resquest, then get request
CORS(stateDcCompDashApiController)

@stateDcCompDashApiController.route("/", methods=["GET", "OPTIONS"])
def healthCheck():
    return "",200


@stateDcCompDashApiController.route("/metrics", methods=["POST"])
def getMetrics():
    # if you dont implement /metrics endpoint, /query endpoint will not be hit, also you have return some dummy metrics
    return jsonify(["Refresh1", "Refresh2"])

    
@stateDcCompDashApiController.route("/variable", methods=["POST"])
def getVariables():

    requestBodyData= request.get_json()
    payload = requestBodyData.get('payload', "")
    revisionType = payload.get('revisionType', "")
   
    

@stateDcCompDashApiController.route("/query", methods=["POST"])
def queryData():
    appConfig =getAppConfig()
    
    queryData = request.get_json()
    startTime = dt.datetime.strptime(
        queryData["range"]["from"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    endTime = dt.datetime.strptime(
        queryData["range"]["to"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    startTime = adjustToNearestQuarter(startTime).replace(second=0)
    endTime = adjustToNearestQuarter(endTime).replace(second=0)
    scopedVars = queryData["scopedVars"]
    stateScadaId = scopedVars['States']['value'] 
    stateName = scopedVars['States']['text'] #Maharashtra
    genType = scopedVars['genType']['value'] #Thermal, Gas, Hydro
    revisionType = scopedVars['revisionType']['value']# Intraday,DayAhead
    queryStateName= getattr(appConfig, stateName)['raStateName']
    plantIdList= []
    queryDcTblName = ""
    if revisionType == "Intraday":
        queryDcTblName ="intraday_dc_data"
    elif revisionType == "DayAhead":
        queryDcTblName ="day_ahead_dc_data"
    
    stateDcDataService= StateDcDataService(appConfig.RaDbHost, appConfig.RaDbPort, appConfig.RaDbName, appConfig.RaDbUsername, appConfig.RaDbPwd)
    stateDcDataService.connect()
    # getting mapping data and selecting IDs of unit for state and fuel type that obtained from frontend
    mappingDataDict = stateDcDataService.fetchMappingTblData()
    for singleUnitData in mappingDataDict:
        if singleUnitData["state"] ==queryStateName and singleUnitData["fuel_type"]==genType:
            plantIdList.append(singleUnitData["id"])

    stateDcAndNormDcSumTotalBlockwise= stateDcDataService.fetchStateDcData(queryDcTblName, plantIdList, startTime, endTime)



    

    response = []
    
    #Getting Actual Data
    stateActDemData= fetchScadaPntHistData(pntId=stateScadaId, startTime=startTime, endTime=endTime, samplingSecs=900)
    #setting traces for grafana, here called as targets
    actualDemandTargetData = {
    "target": 'Actual-Demand',
    "datapoints": stateActDemData
    }
    #adding above 2 targets to final response
    response.append(actualDemandTargetData)
    return jsonify(response)