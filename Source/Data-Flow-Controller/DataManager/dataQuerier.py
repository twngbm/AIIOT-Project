import os
import requests
import time
import json
import logging
from datetime import datetime

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