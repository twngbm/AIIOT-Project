import os
import json
def writeSetback(setting):
    __PATH__ = os.path.dirname(os.path.abspath(__file__))
    
    try:
        os.mkdir(__PATH__+"/../Data")
        os.mkdir(__PATH__+"/../Data/IoT/")
    except:
        return 409,"{'Status':'Already Exists'}"
    try:
        setting["system_setting"]["ORION"]
        setting["system_setting"]["QUANTUMLEAP"]
        setting["system_setting"]["CRATEDB"]
    except:
        return 422,"{'Status':'Wrong Format'}"
    with open(__PATH__+"/../Data/global-setting.json", "w+") as opfile:
        json.dump(setting, opfile)
    return 201,"{'Status':'Create'}"
    
