'''
Created on Aug 15, 2019

@author: foobar
'''
from de.tum.util.utils import get_logger


class Pipeline(object):
    '''
    classdocs
    '''

    def __init__(self, steps, config, nodes):
        '''
        Constructor
        '''
        self.steps = steps
        self.config = config
        self.nodes = nodes
        self.log = get_logger(__name__)

    def execute(self):
        self.log.debug("Executing test_pipeline steps...")
        for step in self.steps:
            self.log.debug("Step : " + step.get_name())

            self.log.debug("Pre-Work...")
            step.pre_work()

            self.log.debug("Pre-Check...")
            step.pre_check()

            self.log.debug("Work...")
            step.work(self.config, nodes=self.nodes)

            self.log.debug("Post-Work...")
            step.post_work()

            self.log.debug("Post-Check...")
            step.post_check()
