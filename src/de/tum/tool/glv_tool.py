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
from pipeline import TestPipeline, TestPipelineQ


class GLVTool(object):
    '''
    classdocs
    '''

    def __init__(self, config_yaml_path):
        '''
        Constructor
        '''
        self.config_yaml_path = config_yaml_path
        self._log = logging.getLogger(__name__)

    def execute_pipeline(self):
        self._log.debug('Reading config YAML')
        config = yaml.load(open(self.config_yaml_path, "r"))

        nodes = config[NODES_YAML_PATH]

        self._log.debug('Reading nodes YAML')
        nodes = yaml.load(open(nodes, "r"))

        self._log.debug('Creating pipeline')
        pipeline = TestPipelineQ()
        pipeline.config = config
        pipeline.nodes = nodes[NODES_LIST]

        self._log.debug('Executing pipeline')
        pipeline.execute()
