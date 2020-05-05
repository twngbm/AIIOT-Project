import os
import requests
import time
import json
import logging
from datetime import datetime
import select
from DataManager import dataPreprocesser


def dataStore(data:dict):
    data_is_ready=False
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
    checkResult,data=dataPreprocesser.dataPreprocesser(__DEVICE_PATH__,data,static_attributes)
    if 2 in checkResult:
        pass
    else:
        count=dataCache(__DEVICE_PATH__,data)
        data_is_ready=dataReady(count,static_attributes)
    if data_is_ready:
        #TODO
        #TODO
        #TODO
        #TODO
        #TODO
        #TODO
        #Tell model manager to start train.
        #Set Flag to stop local caching.
        pass
    return checkResult
def dataCache(__DEVICE_PATH__,data):
    __LOCALDATA__=__DEVICE_PATH__+"/localdata.tmp"
    __COUNTER__=__DEVICE_PATH__+"/counter.tmp"
    __LOCALNEWEST__=__DEVICE_PATH__+"/localnewest.tmp"
    value=data["value"]
    timestamp=data["timestamp"]
    with open(__COUNTER__,"r") as c:
        count=int(c.read())
    count+=1
    with open(__COUNTER__,"w") as c:
        c.write(str(count))
    with open(__LOCALNEWEST__,"w") as ln:
        ln.write(str(value+","+str(timestamp)))
    with open(__LOCALDATA__,"a") as ld:
        ld.write(str(value+","+str(timestamp)+"\n"))
    return count

def dataReady(count,static_attributes):
    targetTime=float(static_attributes["targetTime"])
    timeResolution=float(static_attributes["timeResolution"])
    targetCount=targetTime/timeResolution
    print(targetCount,count)
    if targetCount>count:
        return False
    else:
        return True
"""
class dataQuerier():
    def __init__(self,_id,fiware_service,received_mode):
        self.fiware_service=fiware_service
        if not os.path.isfile("./Data/global-setting-entityID.json"):
            logging.warning("Initial FIWARE First")
            return 404
        if not os.path.isfile("./Data/IoT/"+fiware_service+"/iotagent-setting.json"):
            logging.warning("Initial Iotagent Named '"+fiware_service+"' First")
            return 404
        with open("./Data/IoT/"+fiware_service+"/iotagent-setting.json") as f:
            self.setting=json.load(f)
        IOTA=self.setting["iotagent_setting"]["IOT_AGENT"]
        r=requests.get(IOTA+"/iot/devices",headers={"fiware-service":fiware_service,'fiware-servicepath': "/"})
        r=r.json()["devices"]
        for device in r:
            if received_mode:
                if _id==device["entity_name"]:
                    self.device_id=device["device_id"]
                    self.entity_name=_id
                    self.statice_attributes=device["static_attributes"]
            else:
                if _id==device["device_id"]:
                    self.device_id=_id
                    self.entity_name=device["entity_name"]
                    self.statice_attributes=device["static_attributes"]
        self.swarm_finished=1 if os.path.isfile("./Data/IoT/"+self.fiware_service+"/"+self.device_id+"/swarm_finished") else 0
        
        

    def checkAmount(self):
        data_path="./Data/IoT/"+self.fiware_service+"/"+self.device_id+"/localdata.tmp"
        for sta_attr in self.statice_attributes:
            if sta_attr["name"]=="timeResolution":
                self.time_resolution=int(sta_attr["value"])
        with open(data_path,"r") as f:
            count=int(f.readline())
            
        count+=1
        
        with open(data_path,"w") as f:
            #if count>= int(604800/self.time_resolution):
            if count>= 10:
                header={'Content-Type': 'application/json'}
                sql='{"stmt":"SELECT count,time_index FROM mt'+self.fiware_service+'.etsensor WHERE entity_id=\''+self.entity_name+'\'AND time_index>0 ORDER BY time_index"}'
                r=requests.get("http://fiware-cratedb:4200/_sql",headers=header,data=sql)
                info=r.json()
                print(info)
            else:
                f.write(str(count))
                
    def restartCheck(self):
        pass
if __name__=="__main__":
    __PATH__=os.path.dirname(os.path.abspath(__file__))
    __DATAPIPEPATH__=__PATH__+"/../Data.pipe"
    datapipe=os.open(__DATAPIPEPATH__,os.O_RDONLY|os.O_NONBLOCK)
    epoll=select.epoll()
    epoll.register(datapipe,select.POLLIN)
    
"""