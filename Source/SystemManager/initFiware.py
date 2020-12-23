import json
import sys
import requests
import os


def createEntity(setting):
    __PATH__ = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(__PATH__+"/../Data/global-setting.json", "r") as f:
            globalSetting = json.load(f)
            ORION = globalSetting["system_setting"]["ORION"]
    except:
        return 404, "{'Status':'Can't Find Context Broker'}"

    header = {"Content-Type": "application/json"}
    try:
        entityType = setting["type"]
        entityID = setting["id"].replace(" ", "_")
    except:
        return 400, "{'Status':'Wrong Format'}"

    try:
        metadata = setting["metadata"]
    except:
        metadata = []
    data = {}
    data["type"] = entityType
    dID = "urn:ngsi-ld:"+entityType+":"+entityID
    for meta in metadata:
        value = metadata[meta]
        if meta == "address":
            dType = "PostalAddress"
        elif meta == "relationship":
            dType = "Relationship"
            value = metadata[meta]
        else:
            dType = "Text"
        data[meta] = {"type": dType, "value": value}
    data["id"] = dID
    r = requests.post(ORION+"/v2/entities", headers=header,
                      data=json.dumps(data))
    return r.status_code, r.text
