'''
Created on Aug 15, 2019

@author: foobar
'''
import logging
import os
from pathlib import Path
import sys

import yaml

from de.tum.util.Constants import *
from de.tum.util.utils import get_logger
from pipeline import TestPipelineQ


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
        pipeline = TestPipelineQ()

        self._log.debug('Executing pipeline')
        pipeline.execute()
