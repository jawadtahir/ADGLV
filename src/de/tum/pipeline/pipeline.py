'''
Created on Aug 15, 2019

@author: foobar
'''

from de.tum.measurement.auth_delta import ssh_connect_to_node
from de.tum.measurement.pinger import pinger
from de.tum.pipeline.models import Pipeline
from de.tum.steps.data_collection import DataCollectionStep
from de.tum.steps.data_collection_with_ques import DataCollectionStepQ
from de.tum.steps.feature_vector_generation import FeatureVectorGeneration
from de.tum.steps.pre_visualization import PreVisualization
from de.tum.steps.prediction import DNNPredictor
from de.tum.steps.training import ADGLVDNNClassifier


class TestPipelineQ(Pipeline):
    def __init__(self):
        super().__init__(None, None, None)
        self.steps = [DataCollectionStepQ()]


class FeatureGenPipeline(Pipeline):
    def __init__(self, ts):
        super().__init__(None, None, None)
        self.steps = [FeatureVectorGeneration(ts)]


class DNNOnly(Pipeline):
    def __init__(self, ts):
        Pipeline.__init__(self, None, None, None)
        self.steps = [
            ADGLVDNNClassifier(ts)
        ]


class Predictor(Pipeline):
    def __init__(self, ts):
        Pipeline.__init__(self, None, None, None)
        self.steps = [
            DNNPredictor(ts)
        ]


class ExDNN(Pipeline):
    def __init__(self, ts):
        Pipeline.__init__(self, None, None, None)
        self.steps = [
            FeatureVectorGeneration(ts),
            ADGLVDNNClassifier(ts)
        ]


class ExPredictor(Pipeline):
    def __init__(self, ts):
        Pipeline.__init__(self, None, None, None)
        self.steps = [
            FeatureVectorGeneration(ts),
            DNNPredictor(ts)
        ]


class ExDNNPredictor(Pipeline):
    def __init__(self, ts):
        Pipeline.__init__(self, None, None, None)
        self.steps = [
            FeatureVectorGeneration(ts),
            ADGLVDNNClassifier(ts),
            DNNPredictor(ts)
        ]


class VizPip(Pipeline):
    def __init__(self):
        Pipeline.__init__(self, None, None, None)
        self.steps = [
            PreVisualization()]
