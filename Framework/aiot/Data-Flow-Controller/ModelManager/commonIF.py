# Stage1:Choose model
# 1. HTM
# 2. ...

# Stage2:Choose model operation
# 1. Prepare model (Prepare a model to be ready for setup and train)
# 2. Pretrain model (Setup model for traning)
# 3. Traing model (Train a model)
# 4. Online model (Make a trained model run forever)
# 5. Stop model
# 6. Save model
# 7. Use model (Select a running and trained model to make prediction)
# 8. Clean model

# Stage3:Wait model opreation finished, choose next model opreation or go to next Stage.

# Stage4:Save model prediction and/or exit.

# from modelRepo import *
# from DataManager import dataAccessor
# model=modelRepo["targetModel"]
# if model not EXIST:
#   model.Prepare()
# if model not TRAIN or RETRAIN INTERVAL:
#   model.Pretrain()
#   model.Train()
# if model not RUN or STOP:
#   model.Online()
# if SAVE INTERVAL:
#   model.Save()
# pred=model.Use()
#
# if pred is anomaly:
#   messageManger.send(warning)
#
# dataAccessor(pred)

import os
import json
import datetime
import importlib
import time
import csv
import sys
import inspect
from pathlib import Path
import logging
import shutil

current_dir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from DataManager import dataAccessor

class SensorCommand:
    def __init__(self, data: dict):
        self.dType = data["dType"]
        self.data = __COMMAND__(data)
        self.static_attributes = __STATIC_ATTRITUBES__(data)


class SensorData:
    def __init__(self, data: dict):
        self.dType = data["dType"]
        self.data = __DATA__(data)
        self.static_attributes = __STATIC_ATTRITUBES__(data)


class __DATA__:
    def __init__(self, data: dict):
        self.__data__ = data["data"]
        self.dataType = self.__data__["dataType"]
        if self.dataType == "float":
            self.value = float(self.__data__["value"])
        elif self.dataType == "int":
            self.value = int(self.__data__["value"])
        elif self.dataType == "bool":
            self.value = (
                True if self.__data__["value"] in [
                    "True", "true", "1"] else False
            )
        elif self.dataType == "string":
            self.value = self.__data__["value"]

        self.timestamp = datetime.datetime.strptime(
            self.__data__["timestamp"], "%Y-%m-%d %H:%M:%S"
        )  # Datetime object
        self.deviceID = self.__data__["device_id"]
        self.entityID = self.__data__["entity_id"]
        self.fiware_service = self.__data__["fiware_service"]


class __COMMAND__:
    def __init__(self, data: dict):
        self.__data__ = data["data"]
        self.action = self.__data__["value"]
        self.deviceID = self.__data__["device_id"]
        self.entityID = self.__data__["entity_id"]
        self.fiware_service = self.__data__["fiware_service"]
        self.metadata = self.__data__["metadata"]


class __STATIC_ATTRITUBES__:
    def __init__(self, data: dict):
        self.__static_attributes__ = data["static_attributes"]
        self.sensorName = self.__static_attributes__["sensorName"]
        self.fieldName = self.__static_attributes__["fieldName"]
        self.refRoom = self.__static_attributes__["refRoom"]
        self.timeResolution = float(
            self.__static_attributes__["timeResolution"])
        self.savePeriod = int(self.__static_attributes__["savePeriod"])
        self.targetTime = float(self.__static_attributes__["targetTime"])
        self.targetModel = self.__static_attributes__["targetModel"]
        self.sensorType = self.__static_attributes__["sensorType"]
        self.unit = self.__static_attributes__["unit"]
        self.dataType = self.__static_attributes__["dataType"]
        self.isDummy = (
            True
            if self.__static_attributes__["isDummy"] in ["True", "true", 1]
            else False
        )


def modelSelector(targetModel: str):
    try:
        modelModule = importlib.import_module(
            "ModelManager.modelRepo." + targetModel)
    except:
        raise ImportError

    return modelModule


