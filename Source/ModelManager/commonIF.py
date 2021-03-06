from DataManager import dataAccessor
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


class ModelCommand:
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
        if self.dataType == "Float":
            self.value = float(self.__data__["value"])
        elif self.dataType == "Integer":
            self.value = int(self.__data__["value"])
        elif self.dataType == "Boolean":
            self.value = (
                True if self.__data__["value"] in [
                    "True", "true", "1"] else False
            )
        else:
            self.value = str(self.__data__["value"])

        self.timestamp = datetime.datetime.strptime(
            self.__data__["timestamp"], "%Y-%m-%d %H:%M:%S"
        )  # Datetime object
        self.deviceName = self.__data__["device_name"]
        self.entityID = self.__data__["entity_id"]
        self.service_group = self.__data__["service_group"]


class __COMMAND__:
    def __init__(self, data: dict):
        self.__data__ = data["data"]
        self.action = self.__data__["value"]
        self.deviceName = self.__data__["device_name"]
        self.entityID = self.__data__["entity_id"]
        self.service_group = self.__data__["service_group"]
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
        self.retrainPeriod = int(self.__static_attributes__["retrainPeriod"])
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
        + Data.data.service_group
        + "/"
        + Data.data.deviceName
        + "/"
    )
    if Data.dType == "COMMAND":
        logging.info("{sg}/{device} Receive Command:{action}".format(
            action=Data.data.action, sg=Data.data.service_group, device=Data.data.deviceName))
        if Data.data.action == "Sleep":
            if Model.isOnline:
                Model.Sleep()
            return 0

        elif Data.data.action == "Remove":
            if Model.isExist:
                Model.Remove()
                try:
                    Path(__SENSORDIR__+"preLearning").touch()
                except:
                    pass
                try:
                    os.unlink(__SENSORDIR__+"postLearning")
                except:
                    pass
                try:
                    os.unlink(__SENSORDIR__+"inLearning")
                except:
                    pass
            logging.info("{sg}/{device} Romove Done".format(
                sg=Data.data.service_group, device=Data.data.deviceName))
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
            logging.info("{sg}/{device} Reset Done".format(
                sg=Data.data.service_group, device=Data.data.deviceName))
            return 0

        elif Data.data.action == "Save":
            if Model.isOnline:
                Model.Save()
            logging.info(
                "{sg}/{device} Save Done".format(sg=Data.data.service_group, device=Data.data.deviceName))
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
    if (Data.dType == "DATA" and not Model.isSafeStop) or trainFlag or wakeFlag:
        if Data.dType == "DATA":
            logging.info("{sg}/{device} Receive Data T:{timeidx},V:{value}".format(
                timeidx=Data.data.timestamp, value=Data.data.value, sg=Data.data.service_group, device=Data.data.deviceName))

        if not Model.isExist:
            logging.info("{sg}/{device} Model Prepare Start".format(
                sg=Data.data.service_group, device=Data.data.deviceName))
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
            logging.info("{sg}/{device} Model Prepare Done".format(
                sg=Data.data.service_group, device=Data.data.deviceName))
        if not Model.isTrained or Model.isRetrainPeriod:
            logging.info("{sg}/{device} Model Train Start".format(
                sg=Data.data.service_group, device=Data.data.deviceName))
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

            Model.Train()  # Train Model
            # Train Should Implement Save By it Own
            # Save in Train should generate same file formate as Model.save
            # And Can be loaded by Model.Load without difference.

            Model.TrainCleanup()  # Optional Clean Up File generated during model traning

            os.unlink(__SENSORDIR__+"localdata.tmp")  # Remove Local Data Cache
            try:
                os.unlink(__SENSORDIR__+"counter.tmp")
            except:
                pass
            logging.info("{sg}/{device} Model Train Done".format(
                sg=Data.data.service_group, device=Data.data.deviceName))

            if trainFlag:
                Path(__SENSORDIR__+"postLearning").touch()
                try:
                    os.unlink(__SENSORDIR__+"inLearning")
                except:
                    pass
                wakeFlag = True

        if not Model.isOnline or wakeFlag:
            logging.info("{sg}/{device} Model Bootup Start".format(
                sg=Data.data.service_group, device=Data.data.deviceName))
            Path(__SENSORDIR__+"inLearning").touch()
            try:
                os.unlink(__SENSORDIR__+"postLearning")
            except:
                pass

            Model.Load()
            Model.Recovery()
            # There Should be only two situtation that will come in this code
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

            # CleanupPreUnprocessData(Data,Model,Data.data.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            # timestamp,value,prediction,anomaly,metadata = Model.Use(Data.data.value,Data.data.timestamp)
            # resultWriteback(timestamp,value,prediction,anomaly,metadata,Data)
            # CleanupPostUnprocessData(Data,Model,Data.data.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            Model.Save()
            try:
                os.unlink(__SENSORDIR__+"inLearning")
            except:
                pass
            Path(__SENSORDIR__+"postLearning").touch()
            logging.info("{sg}/{device} Model Bootup Done".format(
                sg=Data.data.service_group, device=Data.data.deviceName))
            return 0

        if Model.isSavePeriod:
            Model.Save()
            logging.info("{sg}/{device} Model Save Done".format(
                sg=Data.data.service_group, device=Data.data.deviceName))
        timestamp, value, anomalyScore, anomalyFlag, metadata = Model.Use(
            Data.data.value, Data.data.timestamp)  # Use model to generate real time prediction
        dataAccessor.resultWriteback(
            timestamp, value, anomalyScore, anomalyFlag, metadata, Data)
        dataAccessor.raiseAnomaly(
            Data.data.entityID, anomalyFlag, anomalyScore, metadata)
        if anomalyFlag:
            logging.warning("Anomaly Detection at Service Group:{sg} EntityId:{entityID} at Time:{timestamp}".format(
                sg=Data.data.service_group, entityID=Data.data.entityID, timestamp=timestamp))
            dataAccessor.groupAnomaly(Data)
        return 0
