from flask import Blueprint, jsonify, request
from src.appConfig import getAppConfig
from src.services.wbesApiService import WbesApiService
from src.services.scadaFetcher import fetchScadaPntHistData
from src.helperFunctions import adjustToNearestQuarter, filterSchBwTwoTimestamp
from flask_cors import CORS
from dateutil import tz
import datetime as dt


schduleCompDashApiController = Blueprint('schduleCompDashApiController', __name__, template_folder='templates', url_prefix="/grafana/api/scheduleComp")
# Enable CORS for this Blueprint, since "/" health check api was not working properly when using bluprint, first it is a preflight option resquest, then get request
CORS(schduleCompDashApiController)

@schduleCompDashApiController.route("/", methods=["GET"])
def healthCheck():
    return "",200


@schduleCompDashApiController.route("/metrics", methods=["POST"])
def getMetrics():
    return jsonify(["Refresh1", "Refresh2"])

@schduleCompDashApiController.route("/variable", methods=["POST"])
def getVariables():
    appConfig=getAppConfig()
    wbesApiService = WbesApiService(appConfig.wbesApiUrl, appConfig.wbesRevNoUrl, appConfig.WbesApiUser, appConfig.WbesApiPass, appConfig.wbesApikey)
    requestBodyData= request.get_json()
    payload = requestBodyData.get('payload', "")
    timeRange = requestBodyData.get('range', "")
    #setting default values starttime, endtime, and revision type
    endTime= dt.datetime.now()
    startTime=endTime-dt.timedelta(hours=6)
    allRevisionsList= []
    revisionType= ""
    # checking if from and to keys present in timeRange
    if "from" in timeRange and "to" in timeRange:
        startTime = dt.datetime.strptime(
            timeRange["from"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
        endTime = dt.datetime.strptime(
            timeRange["to"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    #converting only endTime for wbes Api call
    targetDateStr= endTime.strftime('%d-%m-%Y')
    # checking if revisionType, state variable in payload dictionary
    if "revisionType" in payload:
        revisionType = payload.get('revisionType', "")
    # no of revision is same for any state hence picking wbesAcr for maharashtra
    stateWbesAcr= appConfig.Maharashtra['wbesAcr']
    allRevisionsList=wbesApiService.fetchRevision(targetDateStr, [stateWbesAcr])
    if revisionType== 'DayAhead':
        filteredDaRevisions= [ {"__text": f"R{revision['RevisionNo']}", "__value":revision['RevisionNo'] } for revision in allRevisionsList if dt.datetime.strptime(revision["RevisionDateTimeStamp"], "%d-%m-%Y %H:%M:%S").date()<endTime.date()]
        filteredDaRevisions.insert(0, {"__text": "LatestRev", "__value": -1})
        return jsonify(filteredDaRevisions)
    elif revisionType== 'Intraday':
        filteredIntradayRevisions= [ {"__text": f"R{revision['RevisionNo']}", "__value":revision['RevisionNo'] } for revision in allRevisionsList if dt.datetime.strptime(revision["RevisionDateTimeStamp"], "%d-%m-%Y %H:%M:%S").date()==endTime.date()]
        filteredIntradayRevisions.insert(0, {"__text": "LatestRev", "__value": -1})
        return jsonify(filteredIntradayRevisions)
    else:
        allRevList= [ {"__text": f"R{revision['RevisionNo']}", "__value":revision['RevisionNo'] } for revision in allRevisionsList]
        allRevList.insert(0, {"__text": "LatestRev", "__value": -1})
        return jsonify(allRevList)

@schduleCompDashApiController.route("/query", methods=["POST"])
def queryData():
    appConfig =getAppConfig()
    wbesApiService = WbesApiService(appConfig.wbesApiUrl, appConfig.wbesRevNoUrl, appConfig.WbesApiUser, appConfig.WbesApiPass, appConfig.wbesApikey)
    queryData = request.get_json()
    startTime = dt.datetime.strptime(
        queryData["range"]["from"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    endTime = dt.datetime.strptime(
        queryData["range"]["to"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    #if date of starttime and endtime is not same, starttime will starting 00:00 hrs of endtime date
    startTime = adjustToNearestQuarter(startTime).replace(second=0)
    endTime = adjustToNearestQuarter(endTime).replace(second=0)
    if startTime.date() != endTime.date():
        startTime= dt.datetime.combine(endTime.date(), dt.time(0, 0, 0), tzinfo=endTime.tzinfo)
    targetDateStr= endTime.strftime('%d-%m-%Y')
    scopedVars = queryData["scopedVars"]
    #stateName will be like, Maharashtra, Gujarat, WR, 
    stateName = scopedVars['States']['text']
    stateScadaId = scopedVars['States']['value']
    responseTraces = []
    # since no wbes acronym for WR, making wbes API cal for only Mah, Guj, MP, Chatt
    if stateName!= "WR":
        schRev1 = scopedVars['schRev1']['value']
        schRev2 = scopedVars['schRev2']['value']
        # getting wbesAcr from class AppConfig class using getattr method
        stateWbesAcr = getattr(appConfig, stateName)['wbesAcr']
        for schRev in [schRev1, schRev2]:
            groupwiseDataList = wbesApiService.fetchScheduleData(targetDateStr, [stateWbesAcr], schRev)
            bifurcatedSchDataDict = wbesApiService.generateBifurcationOfSch(groupwiseDataList, stateName)
            for key in bifurcatedSchDataDict:
                filteredSchListForPlot = filterSchBwTwoTimestamp(bifurcatedSchDataDict[key], startTime, endTime)
                #setting traces for grafana, here called as targets
                targetData = {"target": f'{key}_R{schRev}', "datapoints": filteredSchListForPlot}
                responseTraces.append(targetData)
                        
    #Getting Actual Data
    stateActDemData= fetchScadaPntHistData(pntId=stateScadaId, startTime=startTime, endTime=endTime, samplingSecs=900)
    actualDemandTargetData = {
    "target": f'Actual-Demand',
    "datapoints": stateActDemData
    }
    responseTraces.append(actualDemandTargetData)
    return jsonify(responseTraces)


