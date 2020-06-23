import os
import json
from nupic.frameworks.opf import model
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.algorithms import anomaly_likelihood
import cPickle as pickle
import struct
import select
import signal
import time
signal.signal(signal.SIGCHLD, signal.SIG_IGN)



def create_msg(content):
    return struct.pack("<I", len(content)) + content

def get_message(fifo):
    """Get a message from the named pipe."""
    msg_size_bytes = os.read(fifo, 4)
    msg_size = struct.unpack("<I", msg_size_bytes)[0]
    msg_content = os.read(fifo, msg_size).decode("utf8")
    return msg_content

__PATH__=os.path.dirname(os.path.abspath(__file__))
try:
    os.mkfifo(__PATH__+"/input.pipe")
    os.mkfifo(__PATH__+"/output.pipe")
except:
    pass

model=ModelFactory.loadFromCheckpoint(__PATH__+"/HTMmodel")
with open(__PATH__+"/HTMmodel/anomalyhelper.pkl","r") as f:
    anomalyLikelihoodHelper=pickle.load(f)
with open(__PATH__+"/HTMmodel/shifthelper.pkl","r") as f:
    shifter=pickle.load(f)
reader=os.open(__PATH__+"/input.pipe",os.O_RDONLY|os.O_NONBLOCK)
poll=select.poll()
poll.register(reader,select.POLLIN)
writer=os.open(__PATH__+"/output.pipe",os.O_WRONLY)
msg=create_msg("ACK".encode("utf8"))
os.write(writer,msg)
os.close(writer)


while True:
    if (reader,select.POLLIN) in poll.poll(500):
        msg=get_message(reader)
    else:
        time.sleep(0.5)
        continue
    if msg=="SAVE":
        pid=os.fork()
        if pid==0:
            if os.path.isfile(__PATH__+"/saving"):
               pass
            else:
                with open(__PATH__+"/saving","w") as saveflag:
                    saveflag.close()
                os.system("cp "+__PATH__+"/../localnewest.tmp "+__PATH__)
                model.save(__PATH__+"/HTMmodel")
                with open(__PATH__+"/HTMmodel/anomalyhelper.pkl","w+") as  f:
                    pickle.dump(anomalyLikelihoodHelper,f)
                    f.close()
                with open(__PATH__+"/HTMmodel/shifthelper.pkl","w+") as  f:
                    pickle.dump(shifter,f)
                    f.close()
                os.unlink(__PATH__+"/saving")
            os._exit(0)
        else:
            continue
    
    msg=msg.split(",")
    modelInput={"value":float(msg[0])}
    timestamp=msg[1]
    pid=msg[2]
    modelInput["timestamp"]=timestamp
    result=model.run(modelInput)
    result=shifter.shift(result)

    value = result.rawInput["value"]
    timestamp = result.rawInput["timestamp"]
    prediction = result.inferences['multiStepBestPredictions'][
        1] if result.inferences['multiStepBestPredictions'][1] != None else value
    anomalyScore = result.inferences["anomalyScore"]
    anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(
        value, anomalyScore, timestamp)
    Log_anomaly_likelihood = anomalyLikelihoodHelper.computeLogLikelihood(
        anomalyLikelihood)
    msg=create_msg(str([prediction,anomalyScore,anomalyLikelihood,Log_anomaly_likelihood]).encode("utf8"))
    writer=os.open(__PATH__+"/"+pid,os.O_WRONLY)
    os.write(writer,msg)
    os.close(writer)
    
