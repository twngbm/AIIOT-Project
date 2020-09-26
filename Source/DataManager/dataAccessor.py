import json
import os
from crate import client
import time
import logging
import datetime
import csv
import requests
import shutil
from DataManager import dataQuerier
__PATH__ = os.path.dirname(os.path.abspath(__file__))


def trainoutputWriteback(path: str, Data, __GLOBAL_THREADHOLD__: float):
    with open(path, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        service_group = Data.data.service_group
        entity_id = Data.data.entityID
        for row in reader:
            timestamp = row[header.index("timestamp")]
            predictionValue = row[header.index("prediction")]
            anomalyScore = row[header.index("anomaly_score")]
            anomalyLikelihood = row[header.index("anomaly_likelihood")]
            logAnomalyLikelihood = row[header.index("Log_anomaly_likelihood")]
            if float(logAnomalyLikelihood) > __GLOBAL_THREADHOLD__:
                anomaly = "True"
            else:
                anomaly = "False"
            writeToCratedb(
                service_group,
                entity_id,
                timestamp,
                predictionValue,
                anomalyScore,
                anomalyLikelihood,
                logAnomalyLikelihood,
                anomaly,
            )


def resultWriteback(timestamp: datetime, value, anomalyScore: float, anomalyFlag: bool, metadata: dict, Data):

    rawanomalyScore = metadata["rawanomalyScore"] if "rawanomalyScore" in metadata else None
    rawanomalyLikelihood = metadata["rawanomalyLikelihood"] if "rawanomalyLikelihood" in metadata else None
    predictionValue = metadata["predictionValue"] if "predictionValue" in metadata else None
    writeToCratedb(
        Data.data.service_group,
        Data.data.entityID,
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        str(predictionValue),
        str(rawanomalyScore),
        str(rawanomalyLikelihood),
        str(anomalyScore),
        str(anomalyFlag)
    )


def writeToCratedb(
    service_group: str,
    entity_id: str,
    timestamp: str,
    predictionValue: str,
    rawanomalyScore: str,
    rawanomalyLikeliHood: str,
    anomalyScore: str,
    anomalyFlag: str
):
    with open(__PATH__+"/../Data/global-setting.json", "r") as f:

        global_setting = json.load(f)
    __CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()
    timestamp = timestamp.split(" ")
    timestamp = timestamp[0]+"T"+timestamp[1]
    while True:
        cursor.execute(
            "SELECT * FROM mtiota.etsensor WHERE time_index = DATE_TRUNC ('second','" +
            timestamp+"') AND entity_id='"+entity_id+"'"
        )
        result = cursor.fetchall()
        if len(result) == 0:
            logging.warning("CrateDB Entity Not Found, Retrying")
            time.sleep(1)
        else:
            break
    cursor.execute("UPDATE mtiota.etsensor\
                    SET anomalyflag = " + anomalyFlag +
                   ",rawanomalylikehood = " + rawanomalyLikeliHood +
                   ",rawanomalyscore = " + rawanomalyScore +
                   ",anomalyscore = " + anomalyScore +
                   ",predictionvalue = " + predictionValue +
                   "WHERE entity_id = '"+entity_id+"' \
                    AND time_index=DATE_TRUNC ('second','"+timestamp+"')")


def queFromCratedbBack(entity_id: str, timestamp):
    with open(__PATH__+"/../Data/global-setting.json", "r") as f:
        global_setting = json.load(f)
    __CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()
    timestamp = (timestamp-datetime.datetime(1970, 1, 1)).total_seconds()*1000
    cursor.execute(
        "SELECT * FROM mtiota.etsensor \
        WHERE time_index > "+str(int(timestamp)) +
        " AND entity_id='"+entity_id+"'\
        ORDER BY time_index"
    )
    header = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    output = [{header[i]:x[i] for i in range(len(header))} for x in result]
    return output


def queFromCratedbBound(entity_id: str, StartTime, EndTime):
    with open(__PATH__+"/../Data/global-setting.json", "r") as f:
        global_setting = json.load(f)
    __CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()
    StartTime = (StartTime-datetime.datetime(1970, 1, 1)).total_seconds()*1000
    EndTime = (EndTime-datetime.datetime(1970, 1, 1)).total_seconds()*1000
    cursor.execute(
        "SELECT * FROM mtiota.etsensor \
        WHERE time_index > "+str(int(StartTime)) +
        " AND time_index < "+str(int(EndTime)) +
        " AND entity_id='"+entity_id+"'\
        ORDER BY time_index"
    )
    header = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    output = [{header[i]:x[i] for i in range(len(header))} for x in result]
    return output


def queFromCratedbNewest(entity_id: str, limit: int):
    with open(__PATH__+"/../Data/global-setting.json", "r") as f:
        global_setting = json.load(f)
    __CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM mtiota.etsensor \
        WHERE time_index > 0 AND entity_id='"+entity_id+"'\
        ORDER BY time_index DESC LIMIT "+str(limit)
    )
    header = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    output = [{header[i]:x[i] for i in range(len(header))} for x in result]
    return output[::-1]


