'''
Created on Aug 15, 2019

@author: foobar
'''
import os

from de.tum.measurement.auth_delta import ssh_connect_to_node
from de.tum.measurement.pinger import pinger
from de.tum.pipeline.models import Pipeline
from de.tum.steps.data_collection import DataCollectionStep
from de.tum.steps.data_collection_with_ques import DataCollectionStepQ
from de.tum.util.Constants import NODES_YAML_PATH


class TestPipeline(Pipeline):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super().__init__(None, None, None)
        data_collection_fns = [ssh_connect_to_node, pinger]
        self.steps = [DataCollectionStep(
            "data_collection_step", data_collection_fns)]


class TestPipelineQ(Pipeline):
    def __init__(self):
        super().__init__(None, None, None)
        self.steps = [DataCollectionStepQ(
            "data_collection_step_queue", os.environ.get(NODES_YAML_PATH, str(os.path.join("/ADGLV", "config", "nodes.yaml"))))]
