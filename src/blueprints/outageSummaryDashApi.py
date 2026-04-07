from flask import Blueprint, jsonify, request
from src.appConfig import getAppConfig
from src.services.outageSummaryService import OutageSummaryService
from src.helperFunctions import adjustToNearestQuarter
from flask_cors import CORS
from dateutil import tz
import datetime as dt
import pandas as pd

outageSummaryDashApiController = Blueprint('outageSummaryDashApiController', __name__, template_folder='templates', url_prefix="/grafana/api/outageSummary")

# Enable CORS for this Blueprint, since "/" health check api was not working properly when using bluprint, first it is a preflight option resquest, then get request
CORS(outageSummaryDashApiController)

@outageSummaryDashApiController.route("/centralVsStateSectorOutages", methods=["GET", "OPTIONS"])
def healthCheck():
    return "",200


@outageSummaryDashApiController.route("/centralVsStateSectorOutages/metrics", methods=["POST"])
def getMetrics():
    # if you dont implement /metrics endpoint, /query endpoint will not be hit, also you have return some dummy metrics
    return jsonify(["Refresh1", "Refresh2"])

@outageSummaryDashApiController.route("/centralVsStateSectorOutages/query", methods=["POST"])
def queryData():
    appConfig =getAppConfig()
    outageSummaryService = OutageSummaryService(appConfig.RaDbHost, appConfig.RaDbPort, appConfig.RaDbName, appConfig.RaDbUsername, appConfig.RaDbPwd)
    queryData = request.get_json()
    startTime = dt.datetime.strptime(
        queryData["range"]["from"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    endTime = dt.datetime.strptime(
        queryData["range"]["to"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    startTime = adjustToNearestQuarter(startTime).replace(second=0)
    endTime = adjustToNearestQuarter(endTime).replace(second=0)  
    response = []
    # Getting state Load Shedding Data 
    outageSummaryService.connectPostgresqlDb()
    outageSummaryData = outageSummaryService.fetchOutageSummaryData(startTime, endTime)
    outageSummaryService.disconnectPostgresqlDb()
    if len(outageSummaryData) == 0:
        targetData = {"target": 'No Data'," datapoints": []}
        response.append(targetData)
        return jsonify(response)
    # 1. Ensure datetime
    outageSummaryDataDf = pd.DataFrame(outageSummaryData)
    #filtering last timestamp value for each date using max()
    outageSummaryDataDf['time_stamp'] = pd.to_datetime(outageSummaryDataDf['time_stamp'])
    outageSummaryDailyLastDataDf = outageSummaryDataDf.groupby(outageSummaryDataDf['time_stamp'].dt.date).apply(lambda x: x[x['time_stamp'] == x['time_stamp'].max()]).reset_index(drop=True)

    # 3. Replace timestamp with just date
    outageSummaryDailyLastDataDf['DATE'] = outageSummaryDailyLastDataDf['time_stamp'].dt.date
    # df_daily_last = df_daily_last.drop(columns=['time_stamp'])

    # replacing classsification 
    mapping = {'ISGS': 'CENTRAL_SECTOR', 'REGIONAL_IPP': 'CENTRAL_SECTOR', 'STATE_OWNED': 'STATE_SECTOR', 'STATE_IPP': 'STATE_SECTOR'}
    outageSummaryDailyLastDataDf['classification'] = outageSummaryDailyLastDataDf['classification'].replace(mapping)
    # grouping based on date, classification, shutdown_type and summing outage_val
    finalResponseOutageSummaryDf = outageSummaryDailyLastDataDf.groupby(['DATE', 'classification', 'shutdown_type'], as_index=False)['outage_val'].sum()
    # now grouping classfication and shutdown type and geting all traces
    for (cl, st), group in finalResponseOutageSummaryDf.groupby(['classification', 'shutdown_type']):
        group = group.sort_values('DATE')
        x = group['DATE'].tolist()
        y = [float(v) for v in group['outage_val']]
        targetData = {"target": f'{cl}-{st}', 
                      "datapoints": [[y[i], 
                                      int(dt.datetime.combine(x[i], dt.time(23,45)).timestamp()*1000)] for i in range(len(x))]}
        response.append(targetData)
    return jsonify(response)