class SystemInfo():
    def __init__(self, MODEL_PORT):
        self.MODEL_PORT = MODEL_PORT
        self.__PATH__ = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(__PATH__+"/../Data/global-setting.json", "r") as f:
                setting = json.load(f)
            self.ORION = setting["system_setting"]["ORION"]
            self.CRATEDB = setting["system_setting"]["CRATEDB"]
            self.QUANTUMLEAP = setting["system_setting"]["QUANTUMLEAP"]
            self.AIOTDFC = setting["system_setting"]["AIOTDFC"]
        except:
            raise IOError


class Cleaner(SystemInfo):
    def __init__(self, MODEL_PORT):
        super().__init__(MODEL_PORT)
        viewer = Viewer(self.MODEL_PORT)
        self.sg_tree = viewer.listServiceGroupAndDevice()

    def removeIoTSensor(self, service_group, DeviceID):
        with open(self.__PATH__+"/../Data/IoT/"+service_group+"/"+DeviceID+"/device.cfg", "r") as iotafile:
            iota_setting = json.load(iotafile)
            IOTA = iota_setting["iotagent_config"]["Iot-Agent-Url"]
            entityID = iota_setting["entityID"]

        data = {'actionType': "modelControl",
                'action': "Remove",
                "metadata": None
                }
        dataQuerier.commandIssue(
            service_group, DeviceID, data, self.MODEL_PORT)
        header = {'fiware-service': "iota", 'fiware-servicepath': "/"}
        requests.delete(IOTA+"/iot/devices/"+DeviceID, headers=header)
        requests.delete(self.ORION+"/v2/entities/"+entityID, headers=header)
        header = {'Content-Type': 'application/json'}
        sql = '{"stmt":"DELETE FROM mtiota' + \
            '.etsensor WHERE entity_id = \''+entityID+'\'"}'
        requests.get(self.CRATEDB+"/_sql", headers=header, data=sql)
        shutil.rmtree(__PATH__+"/../Data/IoT/"+service_group+"/"+DeviceID)

    def removeServiceGroup(self, service_group):

        for d in self.sg_tree[service_group]:
            self.removeIoTSensor(service_group, d)
        shutil.rmtree(__PATH__+"/../Data/IoT/"+service_group)

    def removeSubscription(self, fiware_service, subscriptionID):
        header = {'fiware-service': fiware_service, 'fiware-servicepath': "/"}
        requests.delete(self.ORION+"/v2/subscriptions/" +
                        subscriptionID, headers=header)

    def removeEntity(self, entityID):
        r = requests.delete(self.ORION+"/v2/entities/" + entityID)
        return r.status_code, r.text

    def removeEntityAttr(self, entityID, attr):
        r = requests.delete(self.ORION+"/v2/entities/" +
                            entityID+"/attrs/"+attr)
        return r.status_code, r.text

    def resetIoTAgent(self):
        with open(self.__PATH__+"/../Data/iotagent-setting.json", "r") as iotafile:
            iotacfg = json.load(iotafile)["iotagent_setting"]
        for iota_setting in iotacfg:
            IOTA = iota_setting["Iot-Agent-Url"]
            fiware_service = iota_setting["Service-Group"]

            resource = iota_setting["Resource"]
            apikey = iota_setting["apikey"]

        header = {'Content-Type': 'application/json'}
        sql = '{"stmt":"DROP TABLE IF EXISTS mt'+fiware_service+'.etsensor"}'
        r = requests.get(self.CRATEDB+"/_sql", headers=header, data=sql)

        header = {'fiware-service': fiware_service, 'fiware-servicepath': "/"}
        requests.delete(IOTA+"/iot/services/?resource=" +
                        resource+"&apikey="+apikey, headers=header)
        r = requests.get(self.ORION+"/v2/subscriptions", headers=header).json()
        for subscription in r:
            requests.delete(self.ORION+"/v2/subscriptions/" +
                            subscription["id"], headers=header)
        shutil.rmtree(__PATH__+"/../Data/IoT/")

    def reset(self):

        for sg in self.sg_tree:
            self.removeServiceGroup(sg)

        r = requests.get(self.ORION+"/v2/entities")
        for entity in r.json():
            r = requests.delete(self.ORION+"/v2/entities/"+entity["id"])
        self.resetIoTAgent()
        shutil.rmtree(__PATH__+"/../Data")

        return 0