def modelHandler(Data: SensorData, __GLOBAL_THREADHOLD__: float):
    trainFlag = False
    wakeFlag = False
    targetModel = Data.static_attributes.targetModel
    module = modelSelector(targetModel)
    Model = module.model(Data, __GLOBAL_THREADHOLD__)
    __SENSORDIR__ = (
        os.path.dirname(os.path.abspath(__file__))
        + "/../Data/IoT/"
        + Data.data.fiware_service
        + "/"
        + Data.data.deviceID
        + "/"
    )

    if Data.dType == "COMMAND":
        logging.info("Model Entrance Receive Command:{action}".format(
            action=Data.data.action))
        if Data.data.action == "Sleep":
            if Model.isOnline:
                Model.Sleep()
            return 0

        elif Data.data.action == "Remove":
            if Model.isOnline:
                Model.Sleep()
                time.sleep(1)
            if Model.isExist:
                Model.Remove()
                Path(__SENSORDIR__+"preLearning").touch()
                try:
                    os.unlink(__SENSORDIR__+"postLearning")
                except:
                    pass
                try:
                    os.unlink(__SENSORDIR__+"inLearning")
                except:
                    pass
            logging.info("Romove Done")
            return 0

        elif Data.data.action == "Reset":
            if Model.isOnline:
                Model.Sleep()
                time.sleep(1)
            if Model.isExist:
                Model.Reset()
                Path(__SENSORDIR__+"preLearning").touch()
                try:
                    os.unlink(__SENSORDIR__+"postLearning")
                except:
                    pass
                try:
                    os.unlink(__SENSORDIR__+"inLearning")
                except:
                    pass
            logging.info("Reset Done")
            return 0

        elif Data.data.action == "Save":
            if Model.isOnline:
                Model.Save()
            logging.info("Save Done")
            return 0

        elif Data.data.action == "Train":
            if Model.isOnline:
                Model.Sleep()
                time.sleep(1)

            Model.isTrained = False
            trainFlag = True

        elif Data.data.action == "Wake":
            if Model.isExist and Model.isTrained:
                wakeFlag = True
        logging.info("Command process end")

    if (Data.dType == "DATA" and not Model.isSafeStop) or trainFlag or wakeFlag:
        if Data.dType == "DATA":
            logging.info("Model Entrance Receive Data:\nValue:{value}\nTimestamp:{timeidx}".format(
                value=Data.data.value, timeidx=Data.data.timestamp))

        if not Model.isExist:
            logging.info("Model Prepare")
            Path(__SENSORDIR__+"inLearning").touch()
            try:
                os.unlink(__SENSORDIR__+"preLearning")
            except:
                pass
            try:
                os.unlink(__SENSORDIR__+"postLearning")
            except:
                pass

            Model.Prepare()  # Prepare, copy model dependence file to data folder
            logging.info("Model Prepare Done")
        if not Model.isTrained or Model.isRetrainPeriod:
            logging.info("Model Train")
            Path(__SENSORDIR__+"inLearning").touch()
            try:
                os.unlink(__SENSORDIR__+"postLearning")
            except:
                pass
            try:
                os.unlink(__SENSORDIR__+"preLearning")
            except:
                pass
            if Model.isRetrainPeriod:
                if Model.isOnline:
                    Model.Sleep()
                Model.Reset()
            Model.Pretrain()  # Set up model to be ready for train

            TrainOutput = Model.Train()  # Train Model
            # Train Should Implement Save By it Own
            # Save in Train should generate same file formate as Model.save
            # And Can be loaded by Model.Load without difference.

            if os.path.isfile(TrainOutput):
                # If model has generate output during traing,write it back to cratedb
                # Output file must contain the following columns:
                # [timestamp,value,prediction,anomaly_score,anomaly_likelihood,Log_anomaly_likelihood]
                dataAccessor.trainoutputWriteback(TrainOutput, Data,
                                                  __GLOBAL_THREADHOLD__)

            Model.TrainCleanup()  # Optional Clean Up File generated during model traning

            os.unlink(__SENSORDIR__+"localdata.tmp")  # Remove Local Data Cache
            try:
                os.unlink(__SENSORDIR__+"counter.tmp")
            except:
                pass
            logging.info("Model Train Done")
        if not Model.isOnline:
            logging.info("Model Bootup...")
            Path(__SENSORDIR__+"inLearning").touch()
            try:
                os.unlink(__SENSORDIR__+"postLearning")
            except:
                pass

            Model.Load()
            Model.Recovery()  # There Should be only two situtation that will come in this code
            # block, After Train and After AIOT-DFC Restart
            # 1. After Train.
            # Should only have current data and data newer than current data.

            # 2. After AIOT-DFC Restart.
            # Should Have 4 types of data.
            #  A. Data older than current data which has been seen by model but
            #     not yet saved by model: need refit in model but don't need to
            #     be rewrite inside history content holder(CradeDB for example)
            #  B. Data older than current data which has not yet been seen by
            #     model nor saved by model nor save inside history content holder
            #     This Data Need to be refit in model and be rewrite inside history
            #     content holder.
            #  C. Current Data
            #  D. Data newer than Current Data, namely data generated during
            #     Model re-Loading

            #CleanupPreUnprocessData(Data,Model,Data.data.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            #timestamp,value,prediction,anomaly,metadata = Model.Use(Data.data.value,Data.data.timestamp)
            # resultWriteback(timestamp,value,prediction,anomaly,metadata,Data)
            #CleanupPostUnprocessData(Data,Model,Data.data.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            Model.Save()
            try:
                os.unlink(__SENSORDIR__+"inLearning")
            except:
                pass
            Path(__SENSORDIR__+"postLearning").touch()
            logging.info("Model Bootup Done")
            return 0
        if Model.isSavePeriod:
            Model.Save()
            logging.info("Save Done")
        timestamp, value, prediction, anomaly, metadata = Model.Use(
            Data.data.value, Data.data.timestamp)  # Use model to generate real time prediction
        if anomaly == True:
            logging.warning("Anomaly Detection at \nIoT Agent {fiwareService}\nEntityId {entityID}\nTimestamp {timestamp}".format(
                fiwareService=Data.data.fiware_service, entityID=Data.data.entityID, timestamp=timestamp))
            # TODO:Raise Warming
            pass
        dataAccessor.resultWriteback(
            timestamp, value, prediction, anomaly, metadata, Data)

        logging.info("Data Process End")
        return 0
