'''
Created on Aug 15, 2019

@author: foobar
'''

import time

from de.tum.pipeline.pipeline import TestPipelineQ, FeatureGenPipeline, DNNOnly,\
    ExDNN, VizPip, Predictor, ExPredictor, ExDNNPredictor
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger


class GLVTool(object):
    '''
    classdocs
    '''

    def __init__(self, phase, timestamp):
        '''
        Constructor
        '''
        self._log = get_logger(__name__)
        self.phase = phase
        self.timestamp = timestamp

    def execute_pipeline(self):
        pipeline = None
        self._log.debug("Phase: " + self.phase)
        self._log.debug('Creating pipeline...')

        if self.phase == PHASE_DATA_COLLECTION:
            pipeline = TestPipelineQ()
            # wait for rabbbitMQ service to set up (Dirty hack)
            time.sleep(10)

        elif self.phase == PHASE_FEAT_GENERATION:
            pipeline = FeatureGenPipeline(self.timestamp)

        elif self.phase == PHASE_TRAIN_MODEL:
            pipeline = DNNOnly(self.timestamp)

        elif self.phase == PHASE_PREDICTION:
            pipeline = Predictor(self.timestamp)

        elif self.phase == PHASE_FEAT_TRAIN:
            pipeline = ExDNN(self.timestamp)

        elif self.phase == PHASE_FEAT_PREDICT:
            pipeline = ExPredictor(self.timestamp)

        elif self.phase == PHASE_FTP:
            pipeline = ExDNNPredictor(self.timestamp)

        else:
            pipeline = ExDNNPredictor(self.timestamp)

        self._log.debug('Executing pipeline')
        pipeline.execute()
