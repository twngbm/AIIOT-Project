import os
import json
import multiprocessing
from nupic.frameworks.opf import model
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.algorithms import anomaly_likelihood
import cPickle as pickle
import struct
import select


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
reader=os.open(__PATH__+"/input.pipe",os.O_RDONLY|os.O_NONBLOCK)
poll=select.poll()
poll.register(reader,select.POLLIN)
print("Model Ready")

while True:
    if (reader,select.POLLIN) in poll.poll():
        msg=get_message(reader)
    else:
        continue
    print("MODEL GET MSG:",msg)
    if msg=="SAVE":
        #TODO:Save Model
        continue
    elif msg=="STOP":
        #TODO:Stop and Save Model
        continue
    
    msg=msg.split(",")
    modelInput={"value":float(msg[0])}
    timestamp=msg[1]
    
    modelInput["timestamp"]=timestamp
    result=model.run(modelInput)

    value = result.rawInput["value"]
    timestamp = result.rawInput["timestamp"]
    prediction = result.inferences['multiStepBestPredictions'][
        1] if result.inferences['multiStepBestPredictions'][1] != None else value
    anomalyScore = result.inferences["anomalyScore"]
    anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(
        value, anomalyScore, timestamp)
    Log_anomaly_likelihood = anomalyLikelihoodHelper.computeLogLikelihood(
        anomalyLikelihood)

    writer=os.open(__PATH__+"/output.pipe",os.O_WRONLY)
    msg=create_msg(str([value,prediction,anomalyScore,anomalyLikelihood,Log_anomaly_likelihood]).encode("utf8"))
    os.write(writer,msg)
    os.close(writer)
    
