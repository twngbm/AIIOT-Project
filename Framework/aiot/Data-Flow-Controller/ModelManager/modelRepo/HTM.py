import os
import subprocess
import json
import time
import logging
import sys
import inspect
import select
import struct
import datetime
current_dir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from DataManager import dataWriteback
class model:
    def __init__(self, Data,__GLOBAL_THREADHOLD__):
        self.Data = Data
        
        self.fiware_service = self.Data.data.fiware_service
        self.deviceID = self.Data.data.deviceID
        self.__GLOBAL_THREADHOLD__=__GLOBAL_THREADHOLD__
        self.__SENSORDIR__ = (
            os.path.dirname(os.path.abspath(__file__))
            + "/../../Data/IoT/"
            + self.fiware_service
            + "/"
            + self.deviceID
            + "/"
        )
        self.__WORKDIR__ = self.__SENSORDIR__ + "HTM/"
        self.TrainOutput=None
        if not os.path.isdir(self.__WORKDIR__):
            self.isExist = False
        else:
            self.isExist = True
        if not os.path.isfile(self.__SENSORDIR__+"postLearning"):
            self.isTrained=False
        else:
            self.isTrained=True
        try:
            writer=os.open(self.__WORKDIR__+"input.pipe",os.O_WRONLY|os.O_NONBLOCK)
            os.close(writer)
            self.isOnline=True
        except:
            self.isOnline=False
        
        try:
            with open(self.__WORKDIR__+"localnewest.tmp","r") as f:
                data=f.read().split(",")[1]
            lastRecordedTime=datetime.datetime.strptime(data,"%Y-%m-%d %H:%M:%S")
            timePeriod=(self.Data.data.timestamp-lastRecordedTime).total_seconds()
            if timePeriod>=self.Data.static_attributes.savePeriod:
                self.isSavePeriod=True
            else:
                self.isSavePeriod=False
        except:
            self.isSavePeriod=False
        self.isRetrainPeriod=False
        

    def Prepare(self):
        startTime=time.time()
        print("Start Prepare at:",startTime)
        self.__REPOPATH__ = os.path.dirname(os.path.abspath(__file__))
        p = subprocess.Popen(
            ["cp", "-r", self.__REPOPATH__ + "/HTM", self.__SENSORDIR__],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        p.wait(10)
        finishTime=time.time()
        print("Prepare finish at:",finishTime)
        print("Take total:",int(finishTime-startTime)," seconds")

    def Pretrain(self):
        startTime=time.time()
        print("Start Pretrain at:",startTime)
        with open(self.__WORKDIR__ + "search_def.json", "r") as f:
            swarm_config = json.loads(f.read())
        swarm_config["includedFields"][0]["fieldType"] = self.Data.data.dataType
        swarm_config["streamDef"]["streams"][0]["source"] = (
            "file://Data/IoT/"
            + self.Data.data.fiware_service
            + "/"
            + self.Data.data.deviceID
            + "/"
            + "localdata.tmp"
        )
        with open(self.__WORKDIR__ + "search_def.json", "w") as f:
            json.dump(swarm_config, f)
        swarm = subprocess.Popen(
            ["/usr/bin/python2.7", self.__WORKDIR__ + "swarm.py"]

        )
        while True:
            state=swarm.poll()
            if state!=None:
                print("Exist Code:",state)
                break
            time.sleep(1)
        if state!=0:
            raise RuntimeError
        os.unlink(self.__WORKDIR__+"permutations.py")
        os.unlink(self.__WORKDIR__+"description.py")
        os.unlink(self.__WORKDIR__+"description.pyc")
        os.unlink(self.__WORKDIR__+"default_Report.csv")
        os.system("rm "+self.__WORKDIR__+"default_HyperSearchJobID.pkl")
        os.system("mv "+self.__WORKDIR__+"model_0/model_params.py "+self.__WORKDIR__)
        os.system("rm -r "+self.__WORKDIR__+"model_0")
        finishTime=time.time()
        print("Swarm finish at:",finishTime)
        print("Take total:",int(finishTime-startTime)," seconds")

    def Train(self):
        
        startTime=time.time()
        print("Start Train at:",startTime)
        train=subprocess.Popen(["python2.7",self.__WORKDIR__+"train.py"])
        while True:
            state=train.poll()
            if state!=None:
                print("Exist Code:",state)
                break
            time.sleep(1)
        if state!=0:
            raise RuntimeError
        finishTime=time.time()
        
        os.system("cp "+self.__SENSORDIR__+"localnewest.tmp "+self.__WORKDIR__)
        print("Train finish at:",finishTime)
        print("Take total:",int(finishTime-startTime)," seconds")
        return self.__SENSORDIR__+"trainoutput.csv"

    def TrainCleanup(self):
        startTime=time.time()
        print("Start TrainCleanup at:",startTime)

        os.unlink(self.__SENSORDIR__+"trainoutput.csv")

        finishTime=time.time()
        print("TrainCleanup finish at:",finishTime)
        print("Take total:",int(finishTime-startTime)," seconds")


    def Load(self):
        print("Start model")
        pid=os.fork()
        if pid==0:
            p=subprocess.Popen(["python2.7",self.__WORKDIR__+"model.py"])
            p.wait()
            print("MODEL STOP")
        else:
            print("Wait for model to be ready")
            while True:
                try:
                    reader=os.open(self.__WORKDIR__+"output.pipe",os.O_RDONLY)
                    break
                except:
                    time.sleep(1)
            result=self.__get_message__(reader)
            os.close(reader)
            if result=="ACK":
                print("Wait End.")
                self.isOnline=True
            else:
                raise IOError
            

    def Save(self):
        writer=os.open(self.__WORKDIR__+"input.pipe",os.O_WRONLY|os.O_NONBLOCK)
        msg="SAVE"
        msg=self.__create_msg__(msg.encode("utf8"))
        os.write(writer,msg)
        os.close(writer)
        logging.info("Model saved")

    def Recovery(self):
        with open(self.__WORKDIR__+"localnewest.tmp","r") as f:
                data=f.read().split(",")[1]
        lastRecordedTime=datetime.datetime.strptime(data,"%Y-%m-%d %H:%M:%S")
        currentTime=self.Data.data.timestamp
        self.__ReLoopPreUnsavedData__(currentTime,lastRecordedTime)
        timestamp,value,prediction,anomaly,metadata = self.Use(self.Data.data.value,self.Data.data.timestamp)
        dataWriteback.resultWriteback(timestamp,value,prediction,anomaly,metadata,self.Data)
        self.__CleanupPostUnprocessData__(currentTime)
        self.Save()
    def Stop(self):
        
        raise NotImplementedError

    def Use(self,value,timestamp):
        writer=os.open(self.__WORKDIR__+"input.pipe",os.O_WRONLY|os.O_NONBLOCK)
        msg=str(value)+","+str(timestamp)
        msg=self.__create_msg__(msg.encode("utf8"))
        os.write(writer,msg)
        reader=os.open(self.__WORKDIR__+"output.pipe",os.O_RDONLY)
        result=self.__get_message__(reader)
        os.close(writer)
        os.close(reader)
        result = result[1:-1].split(",")
        
        dataType = self.Data.data.dataType
        if dataType == "float":
            predictionValue = float(result[0])
        elif dataType == "int":
            predictionValue = int(result[0])
        elif dataType == "bool":
            predictionValue = (
                True if result[0] in ["True", "true", "1"] else False
            )
        elif dataType == "string":
            predictionValue = result[0]
        anomalyScore = float(result[1])
        anomalyLikelihood = float(result[2])
        logAnomalyLikelihood = float(result[3])
        if logAnomalyLikelihood > self.__GLOBAL_THREADHOLD__:
            anomaly = "True"
        else:
            anomaly = "False"
        
        return timestamp,value,predictionValue,anomaly,{"anomalyScore":anomalyScore,"anomalyLikelihood":anomalyLikelihood,"logAnomalyLikelihood":logAnomalyLikelihood}
       

            
        


    def Clean(self):
        pass
    
    def __create_msg__(self,content: bytes) -> bytes:
        return struct.pack("<I", len(content)) + content

    def __get_message__(self,fifo: int) -> str:
        msg_size_bytes = os.read(fifo, 4)
        msg_size = struct.unpack("<I", msg_size_bytes)[0]
        msg_content = os.read(fifo, msg_size).decode("utf8")
        return msg_content

    def __ReLoopPreUnsavedData__(self,EndTime,StartTime):
        # Walk Through Type A and Type B Data, which Type A data's anomaly != None, though  save type B data only.
        result=dataWriteback.queFromCratedbBound(self.Data.data.fiware_service,self.Data.data.entityID,StartTime,EndTime)
        
        for record in result:
            
            time.sleep(1)
            INvalue=record["count"]
            timestampint=record["timestamp"]
            INtimestamp=(datetime.timedelta(seconds=timestampint/1000)+datetime.datetime(1970,1,1))
            timestamp,value,prediction,anomaly,metadata = self.Use(INvalue,INtimestamp)
            if record["anomaly"]==None:
                dataWriteback.resultWriteback(timestamp,value,prediction,anomaly,metadata,self.Data)
        logging.info("Pre Cleanup Done.")
    def __CleanupPostUnprocessData__(self,StartTime):
        result=dataWriteback.queFromCratedbBack(self.Data.data.fiware_service,self.Data.data.entityID,StartTime)
        if result==[]:
            logging.info("Post Cleanup Done.")
            return 0
        for record in result:
            
            time.sleep(1)
            INvalue=record["count"]
            timestampint=record["timestamp"]
            INtimestamp=(datetime.timedelta(seconds=timestampint/1000)+datetime.datetime(1970,1,1))
            timestamp,value,prediction,anomaly,metadata = self.Use(INvalue,INtimestamp)
            dataWriteback.resultWriteback(timestamp,value,prediction,anomaly,metadata,self.Data)
        return self.__CleanupPostUnprocessData__(INtimestamp)