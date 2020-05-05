############################################################################################
#   This script run some setup command to init Iot-Agent for UltraLight as a component of 
# FIWARE system.
#   This script require an api key for each service group define in file 'api_key.py'.
#   Assum different type of devices ( passive devices, initactive devices...) will have it
# different service group,hense with different "fiware-service" and endpoiot. For each iot-agent connected 
# to FIWARE will have each own single "fiware-servicepath", archicture show below:
#                 --------------
#fiware-service: | iota001 |
#                 --------------
#                    -----    -----
#fiware-servicepath:| /ps |  | /is |
#                    -----    -----
#            --------------
#iot-agent: | iot-agent_UL |
#            --------------
#           ---------    ---------
#api keys: | key01   |  | key02   |
#           ---------    ---------
#           ---------    ---------
#resource: | /iot/ps |  | /iot/is |
#           ---------    ---------
#
############################################################################################
import json
import requests

import os

def createServices(setting):
    ORION=setting["system_setting"]["ORION"]
    IOTA=setting["iotagent_setting"]["IOT_AGENT"]
    apikey=setting["iotagent_setting"]["apikey"]
    entity_type=setting["iotagent_setting"]["entity_type"]
    fiware_service=setting["iotagent_setting"]["fiware-service"]
    fiware_servicepath="/"
    header={'Content-Type': 'application/json','fiware-service': fiware_service,'fiware-servicepath': fiware_servicepath}
    data={
     "services": [
       {
         "apikey":      apikey,
         "cbroker":     ORION,
         "entity_type": entity_type,
         "resource":    "/iot/d"
       }
     ]
    }
    r=requests.post(IOTA+"/iot/services",headers=header,data=json.dumps(data))
    return r.status_code
    
def makeSubscription(setting):
    print("start making subscriptions")
    ORION=setting["system_setting"]["ORION"]
    AIOTDFC=setting["system_setting"]["AIOTDFC"]
    QUANTUMLEAP=setting["system_setting"]["QUANTUMLEAP"]
    fiware_service=setting["iotagent_setting"]["fiware-service"]
    fiware_servicepath="/"
    header={"Content-Type": "application/json","fiware-service":fiware_service,"fiware-servicepath":fiware_servicepath}

    for url in [QUANTUMLEAP+"/v2/notify",AIOTDFC+"/notify"]:

        data={
            "description":"Notify QuantumLeap of value changes of any Sensor",
            "subject":{
                "entities":[
                    {
                        "idPattern": ".*",
                        "type":"Sensor"
                    }
                ],
                "condition":{
                    "attrs":[
                        "timestamp"
                        ]
                }
            },
            "notification":{
                "http":{
                    "url":url
                },
                "attrs":["count","predictionValue","anomalyScore","anomalyLikehood","timestamp"]
            }
        }
        if url==AIOTDFC+"/notify":
            data["description"]="Notify Data Flow Contoroler of value changes of any Sensor"
            data["notification"]["attrs"].remove("predictionValue")
            data["notification"]["attrs"].remove("anomalyScore")
            data["notification"]["attrs"].remove("anomalyLikehood")
        r=requests.post(ORION+"/v2/subscriptions?options=skipInitialNotification",headers=header,data=json.dumps(data))
        print(r.status_code,r.text)
        if r.status_code!=201:
            return r.status_code
    return 201
def writebackSetting(setting):
    
    iota_setting={}
    iota_setting["iotagent_setting"]=setting["iotagent_setting"]
    iota_setting["iotagent_setting"].pop("apikey")
    fiware_service=iota_setting["iotagent_setting"].pop("fiware-service")
    iota_setting["iotagent_setting"].pop("entity_type")
    PATH="Data/IoT/"+fiware_service
    os.mkdir(PATH)    
    with open(PATH+"/iotagent-setting.json","w") as opfile:
        json.dump(iota_setting,opfile)
    
    
def initIotagent(setting):
    r=createServices(setting)
    if r!=201:
        return r
    r=makeSubscription(setting)
    if r!=201:
        return r
    writebackSetting(setting)
    
    return 0
    
    
