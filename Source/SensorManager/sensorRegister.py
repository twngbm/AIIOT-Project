import json
import requests
import sys
import re
import os
from os import listdir
import logging
from pathlib import Path


class Device():
    def __init__(self, timezone):
        self.__PATH__ = os.path.dirname(os.path.abspath(__file__))
        self.TZ = timezone

    def sensorCheck(self, setting):
        sensor_info = setting["sensor_info"]
        must_list = [
            "deviceID",
            "timeResolution",
            "targetTime",
            "targetModel",
            "savePeriod",
            "sensorName",
            "fieldName",
            "retrainPeriod",
            "dataType",
            "sensorType",
            "unit",
            "dummy",
            "measurement"]
        lost_list = []
        for attr in must_list:
            if attr not in sensor_info:
                lost_list.append(attr)
        if lost_list != []:
            return lost_list

        else:
            return 0

    def sensorRegister(self, Sensor_info):
        ret = self.sensorCheck(Sensor_info)
        if type(ret) == list:
            return 422, "{'Status':'Missing Sensor Information "+str(ret)+"'}"

        try:
            with open(self.__PATH__+"/../Data/global-setting.json", "r") as f:
                globalSetting = json.load(f)
                ORION = globalSetting["system_setting"]["ORION"]
        except:
            return 404, "{'Status':'Initial FIWARE First'}"

        fiware_service = "iota"
        fiware_servicepath = "/"
        iotagent = Sensor_info["agent_info"]["iotagent"]
        serviceGroup = Sensor_info["agent_info"]["service_group"]
        try:
            with open(self.__PATH__+"/../Data/iotagent-setting.json", "r") as iotaf:
                iota_setting = json.load(iotaf)["iotagent_setting"]
            for iota in iota_setting:
                if iota["Iot-Agent-Url"] == iotagent:
                    found = True
                    IOTA = iotagent
                    iota_setting = iota
                    break
            if not found:
                return 404, "{'Status':'No Iot Agent At "+str(iotagent)+" Installed.'}"

        except:
            return 404, "{'Status':'No Iot Agent Installed.'}"

        if not os.path.isdir(self.__PATH__+"/../Data/IoT/"+serviceGroup):
            return 422, "{'Status':'Create Service Group Named"+serviceGroup+" First'"

        try:
            timezone = requests.get(
                ORION+"/v2/entities?type=House&options=keyValues").json()[0]["timezone"]
        except:
            timezone = self.TZ

        dummy = Sensor_info["sensor_info"]["dummy"]
        unit = Sensor_info["sensor_info"]["unit"]
        data_type = Sensor_info["sensor_info"]["dataType"]
        for i in range(1000):
            index = str(i).zfill(4)
            deviceName = Sensor_info["sensor_info"]["deviceID"]
            device_id = deviceName+"_"+index
            if os.path.isdir(self.__PATH__+"/../Data/IoT/"+serviceGroup+"/"+device_id):
                continue
            else:
                break

        entity_name = "urn:"+serviceGroup+":" + \
            Sensor_info["sensor_info"]["sensorType"]+":"+device_id
        entity_type = "Sensor"
        sensor_name = Sensor_info["sensor_info"]["sensorName"]
        field_name = Sensor_info["sensor_info"]["fieldName"]
        time_resolution = Sensor_info["sensor_info"]["timeResolution"]
        target_time = Sensor_info["sensor_info"]["targetTime"]
        target_model = Sensor_info["sensor_info"]["targetModel"]
        save_period = Sensor_info["sensor_info"]["savePeriod"]
        retrain_period = Sensor_info["sensor_info"]["retrainPeriod"]
        sensor_type = Sensor_info["sensor_info"]["sensorType"]
        measurement = Sensor_info["sensor_info"]["measurement"]
        try:
            refRoomID = Sensor_info["sensor_info"]["refRoom"]
        except:
            refRoomID = None
        attribute = [{"object_id": measurement, "name": "count", "type": data_type},
                     {"object_id": "TS", "name": "timestamp", "type": "DateTime"}]

        static_attributes = [{"name": "sensorName", "type": "Text", "value": sensor_name},
                             {"name": "fieldName", "type": "Text",
                                 "value": field_name},
                             {"name": "refRoom", "type": "Relationship",
                              "value": refRoomID},
                             {"name": "timeResolution", "type": "Integer",
                              "value": time_resolution},
                             {"name": "targetTime", "type": "Integer",
                              "value": target_time},
                             {"name": "targetModel", "type": "Text",
                              "value": target_model},
                             {"name": "savePeriod", "type": "Integer",
                              "value": save_period},
                             {"name": "retrainPeriod", "type": "Integer",
                              "value": retrain_period},
                             {"name": "sensorType", "type": "Text",
                                 "value": sensor_type},
                             {"name": "unit", "type": "Text", "value": unit},
                             {"name": "predictionValue",
                              "type": data_type, "value": "None"},
                             {"name": "anomalyScore",
                                 "type": "Float", "value": "None"},
                             {"name": "anomalyLikehood",
                              "type": "Float", "value": "None"},
                             {"name": "LogAnomalyLikehood",
                              "type": "Float", "value": "None"},
                             {"name": "dataType",
                              "type": "Text", "value": data_type},
                             {"name": "Anomaly", "type": "Bool", "value": "False"}]
        if dummy:
            static_attributes.append(
                {"name": "isDummy", "type": "Bool", "value": "True"})
        else:
            static_attributes.append(
                {"name": "isDummy", "type": "Bool", "value": "False"})
        data = {"devices": [{
            "device_id":   device_id,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "timezone":    timezone,
            "attributes": attribute,
            "static_attributes": static_attributes
        }]}
        header = {"Content-Type": "application/json",
                  "fiware-service": fiware_service, "fiware-servicepath": fiware_servicepath}
        r = requests.post(IOTA+"/iot/devices", headers=header,
                          data=json.dumps(data))
        if r.status_code == 201:
            os.mkdir(self.__PATH__+"/../Data/IoT/"+serviceGroup+"/"+device_id)
            static_attributes_output = {}
            for attr in static_attributes:
                static_attributes_output[attr["name"]] = attr["value"]
            with open(self.__PATH__+"/../Data/IoT/"+serviceGroup+"/"+device_id+"/device.cfg", "w+") as f:
                json.dump({"iotagent_config": iota_setting,
                           "static_attributes": static_attributes_output, "entityID": entity_name}, f)
            with open(self.__PATH__+"/../Data/IoT/"+serviceGroup+"/"+device_id+"/localdata.tmp", "w+") as f:
                f.write("value,timestamp\n"+data_type+",datetime\n ,T\n")
                f.close()
            with open(self.__PATH__+"/../Data/IoT/"+serviceGroup+"/"+device_id+"/counter.tmp", "w+") as f:
                f.write("0")
                f.close()
            Path(self.__PATH__+"/../Data/IoT/"+serviceGroup +
                 "/"+device_id+"/localnewest.tmp").touch()
            Path(self.__PATH__+"/../Data/IoT/"+serviceGroup +
                 "/"+device_id+"/preLearning").touch()
        return r.status_code, r.text
