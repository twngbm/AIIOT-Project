import json
import os
import socket
import threading
from ModelManager import commonIF
import logging
import datetime
import multiprocessing
import signal




"""
def childDead(signum, frame):
    try:
        while True:
            cpid, status = os.waitpid(-1, os.WNOHANG)
            if cpid == 0:
                break
            exitcode = status >> 8
            logging.info('child process %s exit with exitcode %s',
                         cpid, exitcode)
    except OSError as e:
        pass


def init(PORT):
    ServerSocket = socket.socket()
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ServerSocket.bind(("localhost", PORT))
    ServerSocket.listen(10)
    logging.info("Init Socket")
    return ServerSocket
"""

def dataDecoder(data):

    try:
        if data["dType"] == "DATA":
            data = commonIF.SensorData(data)
        elif data["dType"] == "COMMAND":
            data = commonIF.ModelCommand(data)

    except:
        data = None
    if data == None:
        raise TypeError
    return data


def modelPortal(msg, __GLOBAL_THREADHOLD__):
    """
    logging.info(
        "Model Entrance Sub-Process {pid} Start...\n".format(pid=os.getpid()))
    msg = connection.recv(65536)
    connection.close()
    
    fulldata = dataDecoder(msg)
    """
    
    fulldata = dataDecoder(msg)
    if fulldata.dType == "DATA":
        logging.info("Get Data with Timestamp: "+str(fulldata.data.timestamp) +
                     " and value: "+str(fulldata.data.value))
    else:
        logging.info("Get Command at Times: "+str(datetime.datetime.now().time()) +
                     " and action: "+str(fulldata.data.action))

    if fulldata == None:
        raise KeyError

    pid=os.fork()
    if pid==0:
        logging.info(
            "-------MDET:Process {pid} Start-------".format(pid=os.getpid()))
        commonIF.modelHandler(fulldata, __GLOBAL_THREADHOLD__)
        os._exit(0)
    else:
        return 0

"""
def modelEntrance(PORT, level=logging.INFO):
    logging.basicConfig(level=logging.INFO)
    logging.info(
        "Starting Module Entrance with PID:{pid}\n".format(pid=os.getpid()))
    ServerSocket = init(PORT)
    signal.signal(signal.SIGCHLD, childDead)
    while True:
        Client, address = ServerSocket.accept()
        process = multiprocessing.Process(
            None, target=modelPortal, args=(Client, __GLOBAL_THREADHOLD__,), daemon=True
        )
        process.start()
    ServerSocket.close()
"""