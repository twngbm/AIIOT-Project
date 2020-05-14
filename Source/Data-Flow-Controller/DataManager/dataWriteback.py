import requests
import json
import os
from crate import client
import time
__PATH__=os.path.dirname(os.path.abspath(__file__))


def writeToCratedb(
    fiware_service:str,
    entity_id:str,
    timestamp:str,
    predictionValue:str,
    anomalyScore:str,
    anomalyLikeliHood:str,
    logAnomalyLikeliHood:str,
    Anomaly:str
):
    with open(__PATH__+"/../Data/global-setting.json","r") as f:
        global_setting=json.load(f)
    __CRATEDB__=global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()
    timestamp=timestamp.split(" ")
    timestamp=timestamp[0]+"T"+timestamp[1]
    cursor.execute("UPDATE mt" + fiware_service + ".etsensor\
                    SET anomaly = " + Anomaly +
                    ",anomalylikehood = " + anomalyLikeliHood +
                    ",anomalyscore = " + anomalyScore +
                    ",loganomalylikehood = " + logAnomalyLikeliHood +
                    ",predictionvalue = " + predictionValue +
                    "WHERE entity_id = '"+entity_id+"' \
                    AND time_index=DATE_TRUNC ('second','"+timestamp+"')")
