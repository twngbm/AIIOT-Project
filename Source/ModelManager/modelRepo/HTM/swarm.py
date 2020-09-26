# -*- coding: utf-8 -*-
# python2.7
import json
import sys
import os
import csv
import numpy as np
import logging
from nupic.frameworks.opf.common_models.cluster_params import (
  getScalarMetricWithTimeOfDayAnomalyParams)

logging.basicConfig()

if __name__ == "__main__":
    __PATH__ = os.path.dirname(os.path.abspath(__file__))
    with open(__PATH__+"/../localdata.tmp", "r") as filein:
        reader=csv.reader(filein)
        headers = reader.next()
        reader.next()
        reader.next()
        valueList=[]
        try:
            while True:
                record=dict(zip(headers,reader.next()))
                valueList.append(float(record["value"]))
        except:
            pass
        finally:
            
            x=np.array(valueList)
            
            stdVal=np.std(x)
            maxVal=np.max(x)+1.35*stdVal
            minVal=np.min(x)-1.35*stdVal
            if minVal<0:
                minVal=0
            
    modelParams = getScalarMetricWithTimeOfDayAnomalyParams(
          metricData=[0],
          minVal=minVal,
          maxVal=maxVal,
          minResolution=0.001,
          tmImplementation = "cpp")
    modelParams["modelConfig"]['modelParams']["clEnable"]=True
    with open(__PATH__+"/model_params","w") as f:
        json.dump(modelParams,f)

