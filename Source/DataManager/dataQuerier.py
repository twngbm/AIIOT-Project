import os
import requests
import time
import json
import logging
from datetime import datetime
from DataManager import dataPreprocesser
import struct
from ModelManager import modelEntrance
from SystemManager.SysConfig import __GLOBAL_THREADHOLD__


def commandIssue(service_group, sensorUID, post_data_dict, MODEL_PORT):
    __PATH__ = os.path.dirname(os.path.abspath(__file__))
    try:
        actionType = post_data_dict["actionType"]
        action = post_data_dict["action"]
        metadata = post_data_dict["metadata"]
    except:
        return 422, "{'Status':'Wrong Format'}"

    if actionType == "modelControl":
        try:
            with open(__PATH__+"/../Data/IoT/"+service_group+"/"+sensorUID+"/device.cfg") as f:
                setting = json.load(f)
        except:
            return 406, "{'Status':'Target Service Group Not Found'}"

        entityID = setting["entityID"]
        static_attributes = setting["static_attributes"]
        data = {"value": action, "device_name": sensorUID, "entity_id": entityID,
                "service_group": service_group, "metadata": metadata}
        dataSend("COMMAND", data, static_attributes, MODEL_PORT)
        return 200, "{'Status':'Command Issue'}"

    elif actionType == "sensorControl":
        pass
        # TODO:Sensor Control
    else:
        return 418, "{'Status':'Error Command Type'}"


def dataStore(data: dict, MODEL_PORT):
    __PATH__ = os.path.dirname(os.path.abspath(__file__))
    deviceName = data["entity_id"].split(":")[3]
    with open(__PATH__+"/../Data/IoT/"+data["service_group"]+"/"+deviceName+"/device.cfg") as f:
        setting = json.load(f)
    __DEVICE_PATH__ = __PATH__+"/../Data/IoT/" + \
        data["service_group"]+"/"+deviceName
    static_attributes = setting["static_attributes"]
    checkResult, data = dataPreprocesser.dataPreprocesser(
        __DEVICE_PATH__, data, deviceName, static_attributes)

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
        if dataReady(__DEVICE_PATH__, static_attributes, data["service_group"], deviceName):
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


def dataReady(path, static_attributes, iota, deviceName):
    targetTime = float(static_attributes["targetTime"])
    timeResolution = float(static_attributes["timeResolution"])

    targetCount = targetTime/timeResolution
    with open(path+"/counter.tmp", "r") as c:
        count = int(c.read())
    msg = str(iota)+"/"+str(deviceName)+" Data Amount:" + \
        str(count)+","+str(int((count/targetCount)*100))+"%"
    logging.info(msg)
    if targetCount > count:
        return False

    else:
        return True


def dataSend(dType: str, data: dict, static_attributes: dict, MODEL_PORT):
    message = {"dType": dType, "data": data,
               "static_attributes": static_attributes}
    modelEntrance.modelPortal(message, __GLOBAL_THREADHOLD__)
    return 0
