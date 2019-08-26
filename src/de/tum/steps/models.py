'''
Created on Aug 15, 2019

@author: foobar
'''
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from de.tum.models import Config


class Step(ABC):
    '''
    classdocs
    '''

    def __init__(self, name, *vargs, **kwargs):
        '''
        Constructor
        '''
        self.name = name
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.log = logging.getLogger(__name__)

    def pre_work(self):
        pass

    def pre_check(self):
        pass

    @abstractmethod
    def work(self, config: Config, **kwargs):
        raise NotImplementedError(self.name + " has no work")

    def post_work(self):
        pass

    def post_check(self):
        pass

    def get_name(self):
        return self.name


class CollectionTaskMessage():
    def __init__(self, request_node_id: str, request_time: datetime, target_node_name: str, target_node_addr: str, target_node_pkey_path: str=None, target_node_pkey_passphrase: str=None):
        self.request_node_id = request_node_id
        self.request_time = request_time
        self.target_node_name = target_node_name
        self.target_node_addr = target_node_addr
        self.target_node_pkey_path = target_node_pkey_path
        self.target_node_pkey_passphrase = target_node_pkey_passphrase
