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
# from DataManager import dataWriteback
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
# if SENSOR DELETE:
#   model.Stop()
#   model.Clean()
#
# pred=model.Use()
#
# if pred is anomaly:
#   messageManger.send(warning)
#
# dataWriteback(pred)

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

current_dir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from DataManager import dataWriteback


class SensorData:
    def __init__(self, data: dict):
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
        ) #Datetime object
        self.deviceID = self.__data__["device_id"]
        self.entityID = self.__data__["entity_id"]
        self.fiware_service = self.__data__["fiware_service"]


class __STATIC_ATTRITUBES__:
    def __init__(self, data: dict):
        self.__static_attributes__ = data["static_attributes"]
        self.sensorName = self.__static_attributes__["sensorName"]
        self.fieldName = self.__static_attributes__["fieldName"]
        self.refRoom = self.__static_attributes__["refRoom"]
        self.timeResolution = float(
            self.__static_attributes__["timeResolution"])
        self.savePeriod=int(self.__static_attributes__["savePeriod"])
        self.targetTime = float(self.__static_attributes__["targetTime"])
        self.targetModel = self.__static_attributes__["targetModel"]
        self.sensorType = self.__static_attributes__["sensorType"]
        self.unit = self.__static_attributes__["unit"]
        self.isDummy = (
            True
            if self.__static_attributes__["isDummy"] in ["True", "true", 1]
            else False
        )


def modelSelector(targetModel: str):
    try:
        modelModule = importlib.import_module("modelRepo." + targetModel)
    except:
        raise ImportError

    return modelModule


def trainoutputWriteback(path: str, Data: SensorData, __GLOBAL_THREADHOLD__: float):
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
            dataWriteback.writeToCratedb(
                fiware_service,
                entity_id,
                timestamp,
                predictionValue,
                anomalyScore,
                anomalyLikelihood,
                logAnomalyLikelihood,
                anomaly,
            )




    
def modelHandler(Data: SensorData, __GLOBAL_THREADHOLD__: float):
    targetModel = Data.static_attributes.targetModel
    module = modelSelector(targetModel)
    Model = module.model(Data,__GLOBAL_THREADHOLD__)
    __SENSORDIR__ = (
        os.path.dirname(os.path.abspath(__file__))
        + "/../Data/IoT/"
        + Data.data.fiware_service
        + "/"
        + Data.data.deviceID
        + "/"
    )
    if not Model.isExist:
        Path(__SENSORDIR__+"inLearning").touch()
        os.unlink(__SENSORDIR__+"preLearning")
        

        Model.Prepare()  # Prepare, copy model dependence file to data folder

    if not Model.isTrained:

        Model.Pretrain()  # Set up model to be ready for train

        Model.Train()  # Train Model
                       # Train Should Implement Save By it Own
                       # Save in Train should generate same file formate as Model.save
                       # And Can be loaded by Model.Load without difference.

        if Model.TrainOutput != None:
            # If model has generate output during traing,write it back to cratedb
            # Output file must contain the following columns:
            # [timestamp,value,prediction,anomaly_score,anomaly_likelihood,Log_anomaly_likelihood]
            trainoutputWriteback(Model.TrainOutput, Data,
                                 __GLOBAL_THREADHOLD__)

        Model.TrainCleanup()  # Optional Clean Up File generated during model traning
        
        os.unlink(__SENSORDIR__+"localdata.tmp") #Remove Local Data Cache
        os.unlink(__SENSORDIR__+"counter.tmp")
        
        """
        Model.Load()


        timestamp,value,prediction,anomaly,metadata = Model.Use(Data.data.value,Data.data.timestamp)
        resultWriteback(timestamp,value,prediction,anomaly,metadata,Data)
        CleanupPostUnprocessData(Data,Model,Data.data.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        

        os.unlink(__SENSORDIR__+"inLearning")
        Path(__SENSORDIR__+"postLearning").touch()
        return 0
        """

    if not Model.isOnline:
        
        Path(__SENSORDIR__+"inLearning").touch()
        try:
            os.unlink(__SENSORDIR__+"postLearning")
        except:
            pass
        
         
        Model.Load()
        Model.Recovery() # There Should be only two situtation that will come in this code 
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
        #resultWriteback(timestamp,value,prediction,anomaly,metadata,Data)
        #CleanupPostUnprocessData(Data,Model,Data.data.timestamp.strftime("%Y-%m-%d %H:%M:%S"))

        os.unlink(__SENSORDIR__+"inLearning")
        Path(__SENSORDIR__+"postLearning").touch()
        return 0
    if Model.isSavePeriod:
        Model.Save()
    timestamp,value,prediction,anomaly,metadata = Model.Use(Data.data.value,Data.data.timestamp)#Use model to generate real time prediction
    if anomaly==True:
        # TODO:Raise Warming
        pass
    dataWriteback.resultWriteback(timestamp,value,prediction,anomaly,metadata,Data)
    
    logging.info("Data Process End")
    return 0
# if SAVE INTERVAL:
#   model.Save()
# if SENSOR DELETE:
#   model.Stop()
#   model.Clean()
#
# pred=model.Use()
#
# if pred is anomaly:
#   messageManger.send(warning)
#
# dataWriteback(pred)
