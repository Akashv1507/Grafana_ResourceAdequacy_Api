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
    # no specific query variable related to State Dc Comparison Screen
    return ""

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
    stateName = scopedVars['States']['text'] #Maharashtra
    genType = scopedVars['genType']['value'] #Thermal, Gas, Hydro
    revisionType = scopedVars['revisionType']['value']# Intraday,DayAhead
    queryStateName= getattr(appConfig, stateName)['raStateName']
    thermalGenScadaPoint= getattr(appConfig, stateName)['thermalGenScadaPoint']
    thermalAndGasGenScadaPoint= getattr(appConfig, stateName)['thermal&GasGenScadaPoint']
    hydelGenScadaPoint= getattr(appConfig, stateName)['hydelGenScadaPoint']
    dcMultiplier= getattr(appConfig, stateName)['dcMultiplier']
    stateDcDataService= StateDcDataService(appConfig.RaDbHost, appConfig.RaDbPort, appConfig.RaDbName, appConfig.RaDbUsername, appConfig.RaDbPwd)
    stateDcDataService.connect()
    stateDcAndNormDcSumTotalBlockwise= stateDcDataService.fetchStateDcAndNormDcData(startTime, endTime, queryStateName, revisionType, genType )
    stateDcDataService.disconnect()
    stageScadaGenerationData = []
    #Getting Actual generation
    if genType=='Thermal':
        stateThermalGenData= fetchScadaPntHistData(pntId=thermalGenScadaPoint, startTime=startTime, endTime=endTime, samplingSecs=900)
        stageScadaGenerationData = stateThermalGenData
    elif genType == 'Gas':
        # gas point will contain generation of both thermal and gas, hence subtracting thermal values
        stateThermalGenData = fetchScadaPntHistData(pntId=thermalGenScadaPoint, startTime=startTime, endTime=endTime, samplingSecs=900)
        stateThermalAndGasGenData = fetchScadaPntHistData(pntId=thermalAndGasGenScadaPoint, startTime=startTime, endTime=endTime, samplingSecs=900)
        stageScadaGenerationData = [[(a[0] - b[0]), a[1]] for a, b in zip(stateThermalAndGasGenData, stateThermalGenData)]
    elif genType == 'Hydro':
        stateHydelGenData = fetchScadaPntHistData(pntId=hydelGenScadaPoint, startTime=startTime, endTime=endTime, samplingSecs=900)
        stageScadaGenerationData = stateHydelGenData
    
    dcMultiplierTrace = {
    "target": 'DC',
    "datapoints": [[dcMultiplier*(row["dc_val"]), int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    # dcTrace = {
    # "target": 'DC',
    # "datapoints": [[(row["dc_val"]), int(row['timestamp'].timestamp() * 1000)] 
    #                     for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    # }
    outageCapcityTrace = {
    "target": 'Outage-Capacity',
    "datapoints": [[row["outage_capacity"], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    normativeDcTrace = {
    "target": 'Normative-DC',
    "datapoints": [[row["normative_dc"], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateDcAndNormDcSumTotalBlockwise)]
    }
    actualGenTrace = {
    "target": 'Actual-Generation',
    "datapoints": stageScadaGenerationData
    }
    response = []
    #adding above 3 targets to final response
    response.append(outageCapcityTrace)
    # response.append(dcTrace)
    response.append(dcMultiplierTrace)
    response.append(normativeDcTrace)
    response.append(actualGenTrace)
    return jsonify(response)