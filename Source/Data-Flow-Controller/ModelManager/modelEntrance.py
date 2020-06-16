import json
import os
import socket
import threading
from ModelManager import commonIF
import logging
import datetime
import multiprocessing
__GLOBAL_THREADHOLD__ = 0.7


def init(PORT):
    ServerSocket = socket.socket()
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ServerSocket.bind(("localhost", PORT))
    ServerSocket.listen(10)
    logging.info("Init Socket")
    return ServerSocket


def dataDecoder(data: bytes):

    try:
        data = data.decode("utf-8")
        data = json.loads(data)
        if data["dType"]=="DATA":
            data = commonIF.SensorData(data)
        elif data["dType"]=="COMMAND":
            data = commonIF.ModelCommand(data)

    except:
        data = None
    if data==None:
        raise TypeError
    return data


def threaded_client(connection, __GLOBAL_THREADHOLD__):
    logging.info("Model Entrance Sub-Process {pid} Start...\n".format(pid=os.getpid()))
    msg = connection.recv(65536)
    connection.close()
    fulldata = dataDecoder(msg)
    if fulldata.dType=="DATA":
        logging.info("Get Data with Timestamp: "+str(fulldata.data.timestamp) +
                     " and value: "+str(fulldata.data.value))
    else:
        logging.info("Get Command at Times: "+str(datetime.datetime.now().time()) +
                     " and action: "+str(fulldata.data.action))
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

    commonIF.modelHandler(fulldata, __GLOBAL_THREADHOLD__)
    logging.info("Model Entrance Sub-Process {pid} End...\n".format(pid=os.getpid()))


# if __name__=="__main__":
def modelEntrance(PORT,level=logging.INFO):
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Module Entrance with PID:{pid}\n".format(pid=os.getpid()))
    ServerSocket = init(PORT)
    while True:
        Client, address = ServerSocket.accept()
        process = multiprocessing.Process(
            None, target=threaded_client, args=(Client, __GLOBAL_THREADHOLD__,), daemon=True
        )
        process.start()
    ServerSocket.close()
