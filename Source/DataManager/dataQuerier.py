import os
import requests
import time
import json
import logging
from datetime import datetime
from DataManager import dataPreprocesser
import struct
from ModelManager import modelEntrance


__GLOBAL_THREADHOLD__ = 0.7


def commandIssue(fiware_service, sensorUID, post_data_dict, MODEL_PORT):
    __PATH__ = os.path.dirname(os.path.abspath(__file__))
    try:
        actionType = post_data_dict["actionType"]
        action = post_data_dict["action"]
        metadata = post_data_dict["metadata"]
    except:
        return -4
    if actionType == "modelControl":
        try:
            with open(__PATH__+"/../Data/IoT/"+fiware_service+"/iotagent-setting.json") as f:
                setting = json.load(f)
        except:
            return -3

        IOTA = setting["iotagent_setting"]["Iot-Agent-Url"]
        header = {"fiware-service": fiware_service, 'fiware-servicepath': "/"}
        r = requests.get(IOTA+"/iot/devices/"+sensorUID, headers=header).json()
        try:
            entityID = r["entity_name"]
            attrs = r["static_attributes"]
        except:
            return -1
        static_attributes = {}
        for attr in attrs:
            static_attributes[attr["name"]] = attr["value"]
        data = {"value": action, "device_id": sensorUID, "entity_id": entityID,
                "fiware_service": fiware_service, "metadata": metadata}
        dataSend("COMMAND", data, static_attributes, MODEL_PORT)
        return 0

    elif actionType == "sensorControl":
        pass
        # TODO:Sensor Control
    else:
        return -2


def dataStore(data: dict, MODEL_PORT):
    __PATH__ = os.path.dirname(os.path.abspath(__file__))
    with open(__PATH__+"/../Data/IoT/"+data["fiware_service"]+"/iotagent-setting.json") as f:
        setting = json.load(f)
    IOTA = setting["iotagent_setting"]["Iot-Agent-Url"]
    r = requests.get(IOTA+"/iot/devices",
                     headers={"fiware-service": data["fiware_service"], 'fiware-servicepath': "/"})
    r = r.json()["devices"]
    attrs = None
    for device in r:
        if data["entity_id"] == device["entity_name"]:
            device_id = device["device_id"]
            attrs = device["static_attributes"]
    if attrs == None:
        return [4]
    static_attributes = {}

    for attr in attrs:
        static_attributes[attr["name"]] = attr["value"]
    __DEVICE_PATH__ = __PATH__+"/../Data/IoT/" + \
        data["fiware_service"]+"/"+device_id

    checkResult, data = dataPreprocesser.dataPreprocesser(
        __DEVICE_PATH__, data, device_id, static_attributes)

    if 2 in checkResult:
        return checkResult
    if os.path.isfile(__DEVICE_PATH__+"/inLearning"):
        statusUpdate(__DEVICE_PATH__, data)
        return checkResult
    elif os.path.isfile(__DEVICE_PATH__+"/postLearning"):
        statusUpdate(__DEVICE_PATH__, data)
        sendStatus = dataSend("DATA", data,
                              static_attributes, MODEL_PORT)
        if sendStatus != 0:
            checkResult.append(sendStatus)
        return checkResult
    elif os.path.isfile(__DEVICE_PATH__+"/preLearning"):
        dataCache(__DEVICE_PATH__, data)
        statusUpdate(__DEVICE_PATH__, data)
        if dataReady(__DEVICE_PATH__, static_attributes):
            sendStatus = dataSend("DATA", data,
                                  static_attributes, MODEL_PORT)
            if sendStatus != 0:
                checkResult.append(sendStatus)
        return checkResult


def statusUpdate(__DEVICE_PATH__, data):

    __LOCALNEWEST__ = __DEVICE_PATH__+"/localnewest.tmp"
    value = data["value"]
    timestamp = data["timestamp"]

    with open(__LOCALNEWEST__, "w") as ln:
        ln.write(str(value+","+str(timestamp)))


def dataCache(__DEVICE_PATH__, data):
    __COUNTER__ = __DEVICE_PATH__+"/counter.tmp"
    if not os.path.isfile(__COUNTER__):
        with open(__COUNTER__, "w+") as c:
            c.write("0")
            c.close()
    with open(__COUNTER__, "r") as c:
        count = int(c.read())
    count += 1
    with open(__COUNTER__, "w") as c:
        c.write(str(count))
    value = data["value"]
    timestamp = data["timestamp"]
    __LOCALDATA__ = __DEVICE_PATH__+"/localdata.tmp"
    if not os.path.isfile(__LOCALDATA__):
        with open(__LOCALDATA__, "w+") as f:
            f.write("value,timestamp\n"+data["dataType"]+",datetime\n ,T\n")
            f.close()
    with open(__LOCALDATA__, "a") as ld:
        ld.write(str(value+","+str(timestamp)+"\n"))


def dataReady(path, static_attributes):
    targetTime = float(static_attributes["targetTime"])
    timeResolution = float(static_attributes["timeResolution"])

    targetCount = targetTime/timeResolution
    with open(path+"/counter.tmp", "r") as c:
        count = int(c.read())
    msg = path+"\nCount:"+str(count)+","+str(int((count/targetCount)*100))+"%"
    logging.info("Sensor At "+msg)
    if targetCount > count:
        return False
    else:
        return True


def dataSend(dType: str, data: dict, static_attributes: dict, MODEL_PORT):
    message = {"dType": dType, "data": data,
               "static_attributes": static_attributes}
    modelEntrance.modelPortal(message, __GLOBAL_THREADHOLD__)
    return 0
