'''
Created on Aug 15, 2019

@author: foobar
'''
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
import time

from pymongo import MongoClient

from de.tum.steps.models import Step
from de.tum.util.Constants import *


class DataCollectionStep(Step):
    '''
    classdocs
    '''

    def __init__(self, name, fns):
        '''
        Constructor
        '''
        super().__init__(name)
        self.fns = fns
        self.db_client = None

    def __del__(self):
        if self.db_client:
            self.db_client.close()

    def work(self, config, **kwargs):
        nodes = kwargs['nodes']

        end_time = datetime.max if config.get(
            DATA_END_TIME) is None else config[DATA_END_TIME]
        measure_interval = 60 if config.get(
            DATA_COLLECTION_INTERVAL) is None else config[DATA_COLLECTION_INTERVAL]
        node_name = "1337" if config.get(
            NODE_NAME) is None else config[NODE_NAME]

        with MongoClient(config[MONGO_HOST], config[MONGO_PORT])["thesis"] as db:
            collection = db['data_collection']

            self.log.debug("Executing work")
            with ThreadPoolExecutor() as executer:
                t_now = datetime.now()
                while (end_time - t_now).total_seconds() > 0:
                    futures = []
                    datae = []
                    t_now = datetime.now()
                    for node_name, node_adrs in nodes.items():
                        for fn in self.fns:
                            fs = executer.submit(
                                fn, node_name=node_name, t_now=t_now, node_adrs=node_adrs, private_key=config.nodes_private_key, passphrase=config.nodes_private_key_passphrase)
                            futures.append(fs)

                    for fs in as_completed(futures):
                        data_obj = fs.result()
                        datae.append(vars(data_obj))

                    collection.insert_many(datae)
                    time.sleep(measure_interval)

                    t_now = datetime.now()
