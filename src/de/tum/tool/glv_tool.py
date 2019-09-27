'''
Created on Aug 15, 2019

@author: foobar
'''

from de.tum.pipeline.pipeline import TestPipelineQ, FeatureGenPipeline, DNNOnly,\
    ExDNN
from de.tum.util.utils import get_logger


class GLVTool(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self._log = get_logger(__name__)

    def execute_pipeline(self):

        self._log.debug('Creating pipeline')
        pipeline = ExDNN()

        self._log.debug('Executing pipeline')
        pipeline.execute()
