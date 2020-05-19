import os
import requests
import json
import shutil
def cleanFiware(setting,entityID=None):
    ORION=setting["system_setting"]["ORION"]
    if entityID!=None:
        pass
    else:        
        r=requests.get(ORION+"/v2/entities")
        for entity in r.json():
            print("Remove entity: ",entity["id"])
            r=requests.delete(ORION+"/v2/entities/"+entity["id"])
            print(r.status_code,r.text)
def cleanIoTAgent_Service(setting):
    IOTA=setting["iotagent_setting"]["IOT_AGENT"]
    fiware_service=setting["iotagent_setting"]["fiware-service"]
    fiware_servicepath="/"
    header={'fiware-service': fiware_service,'fiware-servicepath': fiware_servicepath}
    r=requests.get(IOTA+"/iot/services",headers=header).json()
    services=r["services"]
    for server in services:
        print("remove server:",server["_id"])
        resource=server["resource"]
        apikey=server["apikey"]
        r=requests.delete(IOTA+"/iot/services/?resource="+resource+"&apikey="+apikey,headers=header)
        print(r.status_code,r.text)
def cleanDevices(setting,device_info=None):
    IOTA=setting["iotagent_setting"]["IOT_AGENT"]
    ORION=setting["system_setting"]["ORION"]
    if device_info!=None:
        pass
    else:    
        fiware_service=setting["iotagent_setting"]["fiware-service"]
        fiware_servicepath="/"
        header={'fiware-service': fiware_service,'fiware-servicepath': fiware_servicepath}
        r=requests.get(IOTA+"/iot/devices",headers=header).json()
        r=r["devices"]
        for device in r:
            device_id=device["device_id"]
            entity_name=device["entity_name"]
            print("Remove device on iot-agent:" ,device_id)
            r=requests.delete(IOTA+"/iot/devices/"+device_id,headers=header)
            print(r.status_code)
            print("Remove device on oriont:" ,entity_name)
            r=requests.delete(ORION+"/v2/entities/"+entity_name,headers=header)
            print(r.status_code)
        
def cleanIoTAgent_Supscription(setting):
    ORION=setting["system_setting"]["ORION"]
    fiware_service=setting["iotagent_setting"]["fiware-service"]
    fiware_servicepath="/"
    header={'fiware-service': fiware_service,'fiware-servicepath': fiware_servicepath}
    r=requests.get(ORION+"/v2/subscriptions",headers=header)
    for subscription in r.json():
        print("Remove subscription: ",subscription["id"])
        r=requests.delete(ORION+"/v2/subscriptions/"+subscription["id"],headers=header)
        print(r.status_code,r.text)
def cleanIoTAgent_Agent(setting):
    __PATH__=os.path.dirname(os.path.abspath(__file__))
    fiware_service=setting["iotagent_setting"]["fiware-service"]
    print("Remove IoT Agent and any sensor under this iot agent include HTM model setting.")
    shutil.rmtree(__PATH__+"/../Data/IoT/"+fiware_service)
    
    
def cleanCratedb_Devices(setting,entity_info):
    print("Clean device records on Crate DB : ",entity_info)
    IOTA=setting["iotagent_setting"]["IOT_AGENT"]
    fiware_service=setting["iotagent_setting"]["fiware-service"]
    fiware_servicepath="/"
    header={'fiware-service': fiware_service,'fiware-servicepath': fiware_servicepath}
    r=requests.get(IOTA+"/iot/devices",headers=header).json()
    r=r["devices"]
    for device in r:
        if device["entity_name"]!=entity_info:
            continue
        static_attributes=device["static_attributes"]
        et_type="sensor"
    header={'Content-Type': 'application/json'}
    sql='{"stmt":"DELETE FROM mt'+fiware_service+'.et'+et_type+' WHERE entity_id = \''+entity_info+'\'"}'
    r=requests.get("http://fiware-cratedb:4200/_sql",headers=header,data=sql)
    print(r.status_code,r.text)
        
    
def cleanCratedb_Table(setting):
    __PATH__=os.path.dirname(os.path.abspath(__file__))
    IOTA=setting["iotagent_setting"]["IOT_AGENT"]
    fiware_service=setting["iotagent_setting"]["fiware-service"]
    dir_l=os.listdir(__PATH__+"/../Data/IoT/"+fiware_service).remove("iotagent-setting.json")
    fiware_service=setting["iotagent_setting"]["fiware-service"]
    fiware_servicepath="/"
    header={'fiware-service': fiware_service,'fiware-servicepath': fiware_servicepath}
    r=requests.get(IOTA+"/iot/devices",headers=header).json()
    r=r["devices"]
    for device in r:
        entity_name=device["entity_name"]
        cleanCratedb_Devices(setting,entity_info=entity_name)
    
    header={'Content-Type': 'application/json'}
    print("Drop table with schema ",fiware_service," and table name etsensor")
    sql='{"stmt":"DROP TABLE IF EXISTS mt'+fiware_service+'.etsensor"}'
    r=requests.get("http://fiware-cratedb:4200/_sql",headers=header,data=sql)
    print(r.status_code,r.text)
    
    

def cleanAll():
    __PATH__=os.path.dirname(os.path.abspath(__file__))
    with open(__PATH__+"/../Data/global-setting.json","r") as f:
        setting=json.load(f)
    cleanFiware(setting)
    PATH=__PATH__+"/../Data/IoT/"
    dir_l=os.listdir(PATH)
    for d in dir_l:
        with open(PATH+d+"/iotagent-setting.json","r") as f:
            iota_setting=json.load(f)
            iota_setting.update(setting)
            iota_setting["iotagent_setting"]["fiware-service"]=d
            cleanCratedb_Table(iota_setting)
            cleanDevices(iota_setting)
            cleanIoTAgent_Service(iota_setting)            
            cleanIoTAgent_Supscription(iota_setting)
            cleanIoTAgent_Agent(iota_setting)
    print("Remove global-.json")
    os.remove(__PATH__+"/../Data/global-setting.json")
    print("Remove IoT folder")
    shutil.rmtree(__PATH__+"/../Data/IoT")
    print("Remove Data folder")
    shutil.rmtree(__PATH__+"/../Data")
    print("Clean up done.")
if __name__=="__main__":
    cleanAll()
    
            