class Creator(SystemInfo):
    def __init__(self, MODEL_PORT):
        super().__init__(MODEL_PORT)

    def createSubscription(self, endpoint, post_data_dict):
        try:
            url = post_data_dict["Url"]
            service_group = endpoint.split("/")[2]
        except:
            raise KeyError
        try:
            condition = post_data_dict["Condition"]
        except:
            condition = "timestamp"
        with open(self.__PATH__+"/../Data/IoT/"+service_group+"/subscription.json", "r") as f:
            try:
                subscriptionList = json.load(f)
            except:
                subscriptionList = {"BuildIn": {}, "Expand": {}}
        if condition == "timestamp" or condition == "count":
            data = {
                "description": "Notify "+url+" of "+condition+" changes.",
                "subject": {
                    "entities": [{"idPattern": service_group, "type": "Sensor"}],
                    "condition": {"attrs": [condition]}
                },
                "notification": {"http": {"url": url},
                                 "attrs": ["count", "timestamp"]
                                 }
            }
            header = {'Content-Type': 'application/json',
                      'fiware-service': "iota", 'fiware-servicepath': "/"}
            requests.post(self.ORION+"/v2/subscriptions?options=skipInitialNotification",
                          headers=header, data=json.dumps(data))
            header.pop('Content-Type')
            r = requests.get(self.ORION+"/v2/subscriptions", headers=header)
            buildInSubscription=json.loads(r.text)
            for sub in buildInSubscription:
                if sub["subject"]["entities"][0]["idPattern"]==service_group:
                    if sub["id"] not in subscriptionList["BuildIn"]:
                        subscriptionList["BuildIn"][sub["id"]]=sub
        else:
            pass

        return r.status_code, r.text


class Updater(SystemInfo):
    def __init__(self, MODEL_PORT):
        super().__init__(MODEL_PORT)

    def updateEntity(self, entityID, attrs):
        header = {'Content-Type': 'application/json'}
        actionType = attrs.pop("actionType", None)
        data = {}
        if actionType == "update":
            data["actionType"] = "append"
        elif actionType == "append":
            data["actionType"] = "append_strict"
        else:
            return 400, "{'Status':'Wrong Data Format'}"
        data["entities"] = [{"id": entityID}]
        for attr in attrs:
            data["entities"][0][attr] = attrs[attr]
        r = requests.post(self.ORION+"/v2/op/update",
                          headers=header, data=json.dumps(data))
        return r.status_code, r.text


