import json
import sys
import requests
import pprint
import os
def makeHouse(ORION,timezone,address,house_name):
    #no House entity inside FIWARE, create_one
    houseUID="urn:ngsi-ld:House:001"
    streetAddress=address["streetAddress"]
    addressRegion=address["addressRegion"]
    Country=address["Country"]
    data={
        "id": houseUID,
        "type": "House",
        "address": {
            "type": "PostalAddress",
            "value": {
                "streetAddress":streetAddress,
                "addressRegion":addressRegion,
                "Country":Country
            }
        },
        "name": {
            "type": "Text",
            "value": house_name
        },
        "timezone":{
            "type":"Text",
            "value":timezone
        }
    }
    header={"Content-Type": "application/json"}
    r=requests.post(ORION+"/v2/entities",headers=header,data=json.dumps(data))
    if r.status_code==422:
        return -1
    return houseUID

    
def makeFloor(ORION,house_id,floor):
    header={"Content-Type": "application/json"}
    floor_id={}
    for count,f in enumerate(floor):
        floor_id[f]="urn:ngsi-ld:Floor:"+str(count+1)
        data={
            "id":"urn:ngsi-ld:Floor:"+str(count+1),
            "type":"Floor",
            "refHouse":{
                "type":"Relationship",
                "value":"urn:ngsi-ld:House:001"
            },
            "floor":{
                "type":"Text",
                "value":f
            }
        }
        r=requests.post(ORION+"/v2/entities",headers=header,data=json.dumps(data))
    return floor_id
def makeRoom(ORION,floor_id,room):
    header={"Content-Type": "application/json"}
    room_id={}
    for fid in floor_id:
        room_id[fid]=[]
    for count,pair in enumerate(room):
        room_name=list(pair)[0]
        floorUID=floor_id[pair[room_name]]
        room_id[pair[room_name]].append({room_name:"urn:ngsi-ld:Room:"+str(count+1)})
        data={
            "id":"urn:ngsi-ld:Room:"+str(count+1),
            "type":"Room",
            "refFloor":{
                "type":"Relationship",
                "value":floorUID
            },
            "roomName":{
                "type":"Text",
                "value":room_name
            }
        }
        r=requests.post(ORION+"/v2/entities",headers=header,data=json.dumps(data))
    return room_id
def writeSetback(setting,house_id,floor_id,room_id):
    system_setting={}
    system_setting["system_setting"]=setting["system_setting"]
    os.mkdir("Data")
    with open("./Data/global-setting-entityID.json","w+") as opfile:
        json.dump(system_setting,opfile)

def initFiware(setting):
    ORION=setting["system_setting"]["ORION"]
    QUANTUMLEAP=setting["system_setting"]["QUANTUMLEAP"]
    timezone=setting["fiware_setting"]["timezone"]
    address=setting["fiware_setting"]["address"]
    house_name=setting["fiware_setting"]["houseName"]
    floor=setting["fiware_setting"]["Floor"]
    room=setting["fiware_setting"]["Room"]
    house_id=makeHouse(ORION,timezone,address,house_name)
    if house_id==-1:
        return -1
    floor_id=makeFloor(ORION,house_id,floor)
    room_id=makeRoom(ORION,floor_id,room)
    writeSetback(setting,house_id,floor_id,room_id)
    return 0

    

