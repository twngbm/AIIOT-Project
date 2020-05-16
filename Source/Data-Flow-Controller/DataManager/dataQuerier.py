import os
import requests
import time
import json
import logging
from datetime import datetime
import select
from DataManager import dataPreprocesser
import socket
import struct

def dataStore(data:dict):
    __PATH__=os.path.dirname(os.path.abspath(__file__))
    with open(__PATH__+"/../Data/IoT/"+data["fiware_service"]+"/iotagent-setting.json") as f:
        setting=json.load(f)
    IOTA=setting["iotagent_setting"]["IOT_AGENT"]
    r=requests.get(IOTA+"/iot/devices",headers={"fiware-service":data["fiware_service"],'fiware-servicepath': "/"})
    r=r.json()["devices"]
    for device in r:
        if data["entity_id"]==device["entity_name"]:
            device_id=device["device_id"]
            attrs=device["static_attributes"]
    static_attributes={}
    for attr in attrs:
        static_attributes[attr["name"]]=attr["value"]
    __DEVICE_PATH__=__PATH__+"/../Data/IoT/"+data["fiware_service"]+"/"+device_id

    checkResult,data=dataPreprocesser.dataPreprocesser(__DEVICE_PATH__,data,device_id,static_attributes)

    if 2 in checkResult:
        return checkResult
    if os.path.isfile(__DEVICE_PATH__+"/inLearning"):
        statusUpdate(__DEVICE_PATH__,data)
        return checkResult
    elif os.path.isfile(__DEVICE_PATH__+"/postLearning"):
        statusUpdate(__DEVICE_PATH__,data)
        sendStatus=dataSend(__PATH__,data,static_attributes)
        if sendStatus!=0:
            checkResult.append(sendStatus)
        return checkResult
    elif os.path.isfile(__DEVICE_PATH__+"/preLearning"):
        dataCache(__DEVICE_PATH__,data)
        statusUpdate(__DEVICE_PATH__,data)
        if dataReady(__DEVICE_PATH__,static_attributes):
            sendStatus=dataSend(__PATH__, data,static_attributes)
            if sendStatus!=0:
                checkResult.append(sendStatus)
        return checkResult
def statusUpdate(__DEVICE_PATH__,data):
    
    __LOCALNEWEST__=__DEVICE_PATH__+"/localnewest.tmp"
    value=data["value"]
    timestamp=data["timestamp"]
   

    with open(__LOCALNEWEST__,"w") as ln:
        ln.write(str(value+","+str(timestamp)))
def dataCache(__DEVICE_PATH__,data):
    __COUNTER__=__DEVICE_PATH__+"/counter.tmp"
    with open(__COUNTER__,"r") as c:
        count=int(c.read())
    count+=1
    with open(__COUNTER__,"w") as c:
        c.write(str(count))
    value=data["value"]
    timestamp=data["timestamp"]
    __LOCALDATA__=__DEVICE_PATH__+"/localdata.tmp"
    with open(__LOCALDATA__,"a") as ld:
        ld.write(str(value+","+str(timestamp)+"\n"))

def dataReady(path,static_attributes):
    targetTime=float(static_attributes["targetTime"])
    timeResolution=float(static_attributes["timeResolution"])

    targetCount=targetTime/timeResolution
    with open(path+"/counter.tmp","r") as c:
        count=int(c.read())
    msg=path+"Count:"+str(count)+","+str(int((count/targetCount)*100))+"%"
    logging.info("Sensor At "+msg)
    if targetCount>count:
        return False
    else:
        return True

def dataSend(path:str,data:dict,static_attributes:dict):
    content=json.dumps({"data":data,"static_attributes":static_attributes})
    ClientSocket = socket.socket()
    try:
        ClientSocket.connect(('localhost', 5000))
    except:
        return 3
    ClientSocket.send(content.encode("utf8"))
    ClientSocket.close()
    return 0