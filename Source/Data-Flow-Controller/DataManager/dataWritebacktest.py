import requests
import json
import os
from crate import client
import time

__PATH__ = os.path.dirname(os.path.abspath(__file__))

with open(__PATH__ + "/../Data/global-setting.json", "r") as f:
    global_setting = json.load(f)
__CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
connection = client.connect(__CRATEDB__)
cursor = connection.cursor()
cursor.execute(
    "SELECT * FROM mtiota001.etsensor WHERE time_index > DATE_TRUNC ('second','2010-07-02T00:00:00.00Z') AND entity_id='urn:ngsi-ld:Temperature:02'ORDER BY time_index"
)
while True:
    result=cursor.fetchone()
    if result!=None:
        print(result)
    else:
        break