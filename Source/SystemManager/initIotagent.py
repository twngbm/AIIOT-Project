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

    def initIotagent(self):
        try:
            with open(self.__PATH__+"/../Data/global-setting.json", "r") as f:
                setting = json.load(f)
        except:
            return 422, "{'Status':'Initial FIWARE First'}"
        try:
            with open(self.__PATH__+"/../iotagent_config.cfg", "r") as iotaf:
                iota_setting = json.load(iotaf)
        except:
            return 422,  "{'Status':'IoT Agent Config Error'}"
        self.setting = {**setting, **iota_setting}
        self.ORION = self.setting["system_setting"]["ORION"]
        self.AIOTDFC = self.setting["system_setting"]["AIOTDFC"]
        self.QUANTUMLEAP = self.setting["system_setting"]["QUANTUMLEAP"]
        if type(self.setting["iotagent_setting"]) != list:
            return 422, "{'Status':'Wrong Format, Must Be List'}"
        rt = []
        for iota in self.setting["iotagent_setting"]:
            try:
                IOTA = iota["Iot-Agent-Url"]
            except:
                return 422, "{'Status':'Must Specific Iot-Agent-Url'}"
            try:
                apikey = iota["apikey"]
            except:
                iota["apikey"] = apikey = self.__generate_apikey__()

            try:
                devicePort = iota["Device-Port"]
            except:
                iota["Device-Port"] = devicePort = ""

            try:
                resource = iota["Resource"]
            except:
                iota["Resource"] = resource = "/iot/d"

            iota["Service-Group"] = fiware_service = "iota"
            iota["Sub-Service-Group"] = fiware_servicepath = "/"

            header = {'Content-Type': 'application/json',
                      'fiware-service': fiware_service, 'fiware-servicepath': fiware_servicepath}
            data = {"services": [{
                "apikey": apikey, "cbroker": self.ORION, "entity_type": "Things", "resource": resource}]}
            r = requests.post(IOTA+"/iot/services", headers=header,
                              data=json.dumps(data))

            rt.append((r.status_code, r.text, r.url))

        for url in [self.QUANTUMLEAP+"/v2/notify", self.AIOTDFC+"/notify"]:

            data = {
                "description": "Notify QuantumLeap of value changes of Sensor",
                "subject": {
                    "entities": [{"idPattern": ".*", "type": "Sensor"}],
                    "condition": {"attrs": ["timestamp"]}
                },
                "notification": {"http": {"url": url},
                                    "attrs": ["count", "predictionValue", "rawanomalyScore", "rawanomalyLikehood", "timestamp", "anomalyScore", "anomalyFlag"]
                                    }
            }
            if url == self.AIOTDFC+"/notify":
                data["description"] = "Notify Data Flow Contoroler of value changes of Sensor"
                data["notification"]["attrs"].remove("predictionValue")
                data["notification"]["attrs"].remove("rawanomalyScore")
                data["notification"]["attrs"].remove("rawanomalyLikehood")
                data["notification"]["attrs"].remove("anomalyScore")
                data["notification"]["attrs"].remove("anomalyFlag")
            r = requests.post(self.ORION+"/v2/subscriptions?options=skipInitialNotification",
                                headers=header, data=json.dumps(data))
            rt.append((r.status_code, r.text, r.url))

        with open(self.__PATH__+"/../Data/iotagent-setting.json", "w") as opfile:
            json.dump({"iotagent_setting": self.setting["iotagent_setting"]}, opfile)
        errorStack = []
        for ret in rt:
            if ret[0] != 201:
                errorStack.append(ret)
        if errorStack == []:
            return 201, ""
        else:
            return 422, json.dumps(errorStack)
