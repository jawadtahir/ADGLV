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
        file = logging.FileHandler("app.log")
        file.setLevel(logging.DEBUG)
        self._log.addHandler(file)

        self._log.debug('Reading config YAML')
        config = yaml.load(open(self.config_yaml_path, "r"))
        #config = obj(config)

        nodes = config[NODES_YAML_PATH]

        nodes = yaml.load(open(nodes, "r"))
        #nodes = obj(nodes)

        pipeline = TestPipelineQ()
        pipeline.config = config
        pipeline.nodes = nodes[NODES_LIST]

        pipeline.execute()


if __name__ == "__main__":
    project_root = Path(
        __file__).parent.parent.parent.parent.parent.absolute()
    os.environ[GLV_TOOL_ROOT] = str(project_root)
    config_path = os.path.join(project_root, "config", "config.yaml")
    GLVTool(config_path).execute_pipeline()
