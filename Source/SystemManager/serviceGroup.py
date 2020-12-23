import os
import json
import logging
from pathlib import Path


def createServiceGroup(data):
    __PATH__ = os.path.dirname(os.path.abspath(__file__))
    for sg in data:
        try:
            sgName = sg["Name"]
        except:
            return 422, "Missing Attritubes Name"

        try:
            os.mkdir(__PATH__+"/../Data/IoT/"+sgName)
            Path(__PATH__+"/../Data/IoT/"+sgName+"/subscription.json").touch()
        except:
            return 422, "Fail at Create Service Group "+str(sg)+", Service Group Already Exist."

    return 201, "Service Group Create Success"
