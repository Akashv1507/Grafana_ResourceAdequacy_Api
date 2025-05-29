import datetime as dt
import requests
import json

class WbesApiService:
    def __init__(self, wbesApiUrl:str, wbesRevNoUrl:str, WbesApiUser:str, WbesApiPass:str, wbesApikey:str):
        self.wbesApiUrl= wbesApiUrl
        self.wbesRevNoUrl = wbesRevNoUrl
        self.WbesApiUser= WbesApiUser
        self.WbesApiPass = WbesApiPass
        self.wbesApikey= wbesApikey
   

    def fetchRevision(self, targetDateStr:str, UtilAcronymList:list ):
        """
        Fetch revision details from wbes API
        """
        params = {"apikey": self.wbesApikey}
        headers = {"Content-Type": "application/json"}
        auth = (self.WbesApiUser,self.WbesApiPass)
        body = {"Date":targetDateStr,"SchdRevNo": -1,"UserName":self.WbesApiUser, "UtilAcronymList": UtilAcronymList,"UtilRegionIdList":[2]}   
        try:
            resp = requests.post( self.wbesRevNoUrl, params=params, auth=auth, data=json.dumps(body), headers=headers)
            if not resp.status_code == 200:
                print(resp.status_code)
                print(f"unable to get data from wbes api")
            respJson = resp.json()
            allRevisionsList=respJson['ResponseBody']["AllRevisions"]
            return allRevisionsList
        except Exception as err:
                print(f'Error while making API call and err-> {err}')
                return []
    
    def fetchScheduleData(self, targetDateStr:str, UtilAcronymList:list, schRevNo:int ):
        """
        Fetch sch data from wbes API
        """
        params = {"apikey": self.wbesApikey}
        headers = {"Content-Type": "application/json"}
        auth = (self.WbesApiUser,self.WbesApiPass)
        body = {"Date":targetDateStr,"SchdRevNo": schRevNo,"UserName":self.WbesApiUser, "UtilAcronymList": UtilAcronymList,"UtilRegionIdList":[2]}   
        try:
            resp = requests.post( self.wbesApiUrl, params=params, auth=auth, data=json.dumps(body), headers=headers)
            if not resp.status_code == 200:
                print(resp.status_code)
                print(f"unable to get data from wbes api")
            respJson = resp.json()
            groupwiseDataList = respJson['ResponseBody']["GroupWiseDataList"]   
            return groupwiseDataList   
        except Exception as err:
                print(f'Error while making API call and err-> {err}')
                return []
                
    def generateBifurcationOfSch(self, groupwiseDataList: list , stateName:str):
        """
        generate Bifurcation Of each Schedule type [OA_REMC, OA_PX, ISGS, ...]
        """   
        if len(groupwiseDataList)>0:
            # it is certain that only one state acronym will be in UtilAcronymList , hence accessing 0th index
            netSchdDataList=groupwiseDataList[0]['NetScheduleSummary']['NetSchdDataList']
            uniqueSchTypeNameList= []
            [uniqueSchTypeNameList.append(sch['EnergyScheduleTypeName']) for sch in netSchdDataList if sch['EnergyScheduleTypeName'] not in uniqueSchTypeNameList]
            #creating empty list of 96 0's for each schedule type
            responseDict = {schType: [0] * 96 for schType in uniqueSchTypeNameList}
            #iterating over each unique schType, and updating responseDict 
            for uniqueSch in uniqueSchTypeNameList:
                #filtering netSchdDataList based on uniqueSch
                filteredNetSchDataList = [ netSch for netSch in netSchdDataList if netSch['EnergyScheduleTypeName'] == uniqueSch]
                #now iterating over filtered list for each sdl type [OA_REMC, OA_PX, ISGS, ...]
                for netSch in filteredNetSchDataList:
                        responseDict[uniqueSch] = [a + b for a, b in zip(responseDict[uniqueSch], netSch["NetSchdAmount"])]  
            # Calculate element-wise sum
            responseDict[f"NetSch-{stateName}"] = [sum(values) for values in zip(*responseDict.values())]  
            return responseDict
        return {}