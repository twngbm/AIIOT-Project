import json
from crate import client
import datetime
import os
import time

__PATH__ = os.path.dirname(os.path.abspath(__file__))


def Default_Nearest_AND(Data, timewidth):
    service_group = Data.data.service_group
    timestamp = Data.data.timestamp

    with open(__PATH__+"/../Data/global-setting.json", "r") as f:
        global_setting = json.load(f)
    __CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()
    EndTime = (timestamp-datetime.datetime(1970, 1, 1)).total_seconds()*1000
    StartTime = timestamp-datetime.timedelta(seconds=timewidth)
    StartTime = (StartTime-datetime.datetime(1970, 1, 1)).total_seconds()*1000

    devices = os.listdir(__PATH__+"/../Data/IoT/"+service_group)
    devices.remove("subscription.json")
    for device in devices:
        with open(__PATH__+"/../Data/IoT/"+service_group+"/"+device+"/device.cfg", "r") as f:
            deviceDetail = json.load(f)
        entity_id = deviceDetail["entityID"]
        output = {}
        retry = 0
        while retry < 10:
            cursor.execute(
                "SELECT * FROM mtiota.etsensor \
            WHERE time_index > "+str(int(StartTime)) +
                " AND time_index <= "+str(int(EndTime)) +
                " AND entity_id='"+entity_id+"'\
            ORDER BY time_index"
            )
            header = [column[0] for column in cursor.description]
            result = cursor.fetchall()
            if result == []:
                break
            result = result[-1]
            output = {x: y for x, y in zip(header, result)}
            if output["anomalyflag"] != None:
                break
            else:
                time.sleep(1)
                retry += 1

        if output == {}:
            continue
        if output["anomalyflag"] != True:
            return False
    return True
