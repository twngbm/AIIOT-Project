import json
import requests
import sys
import re
import pprint
import os
from os import listdir
def sensorRegister(setting):
    
    ORION=setting["system_setting"]["ORION"]
    IOTA=setting["iotagent_setting"]["IOT_AGENT"]
    timezone=requests.get(ORION+"/v2/entities?type=House&options=keyValues").json()[0]["timezone"]
    fiware_service=setting["iotagent_setting"]["fiware-service"]
    fiware_servicepath="/"
    dummy=setting["sensor_info"]["dummy"]
    unit=setting["sensor_info"]["unit"]
    device_id=setting["sensor_info"]["deviceID"]
    entity_name="urn:ngsi-ld:"+setting["sensor_info"]["sensorType"]+":"+device_id[6:]
    entity_type="Sensor"
    sensor_name=setting["sensor_info"]["sensorName"]
    field_name=setting["sensor_info"]["fieldName"]
    time_resolution=setting["sensor_info"]["timeResolution"]
    sensor_type=setting["sensor_info"]["sensorType"]
    measurement=setting["sensor_info"]["measurement"]
    refRoomID=setting["sensor_info"]["refRoom"]
    attribute=[{"object_id": measurement, "name": "count", "type": "Float"},
               {"object_id":"TS", "name": "timestamp", "type":"DateTime"}]
    
    print("Start create device on ",IOTA," with device_id: ",device_id)
    
    
    static_attributes=[{"name":"sensorName", "type": "Text", "value": sensor_name},
                       {"name":"fieldName", "type": "Text", "value": field_name},
                       {"name":"refRoom", "type": "Relationship", "value": refRoomID},
                       {"name":"timeResolution", "type": "Integer", "value": time_resolution},
                       {"name":"sensorType", "type": "Text", "value": sensor_type},   
                       {"name":"unit", "type": "Text", "value": unit},
                       {"name":"predictionValue", "type": "Float", "value": "None"},
                       {"name":"anomalyScore", "type": "Float", "value": "None"},
                       {"name":"anomalyLikehood", "type": "Float", "value": "None"}]
    
    if dummy:
        static_attributes.append({"name":"isDummy", "type": "Bool", "value": "True"})
    else:
        static_attributes.append({"name":"isDummy", "type": "Bool", "value": "False"})
    data={"devices":[{
                    "device_id":   device_id,
                    "entity_name": entity_name,
                    "entity_type": entity_type,
                    "timezone":    timezone,
                    "attributes": attribute,
                    "static_attributes": static_attributes 
          }]}
    header={"Content-Type": "application/json","fiware-service":fiware_service,"fiware-servicepath":fiware_servicepath}
    r=requests.post(IOTA+"/iot/devices",headers=header,data=json.dumps(data))
    
    print(r.status_code,r.text)
    if r.status_code==201:
        os.mkdir("Data/IoT/"+fiware_service+"/"+device_id)
        with open("./Data/IoT/"+fiware_service+"/"+device_id+"/localdata.tmp","w+") as f:
            f.write("0")
            f.close()
            
            
            
    return r.status_code
    


