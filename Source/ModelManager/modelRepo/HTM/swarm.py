# -*- coding: utf-8 -*-
# python2.7
import json
import sys
import os
from nupic.swarming import permutations_runner
import logging
import multiprocessing

logging.basicConfig()


def readConfig(__PATH__):
    with open(__PATH__ + "/search_def.json", "r") as f:
        swarm_config = json.loads(f.read())
    return swarm_config


if __name__ == "__main__":
    cpuCount=int(multiprocessing.cpu_count())
    __PATH__ = os.path.dirname(os.path.abspath(__file__))
    swarm_config = readConfig(__PATH__)
    model_params = permutations_runner.runWithConfig(
        swarm_config,
        {"maxWorkers": cpuCount, "overwrite": True},
        outDir=__PATH__,
        permWorkDir=__PATH__,
    )
