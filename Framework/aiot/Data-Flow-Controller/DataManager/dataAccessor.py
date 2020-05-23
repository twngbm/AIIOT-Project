import json
import os
from crate import client
import time
import logging
import datetime
import csv
__PATH__ = os.path.dirname(os.path.abspath(__file__))


def trainoutputWriteback(path: str, Data, __GLOBAL_THREADHOLD__: float):
    with open(path, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        fiware_service = Data.data.fiware_service
        entity_id = Data.data.entityID
        for row in reader:
            timestamp = row[header.index("timestamp")]
            predictionValue = row[header.index("prediction")]
            anomalyScore = row[header.index("anomaly_score")]
            anomalyLikelihood = row[header.index("anomaly_likelihood")]
            logAnomalyLikelihood = row[header.index("Log_anomaly_likelihood")]
            if float(logAnomalyLikelihood) > __GLOBAL_THREADHOLD__:
                anomaly = "True"
            else:
                anomaly = "False"
            writeToCratedb(
                fiware_service,
                entity_id,
                timestamp,
                predictionValue,
                anomalyScore,
                anomalyLikelihood,
                logAnomalyLikelihood,
                anomaly,
            )


def resultWriteback(timestamp: datetime, value, predictionValue, anomaly: bool, metadata: dict, Data):

    anomalyScore = metadata["anomalyScore"] if "anomalyScore" in metadata else None
    anomalyLikelihood = metadata["anomalyLikelihood"] if "anomalyLikelihood" in metadata else None
    logAnomalyLikelihood = metadata["logAnomalyLikelihood"] if "logAnomalyLikelihood" in metadata else None
    writeToCratedb(
        Data.data.fiware_service,
        Data.data.entityID,
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        str(predictionValue),
        str(anomalyScore),
        str(anomalyLikelihood),
        str(logAnomalyLikelihood),
        str(anomaly)
    )


def writeToCratedb(
    fiware_service: str,
    entity_id: str,
    timestamp: str,
    predictionValue: str,
    anomalyScore: str,
    anomalyLikeliHood: str,
    logAnomalyLikeliHood: str,
    Anomaly: str
):
    with open(__PATH__+"/../Data/global-setting.json", "r") as f:
        global_setting = json.load(f)
    __CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()
    timestamp = timestamp.split(" ")
    timestamp = timestamp[0]+"T"+timestamp[1]
    while True:
        cursor.execute(
            "SELECT * FROM mt" + fiware_service +
            ".etsensor WHERE time_index = DATE_TRUNC ('second','" +
            timestamp+"') AND entity_id='"+entity_id+"'"
        )
        result = cursor.fetchall()
        if len(result) == 0:
            logging.warning("CrateDB Entity Cannot Found, Retry...")
            time.sleep(1)
        else:
            break
    cursor.execute("UPDATE mt" + fiware_service + ".etsensor\
                    SET anomaly = " + Anomaly +
                   ",anomalylikehood = " + anomalyLikeliHood +
                   ",anomalyscore = " + anomalyScore +
                   ",loganomalylikehood = " + logAnomalyLikeliHood +
                   ",predictionvalue = " + predictionValue +
                   "WHERE entity_id = '"+entity_id+"' \
                    AND time_index=DATE_TRUNC ('second','"+timestamp+"')")


def queFromCratedbBack(fiware_service: str, entity_id: str, timestamp):
    with open(__PATH__+"/../Data/global-setting.json", "r") as f:
        global_setting = json.load(f)
    __CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()
    timestamp = (timestamp-datetime.datetime(1970, 1, 1)).total_seconds()*1000
    cursor.execute(
        "SELECT * FROM mt" + fiware_service + ".etsensor \
        WHERE time_index > "+str(int(timestamp)) +
        " AND entity_id='"+entity_id+"'\
        ORDER BY time_index"
    )
    header = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    output = [{header[i]:x[i] for i in range(len(header))} for x in result]
    return output


def queFromCratedbBound(fiware_service: str, entity_id: str, StartTime, EndTime):
    with open(__PATH__+"/../Data/global-setting.json", "r") as f:
        global_setting = json.load(f)
    __CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()
    StartTime = (StartTime-datetime.datetime(1970, 1, 1)).total_seconds()*1000
    EndTime = (EndTime-datetime.datetime(1970, 1, 1)).total_seconds()*1000
    cursor.execute(
        "SELECT * FROM mt" + fiware_service + ".etsensor \
        WHERE time_index > "+str(int(StartTime)) +
        " AND time_index < "+str(int(EndTime)) +
        " AND entity_id='"+entity_id+"'\
        ORDER BY time_index"
    )
    header = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    output = [{header[i]:x[i] for i in range(len(header))} for x in result]
    return output


def queFromCratedbNewest(fiware_service: str, entity_id: str, limit: int):
    with open(__PATH__+"/../Data/global-setting.json", "r") as f:
        global_setting = json.load(f)
    __CRATEDB__ = global_setting["system_setting"]["CRATEDB"]
    connection = client.connect(__CRATEDB__)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM mt" + fiware_service + ".etsensor \
        WHERE time_index > 0 AND entity_id='"+entity_id+"'\
        ORDER BY time_index DESC LIMIT "+str(limit)
    )
    header = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    output = [{header[i]:x[i] for i in range(len(header))} for x in result]
    return output[::-1]
