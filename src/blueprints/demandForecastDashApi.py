from flask import Blueprint, jsonify, request
from src.appConfig import getAppConfig
from src.grafanaMetrics.demForeVsActMetrics import dayAheadRevNoOptions, intradayRevNoOptions
from src.services.demandForecastService import DemandForecastService
from src.services.scadaFetcher import fetchScadaPntHistData
from src.helperFunctions import adjustToNearestQuarter
from flask_cors import CORS
from dateutil import tz
import datetime as dt


demandForecastDashApiController = Blueprint('demandForecastDashApiController', __name__, template_folder='templates', url_prefix="/grafana/api/demandForecast")

# Enable CORS for this Blueprint, since "/" health check api was not working properly when using bluprint, first it is a preflight option resquest, then get request
CORS(demandForecastDashApiController)

@demandForecastDashApiController.route("/", methods=["GET", "OPTIONS"])
def healthCheck():
    return "",200


@demandForecastDashApiController.route("/metrics", methods=["POST"])
def getMetrics():
    # if you dont implement /metrics endpoint, /query endpoint will not be hit, also you have return some dummy metrics
    return jsonify(["Refresh1", "Refresh2"])

    
@demandForecastDashApiController.route("/variable", methods=["POST"])
def getVariables():

    requestBodyData= request.get_json()
    payload = requestBodyData.get('payload', "")
    revisionType = payload.get('revisionType', "")
    if revisionType== 'DayAhead':
        return jsonify(dayAheadRevNoOptions)
    elif revisionType== 'Intraday':
        return jsonify(intradayRevNoOptions)
    return jsonify(dayAheadRevNoOptions)
    

@demandForecastDashApiController.route("/query", methods=["POST"])
def queryData():
    appConfig =getAppConfig()
    demandForecastService = DemandForecastService(appConfig.conStringMisWarehouse,appConfig.RaDbHost, appConfig.RaDbPort, appConfig.RaDbName, appConfig.RaDbUsername, appConfig.RaDbPwd)
    queryData = request.get_json()
    startTime = dt.datetime.strptime(
        queryData["range"]["from"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    endTime = dt.datetime.strptime(
        queryData["range"]["to"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    startTime = adjustToNearestQuarter(startTime).replace(second=0)
    endTime = adjustToNearestQuarter(endTime).replace(second=0)
    scopedVars = queryData["scopedVars"]
    stateScadaId = scopedVars['States']['value']
    stateName = scopedVars['States']['text']
    stateMetaDataDict = getattr(appConfig, stateName)
    forecastRevNo = scopedVars['forecastRevisions']['value']
    response = []
    #getting demand Forecast Data
    demandForecastService.connect()
    demandForecastData = demandForecastService.fetchForecastData(start_timestamp=startTime, end_timestamp=endTime, entity_tag=stateScadaId, revision_no=forecastRevNo)
    demandForecastService.disconnect()
    #Getting Actual Data
    stateActDemData= fetchScadaPntHistData(pntId=stateScadaId, startTime=startTime, endTime=endTime, samplingSecs=900)
    # Getting state Load Shedding Data 
    demandForecastService.connectPostgresqlDb()
    stateLoadSheddingData = demandForecastService.fetchLoadSheddingData(startTime, endTime, stateMetaDataDict['raStateName'])
    demandForecastService.disconnectPostgresqlDb()
    #setting traces for grafana, here called as targets
    demandForecastTargetData = {
    "target": f'DemandForecast',
    "datapoints": [[row['forecasted_demand_value'], int(row['timestamp'].timestamp() * 1000)] for row in demandForecastData]
    }
    actualDemandTargetData = {
    "target": 'Actual-Demand',
    "datapoints": stateActDemData
    }
    actualIncludingLs = {
    "target": 'Actual-Demand(Inc.LS)',
    "datapoints": [[row['ls_val'] + stateActDemData[i][0], int(row['timestamp'].timestamp() * 1000)] 
                        for i, row in enumerate(stateLoadSheddingData)]
    }

    #adding above 2 targets to final response
    response.append(demandForecastTargetData)
    response.append(actualDemandTargetData)
    response.append(actualIncludingLs)
    return jsonify(response)