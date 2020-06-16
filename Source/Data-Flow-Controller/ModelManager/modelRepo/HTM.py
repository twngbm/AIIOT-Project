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
import re
import shutil
from pathlib import Path
current_dir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from DataManager import dataAccessor

class model:
    def __init__(self, Data, __GLOBAL_THREADHOLD__):
        self.Data = Data
        self.fiware_service = self.Data.data.fiware_service
        self.deviceID = self.Data.data.deviceID
        self.__GLOBAL_THREADHOLD__ = __GLOBAL_THREADHOLD__
        self.__SENSORDIR__ = (
            os.path.dirname(os.path.abspath(__file__))
            + "/../../Data/IoT/"
            + self.fiware_service
            + "/"
            + self.deviceID
            + "/"
        )
        self.__WORKDIR__ = self.__SENSORDIR__ + "HTM/"
        self.workdir = self.__SENSORDIR__ + "HTM/"
        self.TrainOutput = None
        if not os.path.isdir(self.__WORKDIR__):
            self.isExist = False
        else:
            self.isExist = True
        if not os.path.isfile(self.__SENSORDIR__+"postLearning"):
            self.isTrained = False
        else:
            self.isTrained = True
        try:
            writer = os.open(self.__WORKDIR__+"input.pipe",
                             os.O_WRONLY | os.O_NONBLOCK)
            os.close(writer)
            self.isOnline = True
            if os.path.isfile(self.__SENSORDIR__+"inLearning"):
                self.isOnline = False
        except:
            self.isOnline = False

        try:
            with open(self.__WORKDIR__+"localnewest.tmp", "r") as f:
                data = f.read().split(",")[1]
            lastRecordedTime = datetime.datetime.strptime(
                data, "%Y-%m-%d %H:%M:%S")
            timePeriod = (self.Data.data.timestamp -
                          lastRecordedTime).total_seconds()
            if timePeriod >= self.Data.static_attributes.savePeriod:
                self.isSavePeriod = True
            else:
                self.isSavePeriod = False
        except:
            self.isSavePeriod = False
        
        self.isRetrainPeriod = False
        

        if os.path.isfile(self.__WORKDIR__+"modelInactive"):
            self.isSafeStop = True
        else:
            self.isSafeStop = False

    def Prepare(self):

        self.__REPOPATH__ = os.path.dirname(os.path.abspath(__file__))
        p = subprocess.Popen(
            ["cp", "-r", self.__REPOPATH__ + "/HTM", self.__SENSORDIR__]
        )
        p.wait(10)

    def Pretrain(self):

        shutil.copy(self.__SENSORDIR__+"localnewest.tmp", self.__WORKDIR__)
        with open(self.__WORKDIR__ + "search_def.json", "r") as f:
            swarm_config = json.loads(f.read())
        swarm_config["includedFields"][0]["fieldType"] = self.Data.static_attributes.dataType
        swarm_config["streamDef"]["streams"][0]["source"] = (
            "file://Data/IoT/"
            + self.Data.data.fiware_service
            + "/"
            + self.Data.data.deviceID
            + "/"
            + "localdata.tmp"
        )
        if os.path.isfile(self.__SENSORDIR__+"localdata.tmp"):
            pass
        else:
            try:
                data = dataAccessor.queFromCratedbNewest(
                    self.Data.data.fiware_service, self.Data.data.entityID, int(self.Data.data.metadata["TrainLimit"]))

            except KeyError:
                raise KeyError
            with open(self.__SENSORDIR__+"localdata.tmp", "w+") as f:
                f.write("value,timestamp\n" +
                        self.Data.static_attributes.dataType+",datetime\n ,T\n")
                for record in data:
                    value = str(record["count"])
                    timestampint = record["time_index"]
                    timestamp = (datetime.timedelta(
                        seconds=timestampint/1000)+datetime.datetime(1970, 1, 1))
                    timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(value+","+timestamp+"\n")
                f.close()

        with open(self.__WORKDIR__ + "search_def.json", "w") as f:
            json.dump(swarm_config, f)
        swarm = subprocess.Popen(
            ["/usr/bin/python2.7", self.__WORKDIR__ + "swarm.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        while True:
            state = swarm.poll()
            if state != None:
                print("Exist Code:", state)
                break
            time.sleep(1)
        if state != 0:
            raise RuntimeError
        os.unlink(self.__WORKDIR__+"permutations.py")
        os.unlink(self.__WORKDIR__+"description.py")
        os.unlink(self.__WORKDIR__+"description.pyc")
        os.unlink(self.__WORKDIR__+"default_Report.csv")
        os.system("rm "+self.__WORKDIR__+"default_HyperSearchJobID.pkl")
        os.system("mv "+self.__WORKDIR__ +
                  "model_0/model_params.py "+self.__WORKDIR__)
        os.system("rm -r "+self.__WORKDIR__+"model_0")

    def Train(self):

        train = subprocess.Popen(["python2.7", self.__WORKDIR__+"train.py"])
        while True:
            state = train.poll()
            if state != None:
                print("Exist Code:", state)
                break
            time.sleep(1)
        if state != 0:
            raise RuntimeError

        return self.__SENSORDIR__+"trainoutput.csv"

    def TrainCleanup(self):

        os.unlink(self.__SENSORDIR__+"trainoutput.csv")

    def Load(self):

        try:
            os.unlink(self.__WORKDIR__+"modelInactive")
        except:
            pass
        pid = os.fork()
        if pid == 0:
            self.MODELP = subprocess.Popen(
                ["python2.7", self.__WORKDIR__+"model.py"])
            Path(self.__WORKDIR__ +
                 "HTM-{pid}.pid".format(pid=self.MODELP.pid)).touch()
            self.MODELP.wait()
            logging.info("MODEL PROCESS EXIST")
            os._exit(0)
        else:
            logging.info("Model Loading...")
            while True:
                try:
                    reader = os.open(self.__WORKDIR__ +
                                     "output.pipe", os.O_RDONLY)
                    break
                except:
                    time.sleep(1)
            result = self.__get_message__(reader)
            os.close(reader)
            if result == "ACK":
                logging.info("Model Load Done")
                self.isOnline = True
            else:
                raise IOError

    def Save(self):
        writer = os.open(self.__WORKDIR__+"input.pipe",
                         os.O_WRONLY | os.O_NONBLOCK)
        msg = "SAVE"
        msg = self.__create_msg__(msg.encode("utf8"))
        os.write(writer, msg)
        os.close(writer)

    def Recovery(self):

        with open(self.__WORKDIR__+"localnewest.tmp", "r") as f:
            data = f.read().split(",")[1]
        lastRecordedTime = datetime.datetime.strptime(
            data, "%Y-%m-%d %H:%M:%S")

        try:
            currentTime = self.Data.data.timestamp
            currentValue = self.Data.data.value
        except:
            data = dataAccessor.queFromCratedbNewest(
                self.Data.data.fiware_service, self.Data.data.entityID, 1)[0]
            currentTime = (datetime.timedelta(
                seconds=data["time_index"]/1000)+datetime.datetime(1970, 1, 1))
            dataType = self.Data.static_attributes.dataType
            if dataType == "float":
                currentValue = float(data["count"])
            elif dataType == "int":
                currentValue = int(data["count"])
            elif dataType == "bool":
                currentValue = (
                    True if data["count"] in [
                        "True", "true", "1"] else False
                )
            elif dataType == "string":
                currentValue = data["count"]

        logging.info("Pre Cleanup Start.")
        self.__ReLoopPreUnsavedData__(currentTime, lastRecordedTime)

        timestamp, value, prediction, anomaly, metadata = self.Use(
            currentValue, currentTime)
        dataAccessor.resultWriteback(
            timestamp, value, prediction, anomaly, metadata, self.Data)

        logging.info("Post Cleanup Start.")
        self.__CleanupPostUnprocessData__(currentTime)

    def Sleep(self):
        dirl = os.listdir(self.__WORKDIR__)
        pidfile = {}
        for f in dirl:
            mf = re.match(r"^HTM-(.*)\.pid$", f)
            if mf != None:
                pidfile[int(mf.group(0)[4:-4])] = mf.group(0)
        for pid in pidfile:
            try:
                os.kill(pid, 9)
            except ProcessLookupError:
                pass
            finally:
                logging.info("Kill Process with pid:{pid}".format(pid=pid))
            os.unlink(self.__WORKDIR__+pidfile[pid])
        Path(self.__WORKDIR__+"modelInactive").touch()
        self.isOnline = False

    def Use(self, value, timestamp):
        writer = os.open(self.__WORKDIR__+"input.pipe",
                         os.O_WRONLY | os.O_NONBLOCK)
        msg = str(value)+","+str(timestamp)
        msg = self.__create_msg__(msg.encode("utf8"))
        os.write(writer, msg)
        reader = os.open(self.__WORKDIR__+"output.pipe", os.O_RDONLY)
        result = self.__get_message__(reader)
        os.close(writer)
        os.close(reader)
        result = result[1:-1].split(",")

        dataType = self.Data.static_attributes.dataType
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

        return timestamp, value, predictionValue, anomaly, {"anomalyScore": anomalyScore, "anomalyLikelihood": anomalyLikelihood, "logAnomalyLikelihood": logAnomalyLikelihood}

    def Reset(self):
        try:
            shutil.rmtree(self.__WORKDIR__)
        except:
            pass
        self.__REPOPATH__ = os.path.dirname(os.path.abspath(__file__))
        p = subprocess.Popen(
            ["cp", "-r", self.__REPOPATH__ + "/HTM", self.__SENSORDIR__]
        )
        p.wait(10)
        self.isTrained = False

    def Remove(self):
        shutil.rmtree(self.__WORKDIR__)
        self.isExist = False
        self.isTrained = False

    def __create_msg__(self, content: bytes) -> bytes:
        return struct.pack("<I", len(content)) + content

    def __get_message__(self, fifo: int) -> str:
        msg_size_bytes = os.read(fifo, 4)
        msg_size = struct.unpack("<I", msg_size_bytes)[0]
        msg_content = os.read(fifo, msg_size).decode("utf8")
        return msg_content

    def __ReLoopPreUnsavedData__(self, EndTime, StartTime):
        # Walk Through Type A and Type B Data, which Type A data's anomaly != None, though  save type B data only.
        result = dataAccessor.queFromCratedbBound(
            self.Data.data.fiware_service, self.Data.data.entityID, StartTime, EndTime)

        for record in result:

            time.sleep(1)
            INvalue = record["count"]
            timestampint = record["timestamp"]
            INtimestamp = (datetime.timedelta(
                seconds=timestampint/1000)+datetime.datetime(1970, 1, 1))
            timestamp, value, prediction, anomaly, metadata = self.Use(
                INvalue, INtimestamp)
            if record["anomaly"] == None:
                dataAccessor.resultWriteback(
                    timestamp, value, prediction, anomaly, metadata, self.Data)
        logging.info("Pre Cleanup Done.")

    def __CleanupPostUnprocessData__(self, StartTime):
        result = dataAccessor.queFromCratedbBack(
            self.Data.data.fiware_service, self.Data.data.entityID, StartTime)

        if result == []:
            logging.info("Post Cleanup Done.")
            return 0
        for record in result:

            time.sleep(1)
            INvalue = record["count"]
            timestampint = record["timestamp"]
            INtimestamp = (datetime.timedelta(
                seconds=timestampint/1000)+datetime.datetime(1970, 1, 1))
            timestamp, value, prediction, anomaly, metadata = self.Use(
                INvalue, INtimestamp)
            dataAccessor.resultWriteback(
                timestamp, value, prediction, anomaly, metadata, self.Data)
        return self.__CleanupPostUnprocessData__(INtimestamp)
