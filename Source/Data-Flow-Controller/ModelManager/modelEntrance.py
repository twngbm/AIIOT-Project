import json
import os
import socket
import threading
import commonIF


def init():
    ServerSocket = socket.socket()
    ServerSocket.bind(("localhost", 5000))
    ServerSocket.listen(10)
    return ServerSocket


def dataDecoder(data: bytes):

    try:
        data = data.decode("utf-8")
        data = json.loads(data)
        data=commonIF.SensoeData(data)
    except:
        data = None
    
    return data


def threaded_client(connection):
    msg = connection.recv(65536)
    connection.close()
    fulldata = dataDecoder(msg)
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
    
    commonIF.dataProcess(fulldata)


if __name__ == "__main__":
    ServerSocket = init()
    while True:
        Client, address = ServerSocket.accept()
        thread = threading.Thread(
            None, target=threaded_client, args=(Client,), daemon=True
        )
        thread.start()
    ServerSocket.close()
