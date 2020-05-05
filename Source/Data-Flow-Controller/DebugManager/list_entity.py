import requests
import json
import pprint
import os

Fake=False
__PTAH__=os.path.dirname(os.path.abspath(__file__))
setting_path="../Data/global-setting-entityID.json"
PATH="../Data/IoT/"
if not os.path.isfile("../Data/global-setting-entityID.json"):
    print("********************************************************")
    print("WARNING:System havn't been initialliz,use Web's setting!")
    print("********************************************************")
    setting_path="../../Web/Data/global-setting.json"
    PATH="../../Web/Data/IoT/"
    Fake=True

def show_(PATH,Type=None,Header=None,Iota=False,Raw=False):
    if Type!=None:
        r=requests.get(PATH,params={"type":Type},headers=Header)
    else:
        r=requests.get(PATH,headers=Header)
    if Raw:
        return r
    r=r.json()
    if Iota:
        count=r['count']
        print("Count on this IoT Agent:",count)
        try:
            r=r['services']
        except:
            r=r['devices']
    for item in r:
        print("")
        pprint.pprint(item,compact=True)


with open(setting_path,"r") as f:
    setting=json.load(f)
    ORION=setting["system_setting"]["ORION"]
    QUANTUMLEAP=setting["system_setting"]["QUANTUMLEAP"]

ORION_entity=ORION+"/v2/entities"
ORION_subscription=ORION+"/v2/subscriptions"

dir_l=os.listdir(PATH)


print("Show system setting:")
print("Is ./Data/IoT exist?:")
print(os.path.isdir("../Data/IoT"))
print("Is ./Data exist?:")
print(os.path.isdir("../Data"))
if Fake:
    print("Current IoT Agent ready to install are:")
    print(dir_l)
else:
    print("Current installed IoT Agent are:")
    print(dir_l)
print("Orion's address is: ",ORION)
print("Quantumleap's address is: " ,QUANTUMLEAP)

print("")
print("")
print("Print entity on Orion Context Broker:")

print("")
print("Print entities with type=House")
show_(ORION_entity,"House")
print("")
print("Print entities with type=Floor")
show_(ORION_entity,"Floor")
print("")
print("Print entities with type=Room")
show_(ORION_entity,"Room")
print("")
print("Print subscription on Orion Context Broker:")

for d in dir_l:
    if d[0]==".":
        continue
    print("Start list current installed iot-agent with it's services.")
    print("")
    with open(PATH+d+"/iotagent-setting.json","r") as f:
        iota_setting=json.load(f)
        IOT_AGENT=iota_setting["iotagent_setting"]["IOT_AGENT"]
        IOT_AGENT_devices=IOT_AGENT+"/iot/devices"
        IOT_AGENT_services=IOT_AGENT+"/iot/services"
        current_iota=d
    print("Current Iot Agent is : ",current_iota)
    print("")
    print("Iotagent address is:",IOT_AGENT)
    print("Subscription on orion to quantumleap and aiot-dfc response for this IoT agent is:")
    print("")
    header={'fiware-service':current_iota,"fiware-servicepath":"/"}
    show_(ORION_subscription,Header=header)
    print("")
    print("Service on this IoT Agent is :")
    show_(IOT_AGENT_services,Header=header,Iota=True)
    print("")
    print("Devices on this IoT Agent are :")
    show_(IOT_AGENT_devices,Header=header,Iota=True)

