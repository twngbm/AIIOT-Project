import csv
import datetime
import os
import json
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.data.inference_shifter import InferenceShifter
from nupic.algorithms import anomaly_likelihood
__PATH__ = os.path.dirname(os.path.abspath(__file__))
import pickle


with open(__PATH__ + "/../trainoutput.csv", "w+") as opt:
    opt.write(
        "timestamp,value,prediction,anomaly_score,anomaly_likelihood,Log_anomaly_likelihood\n")
    opt.close()

with open(__PATH__+"/model_params", "r") as md:
    modelParams = json.load(md)
model = ModelFactory.create(modelConfig=modelParams["modelConfig"])
model.enableInference(modelParams["inferenceArgs"])

with open(__PATH__+"/../localdata.tmp", "r") as f:
    l = f.readlines()
dataAmount = len(l)-103
if dataAmount <= 0:
    dataAmount = 288

with open(__PATH__+"/../device.cfg", "r") as f:
    devicecfg = json.load(f)
timeResolution = int(devicecfg["static_attributes"]["timeResolution"])

anomalyLikelihoodHelper = anomaly_likelihood.AnomalyLikelihood(
    learningPeriod=dataAmount, historicWindowSize=int(2592000/timeResolution), reestimationPeriod=50)

shifter = InferenceShifter()
with open(__PATH__ + "/../localdata.tmp", "r") as filein:
    reader = csv.reader(filein)
    headers = reader.next()
    reader.next()
    reader.next()
    for record in reader:
        modelInput = dict(zip(headers, record))
        value = float(modelInput["value"])
        modelInput["c1"] = value
        modelInput["c0"] = datetime.datetime.strptime(
            modelInput["timestamp"], "%Y-%m-%d %H:%M:%S"
        )

        result = model.run(modelInput)

        result = shifter.shift(result)

        timestamp = result.rawInput["c0"]
        value = result.rawInput["c1"]
        prediction = result.inferences['multiStepBestPredictions'][
            1] if result.inferences['multiStepBestPredictions'][1] != None else value
        anomalyScore = result.inferences["anomalyScore"]
        anomalyLikelihood = anomalyLikelihoodHelper.anomalyProbability(
            value, anomalyScore, timestamp)
        Log_anomaly_likelihood = anomalyLikelihoodHelper.computeLogLikelihood(
            anomalyLikelihood)
        with open(__PATH__+"/../trainoutput.csv", "a") as op:
            op.write(str(timestamp)+","+str(value)+","+str(prediction)+","+str(anomalyScore) +
                     ","+str(anomalyLikelihood)+","+str(Log_anomaly_likelihood)+"\n")
            op.close()
    model.save(__PATH__+"/HTMmodel")
    with open(__PATH__+"/HTMmodel/anomalyhelper.pkl", "w+") as f:
        pickle.dump(anomalyLikelihoodHelper, f)
        f.close()
    with open(__PATH__+"/HTMmodel/shifthelper.pkl", "w+") as f:
        pickle.dump(shifter, f)
        f.close()
