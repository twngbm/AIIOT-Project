import json
import os
import socket
import threading
from ModelManager import commonIF
import logging
import multiprocessing
__GLOBAL_THREADHOLD__=0.7

def init():
    ServerSocket = socket.socket()
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ServerSocket.bind(("localhost", 5000))
    ServerSocket.listen(10)
    logging.info("Init Socket")
    return ServerSocket


def dataDecoder(data: bytes):

    try:
        data = data.decode("utf-8")
        data = json.loads(data)
        data=commonIF.SensorData(data)
    except:
        data = None
    
    return data


def threaded_client(connection,__GLOBAL_THREADHOLD__):
    msg = connection.recv(65536)
    connection.close()
    fulldata = dataDecoder(msg)
    logging.info("Get Data with Timestamp: "+str(fulldata.data.timestamp)+" and value: "+str(fulldata.data.value))
    """
    fulldata=
    {'data': 
        {'value': '101', 
        'dataType': 'Float',
        'timestamp': '2020-05-08 00:13:12', 
        'entity_id': 'urn:ngsi-ld:Electricity:02', 
        'device_id': 'Sensor02', 
        'fiware_service': 'iota001'}, 
    'static_attributes': 
        {'sensorName': 'Basement Temp', 
        'fieldName': 'Power consumption', 
        'refRoom': 'urn:ngsi-ld:Room:1', 
        'timeResolution': '30', 
        'targetTime': '300', 
        'targetModel': 'HTM', 
        'sensorType': 'Electricity', 
        'unit': 'Celsius', 
        'predictionValue': 'None', 
        'anomalyScore': 'None', 
        'anomalyLikehood': 'None', 
        'isDummy': 'True'}}
    """
    if fulldata == None:
        return -1
    
    commonIF.modelHandler(fulldata,__GLOBAL_THREADHOLD__)


#if __name__=="__main__":
def modelEntrance(level=logging.INFO):
    logging.basicConfig(level=logging.INFO)
    ServerSocket = init()
    while True:
        Client, address = ServerSocket.accept()
        process = multiprocessing.Process(
            None, target=threaded_client, args=(Client,__GLOBAL_THREADHOLD__,), daemon=True
        )
        process.start()
    ServerSocket.close()
