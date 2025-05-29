from flask import Blueprint, jsonify, request
from src.appConfig import getAppConfig
from src.services.reForecastService import ReForecastService
from src.services.scadaFetcher import fetchScadaPntHistData
from src.helperFunctions import adjustToNearestQuarter, filterSchBwTwoTimestamp
from src.grafanaMetrics.reForecastMetrics import dayAheadRevNoOptions, intradayRevNoOptions
from flask_cors import CORS
from dateutil import tz
import datetime as dt


reForecastCompDashApiController = Blueprint('reForecastCompDashApiController', __name__, template_folder='templates', url_prefix="/grafana/api/reForecastComp")
# Enable CORS for this Blueprint, since "/" health check api was not working properly when using bluprint, first it is a preflight option resquest, then get request
CORS(reForecastCompDashApiController)

@reForecastCompDashApiController.route("/", methods=["GET"])
def healthCheck():
    return "",200


@reForecastCompDashApiController.route("/metrics", methods=["POST"])
def getMetrics():
    return jsonify(["Refresh1", "Refresh2"])

@reForecastCompDashApiController.route("/variable", methods=["POST"])
def getVariables():
    requestBodyData= request.get_json()
    payload = requestBodyData.get('payload', "")  
    revisionType= ""
    # checking if revisionType in payload dictionary
    if "revisionType" in payload:
        revisionType = payload.get('revisionType', "")
    if revisionType== 'DayAhead':   
        return jsonify(dayAheadRevNoOptions)
    elif revisionType== 'Intraday': 
        return jsonify(intradayRevNoOptions)
    else:
        return jsonify(dayAheadRevNoOptions)

@reForecastCompDashApiController.route("/query", methods=["POST"])
def queryData():
    appConfig =getAppConfig()
    queryData = request.get_json()
    startTime = dt.datetime.strptime(
        queryData["range"]["from"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    endTime = dt.datetime.strptime(
        queryData["range"]["to"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    #if date of starttime and endtime is not same, starttime will starting 00:00 hrs of endtime date
    startTime = adjustToNearestQuarter(startTime).replace(second=0)
    endTime = adjustToNearestQuarter(endTime).replace(second=0)
    reForecastService = ReForecastService()
    # all grafana variable data will be in scopedVars field
    scopedVars = queryData["scopedVars"]
    #stateName will be like, Maharashtra, Gujarat, WR, 
    stateName = scopedVars['States']['text']
    stateMetaDataDict = getattr(appConfig, stateName)
    reForecastRevisionNo = scopedVars['reForecastRevisions']['value']
    reGenType = scopedVars['reGenType']['value']

    responseTraces = []
    reForecastData = []
    stateActGenration = []
    if reGenType=="SOLAR":
            reForecastData = reForecastService.fetchReForecastData(startTime, endTime, stateMetaDataDict['reStateName'], reGenType, reForecastRevisionNo)
            stateActGenration= fetchScadaPntHistData(pntId=stateMetaDataDict['solarGenScadaPoint'], startTime=startTime, endTime=endTime, samplingSecs=900)
    elif reGenType =="WIND":
            reForecastData = reForecastService.fetchReForecastData(startTime, endTime,  stateMetaDataDict['reStateName'], reGenType, reForecastRevisionNo)
            stateActGenration= fetchScadaPntHistData(pntId=stateMetaDataDict['windGenScadaPoint'], startTime=startTime, endTime=endTime, samplingSecs=900)

    reponseReForecastData= [[float(reForecastPoint['value']), int(dt.datetime.strptime(reForecastPoint['timestamp'], "%Y-%m-%d %H:%M").timestamp() * 1000)] for reForecastPoint in reForecastData]                     
    #setting Traces of actual data and reforecast data
    reForecastTargetData = {
    "target": f"{reGenType}-{stateName}-{reForecastRevisionNo}",
    "datapoints": reponseReForecastData
    } 
    actualDemandTargetData = {
    "target": f'Actual-Generation',
    "datapoints": stateActGenration
    }
    responseTraces.append(reForecastTargetData)
    responseTraces.append(actualDemandTargetData)
    return jsonify(responseTraces)


