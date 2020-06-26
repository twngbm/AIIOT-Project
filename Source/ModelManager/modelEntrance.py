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
        logging.info("DATA T: "+str(fulldata.data.timestamp) +
                     ",V: "+str(fulldata.data.value))
    else:
        logging.info("COMMAND T: "+str(datetime.datetime.now().time()) +
                     ",V: "+str(fulldata.data.action))

    if fulldata == None:
        raise KeyError

    pid=os.fork()
    if pid==0:
        logging.info('\n|---------------'+str(os.getpid()) +
                     ' START---------------')
        commonIF.modelHandler(fulldata, __GLOBAL_THREADHOLD__)
        os._exit(0)
    else:
        return 0
