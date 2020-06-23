import json
import os
from ModelManager import commonIF
import logging
import datetime


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
