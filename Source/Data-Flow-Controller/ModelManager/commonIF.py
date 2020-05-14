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
import csv
import sys
import inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from DataManager import dataWriteback
class SensoeData:
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
                True if self.__data__["value"] in ["True", "true", "1"] else False
            )
        elif self.dataType == "string":
            self.value = self.__data__["value"]

        self.timestamp = datetime.datetime.strptime(
            self.__data__["timestamp"], "%Y-%m-%d %H:%M:%S"
        )
        self.deviceID = self.__data__["device_id"]
        self.entityID = self.__data__["entity_id"]
        self.fiware_service = self.__data__["fiware_service"]

class __STATIC_ATTRITUBES__:
    def __init__(self, data: dict):
        self.__static_attributes__ = data["static_attributes"]
        self.sensorName = self.__static_attributes__["sensorName"]
        self.fieldName = self.__static_attributes__["fieldName"]
        self.refRoom = self.__static_attributes__["refRoom"]
        self.timeResolution = float(self.__static_attributes__["timeResolution"])
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
def trainoutputWriteback(path:str,Data:SensoeData):
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
            if float(logAnomalyLikelihood) > 0.7:
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

def dataProcess(Data: SensoeData):

    targetModel = Data.static_attributes.targetModel
    module = modelSelector(targetModel)
    Model = module.model(Data)
    __SENSORDIR__ = (
            os.path.dirname(os.path.abspath(__file__))
            + "/../Data/IoT/"
            + Data.data.fiware_service
            + "/"
            + Data.data.deviceID
            + "/"
        )
    if not Model.isExist:
        os.unlink(__SENSORDIR__+"preLearning")
        with open(__SENSORDIR__+"inLearning","w+") as f:
            f.close()
        
        Model.Prepare() #Prepare, copy model dependence file to data folder
        
    if not Model.isTrained:
        
        Model.Pretrain() #Set up model to be ready for train

        Model.Train() #Train Model

        if Model.TrainOutput!=None:
            # If model has generate output during traing,write it back to cratedb
            # Output file must contain the following columns:
            # [timestamp,value,prediction,anomaly_score,anomaly_likelihood,Log_anomaly_likelihood]
            trainoutputWriteback(Model.TrainOutput, Data)

        Model.TrainCleanup() #Optional Clean Up File generated during model traning
        
        # TODO:
        # Process unhandel data during learning

        Model.Online()
        os.unlink(__SENSORDIR__+"inLearning")
        
        with open(__SENSORDIR__+"postLearning","w+") as f:
            f.close()
    
    if not Model.isOnline:
        Model.Online()

    result=Model.Use()
    print(result)

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
    