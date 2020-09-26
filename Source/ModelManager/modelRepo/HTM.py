from DataManager import dataAccessor
import os
import subprocess
import json
import time
import logging
import sys
import inspect
import struct
import datetime
import re
import shutil
from pathlib import Path
current_dir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


class model:
    def __init__(self, Data, __GLOBAL_THREADHOLD__):
        self.Data = Data
        self.serviceGroup = self.Data.data.service_group
        self.deviceID = self.Data.data.deviceID
        self.__GLOBAL_THREADHOLD__ = __GLOBAL_THREADHOLD__
        self.__SENSORDIR__ = (
            os.path.dirname(os.path.abspath(__file__))
            + "/../../Data/IoT/"
            + self.serviceGroup
            + "/"
            + self.deviceID
            + "/"
        )
        self.__WORKDIR__ = self.__SENSORDIR__ + "HTM/"
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
            if self.Data.static_attributes.savePeriod < 0:
                self.isSavePeriod = False
            elif timePeriod >= self.Data.static_attributes.savePeriod:
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
        if os.path.isfile(self.__SENSORDIR__+"localdata.tmp"):
            pass
        else:
            try:
                data = dataAccessor.queFromCratedbNewest(self.Data.data.entityID, int(self.Data.data.metadata["TrainLimit"]))

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

        swarm = subprocess.Popen(
            ["/usr/bin/python2.7", self.__WORKDIR__ + "swarm.py"],
            #stdout=subprocess.DEVNULL,
            #stderr=subprocess.DEVNULL
        )
        swarmpid = swarm.pid
        logging.info("{service_group}/{deviceID} HTM Pretrain Start PID {pid}".format(
            service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID, pid=swarmpid))
        Path(self.__WORKDIR__ +
             "HTM-{pid}.pid".format(pid=swarmpid)).touch()
        while True:
            state = swarm.poll()
            if state != None:
                logging.info("{service_group}/{deviceID} HTM Pretrain End PID {pid} Exit Code {exitc}".format(
                    service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID, pid=swarmpid, exitc=state))
                os.unlink(self.__WORKDIR__ +
                          "HTM-{pid}.pid".format(pid=swarmpid))
                break
            time.sleep(1)
        if state != 0:
            raise RuntimeError

    def Train(self):

        train = subprocess.Popen(["python2.7", self.__WORKDIR__+"train.py"])
        trainpid = train.pid
        logging.info("{service_group}/{deviceID} HTM Train Start PID {pid}".format(
            service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID, pid=trainpid))
        Path(self.__WORKDIR__ +
             "HTM-{pid}.pid".format(pid=trainpid)).touch()
        while True:
            state = train.poll()
            if state != None:
                logging.info("{service_group}/{deviceID} HTM Train End PID {pid} Exit Code {exitc}".format(
                    service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID, pid=trainpid, exitc=state))
                os.unlink(self.__WORKDIR__ +
                          "HTM-{pid}.pid".format(pid=trainpid))
                break
            time.sleep(1)
        if state != 0:
            raise RuntimeError

        self.TrainOutput = self.__SENSORDIR__+"trainoutput.csv"

    def TrainCleanup(self):
        dataAccessor.trainoutputWriteback(self.TrainOutput, self.Data,
                                          self.__GLOBAL_THREADHOLD__)
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
            modelPID = self.MODELP.pid
            Path(self.__WORKDIR__ +
                 "HTM-{pid}.pid".format(pid=modelPID)).touch()
            logging.info("{service_group}/{deviceID} HTM Start PID {pid}".format(
                service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID, pid=modelPID))
            self.MODELP.wait()
            logging.info("{service_group}/{deviceID} HTM End PID {pid}".format(
                service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID, pid=modelPID))
            os._exit(0)
        else:
            logging.info("{service_group}/{deviceID} HTM Model Loading Start".format(
                service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID))
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
                logging.info("{service_group}/{deviceID} HTM Model Loading Done".format(
                    service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID))
                self.isOnline = True
            else:
                raise IOError

    def Save(self):
        writer = os.open(self.__WORKDIR__+"input.pipe",
                         os.O_WRONLY | os.O_NONBLOCK)
        msg = "SAVE"
        msg = self.__create_msg__(msg.encode("utf8"))
        os.write(writer, msg)
        time.sleep(1)  # Let Model Can Read Msg
        os.close(writer)

    def Recovery(self):
        recoverypid = os.getpid()
        Path(self.__WORKDIR__ +
             "HTM-{pid}.pid".format(pid=recoverypid)).touch()

        with open(self.__WORKDIR__+"localnewest.tmp", "r") as f:
            data = f.read().split(",")[1]
        lastRecordedTime = datetime.datetime.strptime(
            data, "%Y-%m-%d %H:%M:%S")

        try:
            currentTime = self.Data.data.timestamp
            currentValue = self.Data.data.value
        except:
            data = dataAccessor.queFromCratedbNewest(self.Data.data.entityID, 1)[0]
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

        logging.info("{service_group}/{deviceID} HTM Pre-Cleanup Start".format(
            service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID))
        try:
            self.__ReLoopPreUnsavedData__(currentTime, lastRecordedTime)
        except:
            print("Here")
        time.sleep(1)
        timestamp, value, anomalyScore, anomalyFlag, metadata = self.Use(
            currentValue, currentTime)
        dataAccessor.resultWriteback(
            timestamp, value, anomalyScore, anomalyFlag, metadata, self.Data)

        time.sleep(1)
        logging.info("{service_group}/{deviceID} HTM Post-Cleanup Start".format(
            service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID))
        try:
            self.__CleanupPostUnprocessData__(currentTime)
        except:
            print("Here2")
        os.unlink(self.__WORKDIR__ +
                  "HTM-{pid}.pid".format(pid=recoverypid))

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
                os.unlink(self.__WORKDIR__+pidfile[pid])
            except ProcessLookupError:
                pass
            finally:
                logging.info("{service_group}/{deviceID} HTM Kill PID {pid}".format(
                    service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID, pid=pid))
        Path(self.__WORKDIR__+"modelInactive").touch()
        self.isOnline = False

    def Use(self, value, timestamp):
        pid = str(os.getpid())
        writer = os.open(self.__WORKDIR__+"input.pipe",
                         os.O_WRONLY | os.O_NONBLOCK)

        msg = str(value)+","+str(timestamp)+","+pid
        msg = self.__create_msg__(msg.encode("utf8"))
        os.mkfifo(self.__WORKDIR__+pid)
        os.write(writer, msg)
        reader = os.open(self.__WORKDIR__+pid, os.O_RDONLY)
        result = self.__get_message__(reader)
        os.close(writer)
        os.close(reader)
        os.unlink(self.__WORKDIR__+pid)
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
        anomalyFlag = self.__anomaly_detector__(
            logAnomalyLikelihood, value, self.__GLOBAL_THREADHOLD__)
        return timestamp, value, logAnomalyLikelihood, anomalyFlag, {"rawanomalyScore": anomalyScore, "rawanomalyLikelihood": anomalyLikelihood, "predictionValue": predictionValue}

    def Reset(self):
        try:
            self.Sleep()
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
        try:
            self.Sleep()
            shutil.rmtree(self.__WORKDIR__)
        except:
            pass
        self.isExist = False
        self.isTrained = False

    def __anomaly_detector__(self, score, value, threshold, SPATIAL_TOLERANCE=0.05, windowSize=12):
        return False
        pass

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
            self.Data.data.entityID, StartTime, EndTime)
        for record in result:
            time.sleep(1)
            INvalue = record["count"]
            timestampint = record["timestamp"]
            INtimestamp = (datetime.timedelta(
                seconds=timestampint/1000)+datetime.datetime(1970, 1, 1))
            timestamp, value, anomalyScore, anomalyFlag, metadata = self.Use(
                INvalue, INtimestamp)
            if record["anomalyflag"] == None:
                dataAccessor.resultWriteback(
                    timestamp, value, anomalyScore, anomalyFlag, metadata, self.Data)
        logging.info("{service_group}/{deviceID} HTM Pre-Cleanup Done".format(
            service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID))

    def __CleanupPostUnprocessData__(self, StartTime):
        result = dataAccessor.queFromCratedbBack(
            self.Data.data.entityID, StartTime)
        if result == []:
            logging.info("{service_group}/{deviceID} HTM Post-Cleanup Done".format(
                service_group=self.Data.data.service_group, deviceID=self.Data.data.deviceID))
            return 0
        for record in result:

            time.sleep(1)
            INvalue = record["count"]
            timestampint = record["timestamp"]
            INtimestamp = (datetime.timedelta(
                seconds=timestampint/1000)+datetime.datetime(1970, 1, 1))
            timestamp, value, anomalyScore, anomalyFlag, metadata = self.Use(
                INvalue, INtimestamp)
            dataAccessor.resultWriteback(
                timestamp, value, anomalyScore, anomalyFlag, metadata, self.Data)
        return self.__CleanupPostUnprocessData__(INtimestamp)
