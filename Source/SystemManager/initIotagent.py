############################################################################################
#   This script run some setup command to init Iot-Agent for UltraLight as a component of
# FIWARE system.
#   This script require an api key for each service group define in file 'api_key.py'.
#   Assum different type of devices ( passive devices, initactive devices...) will have it
# different service group,hense with different "fiware-service" and endpoiot. For each iot-agent connected
# to FIWARE will have each own single "fiware-servicepath", archicture show below:
#                 --------------
# fiware-service: | iota001 |
#                 --------------
#                    -----    -----
# fiware-servicepath:| /ps |  | /is |
#                    -----    -----
#            --------------
# iot-agent: | iot-agent_UL |
#            --------------
#           ---------    ---------
# api keys: | key01   |  | key02   |
#           ---------    ---------
#           ---------    ---------
# resource: | /iot/ps |  | /iot/is |
#           ---------    ---------
#
############################################################################################
import json
import requests
import logging
import os
import random
import string


class IotAgent():
    def __init__(self):
        self.__PATH__ = os.path.dirname(os.path.abspath(__file__))

    def __generate_apikey__(self, stringLength=26):
        lettersAndDigits = string.ascii_letters + string.digits
        return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))

    def createIotagent(self, iota_setting):
        try:
            with open("./Data/global-setting.json", "r") as f:
                setting = json.load(f)
        except:
            return -1
        self.setting = {**setting, **iota_setting}
        self.ORION = self.setting["system_setting"]["ORION"]
        self.AIOTDFC = self.setting["system_setting"]["AIOTDFC"]
        self.QUANTUMLEAP = self.setting["system_setting"]["QUANTUMLEAP"]
        if type(self.setting["iotagent_setting"])!=list:
            return -2
        for iota in self.setting["iotagent_setting"]:
            try:
                IOTA = iota["Iot-Agent-Url"]
            except:
                return 400
            try:
                apikey = iota["apikey"]
            except:
                iota["apikey"] = apikey = self.__generate_apikey__()
            
            try:
                devicePort=iota["Device-Port"]
            except:
                iota["Device-Port"]=devicePort=""

            try:
                fiware_service = iota["Service-Group"]
                if fiware_service in os.listdir(self.__PATH__+"/../Data/IoT"):
                    continue
            except:
                existNum = sorted([int(x[4:]) for x in os.listdir(
                    self.__PATH__+"/../Data/IoT") if x[-4:] != "json"])
                for i in range(1000):
                    if i not in existNum:
                        iota["Service-Group"] = fiware_service = "iota" + \
                            str(i).zfill(3)
                        break

            iota["Sub-Service-Group"] = fiware_servicepath = "/"

            try:
                resource = iota["Resource"]
            except:
                iota["Resource"] = resource = "/iot/d"

            header = {'Content-Type': 'application/json',
                      'fiware-service': fiware_service, 'fiware-servicepath': fiware_servicepath}
            data = {"services": [{
                "apikey": apikey, "cbroker": self.ORION, "entity_type": "Things", "resource": resource}]}
            requests.post(IOTA+"/iot/services", headers=header,
                          data=json.dumps(data))
            

            for url in [self.QUANTUMLEAP+"/v2/notify", self.AIOTDFC+"/notify"]:

                data = {
                    "description": "Notify QuantumLeap of value changes of Sensor",
                    "subject": {
                        "entities": [{"idPattern": ".*", "type": "Sensor"}],
                        "condition": {"attrs": ["timestamp"]}
                    },
                    "notification": {"http": {"url": url},
                                     "attrs": ["count", "predictionValue", "anomalyScore", "anomalyLikehood", "timestamp", "LogAnomalyLikehood", "Anomaly"]
                                     }
                }
                if url == self.AIOTDFC+"/notify":
                    data["description"] = "Notify Data Flow Contoroler of value changes of Sensor"
                    data["notification"]["attrs"].remove("predictionValue")
                    data["notification"]["attrs"].remove("anomalyScore")
                    data["notification"]["attrs"].remove("anomalyLikehood")
                    data["notification"]["attrs"].remove("LogAnomalyLikehood")
                    data["notification"]["attrs"].remove("Anomaly")
                requests.post(self.ORION+"/v2/subscriptions?options=skipInitialNotification",
                              headers=header, data=json.dumps(data))

            os.mkdir(self.__PATH__+"/../Data/IoT/"+fiware_service)
            
            with open(self.__PATH__+"/../Data/IoT/"+fiware_service+"/iotagent-setting.json", "w") as opfile:
                json.dump({"iotagent_setting": iota}, opfile)

        return 0