class Viewer(SystemInfo):
    def __init__(self, MODEL_PORT):
        super().__init__(MODEL_PORT)

    def listEntities(self, additionEndpiont="", query={}):
        if additionEndpiont == "" or additionEndpiont == "/":
            return requests.get(self.ORION+"/v2/entities", params=query).text
        else:
            try:
                targetEntity = additionEndpiont.split("/")[1]
                fiware_service = targetEntity.split(":")[1]
            except:
                return -1
            header = {}
            if targetEntity.find("urn:ngsi-ld") == -1:
                header = {
                    'fiware-service': fiware_service, "fiware-servicepath": "/"}
            return requests.get(self.ORION+"/v2/entities"+additionEndpiont, headers=header, params=query).text

    def listDevices(self, additionEndpiont, query):
        info = ""
        try:
            service_group = additionEndpiont.split("/")[1]
        except:
            return -1
        try:
            deviceID = additionEndpiont.split("/")[2]
        except:
            deviceID = ""

        try:
            dirlist = os.listdir(
                self.__PATH__+"/../Data/IoT/"+service_group)
        except:
            return -2

        if deviceID != "":
            try:
                info = additionEndpiont.split("/")[3]
            except:
                info = "info"
            if deviceID not in dirlist:
                return -2
            with open(self.__PATH__+"/../Data/IoT/"+service_group+"/"+deviceID+"/device.cfg", "r") as f:
                iota_setting = json.load(f)
            iota_url = iota_setting["iotagent_config"]["Iot-Agent-Url"]
            header = {'fiware-service': "iota",
                      "fiware-servicepath": "/"}

            if info == "model":
                try:
                    dirlist = os.listdir(
                        self.__PATH__+"/../Data/IoT/"+service_group+"/"+deviceID)
                except:
                    return -2

                for i in dirlist:
                    if "Learning" in i:
                        return json.dumps({"ModelState": i})

            elif info == "data":
                entity_id = requests.get(
                    iota_url+"/iot/devices/"+deviceID, headers=header).json()["entity_name"]
                connection = client.connect(self.CRATEDB)
                cursor = connection.cursor()
                try:
                    limit = "LIMIT "+query["limit"]
                except:
                    limit = ""
                try:
                    attritubes = query["attrs"]
                except:
                    attritubes = "*"
                try:
                    cursor.execute(
                        "SELECT "+attritubes+" FROM mtiota.etsensor\
                         WHERE time_index > 0 AND entity_id='"+entity_id+"'\
                        ORDER BY time_index DESC  "+limit
                    )
                except Exception as e:
                    return e

                header = [column[0] for column in cursor.description]
                result = cursor.fetchall()
                output = [{header[i]:x[i]
                           for i in range(len(header))} for x in result]
                return json.dumps(output)
            elif info == "controls":
                try:
                    os.listdir(self.__PATH__+"/../Data/IoT/" +
                               service_group+"/"+deviceID)
                    return json.dumps({"modelControl": ["Reset,Remove,Save,Sleep,Train,Wake"], "sensorControl": []})
                except:
                    return -2

            else:
                return requests.get(iota_url+"/iot/devices/"+deviceID, headers=header).text

        elif deviceID == "":
            deviceList = os.listdir(
                self.__PATH__+"/../Data/IoT/"+service_group)
            deviceList.remove("subscription.json")
            return deviceList

    def listServiceGroups(self, additionEndpiont, query):
        sg = os.listdir(self.__PATH__+"/../Data/IoT/")

        if additionEndpiont == "" and query == {}:
            return json.dumps({"type": "service-groups", "value": sg, "metadata": {}})

        elif additionEndpiont.split("/")[1] in sg:
            service_group = additionEndpiont.split("/")[1]
            try:
                subEndpoint = additionEndpiont.split("/")[2]
            except:
                subEndpoint = ""
            deviceList = os.listdir(
                self.__PATH__+"/../Data/IoT/"+service_group)
            deviceList.remove("subscription.json")
            with open(self.__PATH__+"/../Data/IoT/"+service_group+"/subscription.json", "r") as f:
                try:
                    subscriptionList = json.load(f)
                except:
                    subscriptionList = {}
            if subEndpoint == "devices":
                return deviceList
            elif subEndpoint == "subscriptions":
                return subscriptionList
            else:
                return {"Device": deviceList, "Subscription": subscriptionList}

    def listSubscriptions(self, additionEndpiont, query):
        try:
            fiware_service = additionEndpiont.split("/")[1]
        except:
            return -1
        try:
            subscriptionID = additionEndpiont.split("/")[2]
        except:
            subscriptionID = ""

        header = {'fiware-service': fiware_service, "fiware-servicepath": "/"}

        return requests.get(self.ORION+"/v2/subscriptions/"+subscriptionID, headers=header).text

    def listServiceGroupAndDevice(self) -> dict:
        tree = {}
        for sg in os.listdir(self.__PATH__+"/../Data/IoT/"):
            tree[sg] = []
            for d in os.listdir(self.__PATH__+"/../Data/IoT/"+sg+"/"):
                if "subscription.json" not in d:
                    tree[sg].append(d)

        return tree
