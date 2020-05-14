import os
import subprocess
import json
import time
import logging
import select
import struct
class model:
    def __init__(self, Data):
        self.Data = Data
        self.fiware_service = self.Data.data.fiware_service
        self.deviceID = self.Data.data.deviceID
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

    def Prepare(self):
        startTime=time.time()
        print("Start Prepare at:",startTime)
        self.__REPOPATH__ = os.path.dirname(os.path.abspath(__file__))
        p = subprocess.Popen(
            ["cp", "-r", self.__REPOPATH__ + "/HTM", self.__SENSORDIR__]
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
            "file://../Data/IoT/"
            + self.Data.data.fiware_service
            + "/"
            + self.Data.data.deviceID
            + "/"
            + "localdata.tmp"
        )
        with open(self.__WORKDIR__ + "search_def.json", "w") as f:
            json.dump(swarm_config, f)
        swarm = subprocess.Popen(
            ["/usr/bin/python2.7", self.__WORKDIR__ + "swarm.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        while True:
            state=swarm.poll()
            if state!=None:
                print("Exist Code:",state)
                break
            time.sleep(30)
            print("Swarming")
        if state!=0:
            raise RuntimeError
        os.unlink(self.__WORKDIR__+"permutations.py")
        os.unlink(self.__WORKDIR__+"description.py")
        os.unlink(self.__WORKDIR__+"description.pyc")
        os.unlink(self.__WORKDIR__+"default_Report.csv")
        subprocess.Popen(["rm",self.__WORKDIR__+"default_HyperSearchJobID.pkl"])
        subprocess.Popen(["mv",self.__WORKDIR__+"model_0/model_params.py" ,self.__WORKDIR__])
        subprocess.Popen(["rm","-r",self.__WORKDIR__+"model_0"])
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
            time.sleep(30)
            print("Training")
        if state!=0:
            raise RuntimeError
        finishTime=time.time()
        self.TrainOutput=self.__SENSORDIR__+"trainoutput.csv"
        print("Train finish at:",finishTime)
        print("Take total:",int(finishTime-startTime)," seconds")

    def TrainCleanup(self):
        startTime=time.time()
        print("Start TrainCleanup at:",startTime)

        os.unlink(self.__SENSORDIR__+"trainoutput.csv")

        finishTime=time.time()
        print("TrainCleanup finish at:",finishTime)
        print("Take total:",int(finishTime-startTime)," seconds")


    def Online(self):
        print("Start model")
        pid=os.fork()
        if pid==0:
            p=subprocess.Popen(["python2.7",self.__WORKDIR__+"model.py"])
            p.wait()
            print("MODEL STOP")
        else:
            print("Wait 15 Second for model to be ready")
            time.sleep(15)
            print("Wait End.")
            self.isOnline=True
            

    def Stop(self):
        raise NotImplementedError

    def Save(self):
        raise NotImplementedError

    def Use(self):
        print("USE")
        writer=os.open(self.__WORKDIR__+"input.pipe",os.O_WRONLY|os.O_NONBLOCK)
        
        
        msg=str(self.Data.data.value)+","+str(self.Data.data.timestamp)
        msg=self.__create_msg__(msg.encode("utf8"))
        os.write(writer,msg)
        reader=os.open(self.__WORKDIR__+"output.pipe",os.O_RDONLY)
        msg=self.__get_message__(reader)
        os.close(writer)
        os.close(reader)
        return msg
       

            
        


    def Clean(self):
        raise NotImplementedError
    
    def __create_msg__(self,content: bytes) -> bytes:
        return struct.pack("<I", len(content)) + content

    def __get_message__(self,fifo: int) -> str:
        msg_size_bytes = os.read(fifo, 4)
        msg_size = struct.unpack("<I", msg_size_bytes)[0]
        msg_content = os.read(fifo, msg_size).decode("utf8")
        return msg_content