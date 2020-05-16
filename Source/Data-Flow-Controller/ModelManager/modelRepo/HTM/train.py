import csv
import datetime
import os
import json
import model_params
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.data.inference_shifter import InferenceShifter
from nupic.algorithms import anomaly_likelihood
__PATH__ = os.path.dirname(os.path.abspath(__file__))
import pickle

with open(__PATH__ + "/search_def.json", "r") as f:
    swarm_config = json.loads(f.read())
    dataType = swarm_config["includedFields"][0]["fieldType"]
with open(__PATH__ + "/../trainoutput.csv", "w+") as opt:
    opt.write(
        "timestamp,value,prediction,anomaly_score,anomaly_likelihood,Log_anomaly_likelihood\n")
    opt.close()
model = ModelFactory.create(model_params.MODEL_PARAMS)
model.enableInference({"predictedField": "value"})
anomalyLikelihoodHelper = anomaly_likelihood.AnomalyLikelihood()
shifter = InferenceShifter()
with open(__PATH__ + "/../localdata.tmp", "r") as filein:
    reader = csv.reader(filein)
    headers = reader.next()
    reader.next()
    reader.next()
    for record in reader:
        modelInput = dict(zip(headers, record))
        if dataType == "float":
            value = float(modelInput["value"])
        elif dataType == "int":
            value = int(modelInput["value"])
        elif dataType == "bool":
            value = True if modelInput["value"] in [
                "True", "true", "1"] else False
        elif dataType == "string":
            value = modelInput["value"]

        modelInput["value"] = value
        modelInput["timestamp"] = datetime.datetime.strptime(
            modelInput["timestamp"], "%Y-%m-%d %H:%M:%S"
        )

        result = model.run(modelInput)
        
        result = shifter.shift(result)
       
        timestamp = result.rawInput["timestamp"]
        value = result.rawInput["value"]
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
    with open(__PATH__+"/HTMmodel/anomalyhelper.pkl","w+") as  f:
        pickle.dump(anomalyLikelihoodHelper,f)
        f.close()
    with open(__PATH__+"/HTMmodel/shifthelper.pkl","w+") as  f:
        pickle.dump(shifter,f)
        f.close()
    
    """
    ModelResult(    predictionNumber=0
    rawInput={'timestamp': datetime.datetime(2014, 5, 14, 1, 14), 'value': 85.835}
    
    inferences={'multiStepPredictions': {1: {85.835: 1.0}}, 
    'multiStepBucketLikelihoods': {1: {0: 1.0}}, 
    'multiStepBestPredictions': {1: 85.835}, 
    'anomalyLabel': '[]', 'anomalyScore': 1.0}
    metrics=None
    predictedFieldIdx=0
    predictedFieldName=value
    classifierInput=ClassifierInput(        dataRow=85.835
    bucketIndex=0
    )
    )      
    """

