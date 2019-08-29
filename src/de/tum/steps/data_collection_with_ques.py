'''
Created on Aug 15, 2019

@author: foobar
'''
from abc import ABC, abstractmethod
from datetime import datetime
import json
import os
from threading import Thread
import time

import pika
from pymongo import MongoClient

from de.tum.measurement.auth_delta import ssh_connect_to_node
from de.tum.measurement.pinger import pinger
from de.tum.steps.models import Step, CollectionTaskMessage
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger


class WorkerCallback(ABC):
    def __init__(self, config):
        self.config = config
        self._log = get_logger(__name__)

    @abstractmethod
    def callback_function(self, ch, method, properties, body):
        pass


class SSHCallback(WorkerCallback):

    def callback_function(self, ch, method, properties, body):
        body = body.decode("utf8")
        body = json.loads(body)
        body = CollectionTaskMessage(**body)

        measurement = ssh_connect_to_node(body.request_node_id, body.request_time, body.target_node_addr,
                                          body.target_node_pkey_path, body.target_node_pkey_passphrase)
        with MongoClient(self.config[MONGO_HOST], self.config[MONGO_PORT]) as db_client:
            db = db_client['thesis']
            collection = db['data_collection']
            collection.insert(vars(measurement))

        ch.basic_ack(delivery_tag=method.delivery_tag)
        self._log.debug('SSH stored')


class MTRCallback(WorkerCallback):

    def callback_function(self, ch, method, properties, body):
        body = body.decode("utf8")
        body = json.loads(body)
        body = CollectionTaskMessage(**body)

        measurement = pinger(body.request_node_id,
                             body.request_time, body.target_node_addr)
        with MongoClient(self.config[MONGO_HOST], self.config[MONGO_PORT]) as db_client:
            db = db_client['thesis']
            collection = db['data_collection']
            collection.insert(vars(measurement))

        ch.basic_ack(delivery_tag=method.delivery_tag)
        self._log.debug('MTR stored')


class DataCollectionWorker(Thread):
    def __init__(self, collection_type: str, collection_callback: WorkerCallback=None):
        super().__init__()
        self.collection_callback = collection_callback
        self.collectoin_type = collection_type
        self._log = get_logger(__name__)

    def run(self):
        if self.collection_callback is None:
            self._log.debug('Collection callback not provided')
            raise ValueError('Collection callback not provided')

        with pika.BlockingConnection(pika.ConnectionParameters('localhost')) as q_connection:

            channel = q_connection.channel()
            channel.queue_declare(queue=self.collectoin_type)
            channel.basic_consume(
                queue=self.collectoin_type, auto_ack=False, on_message_callback=self.collection_callback.callback_function)
            channel.start_consuming()


class DataCollectionStepQ(Step):
    '''
    classdocs
    '''

    def __init__(self, name):
        '''
        Constructor
        '''
        super().__init__(name)
        self._log = get_logger(__name__)

    def work(self, config, **kwargs):

        nodes = kwargs['nodes']

        end_time = datetime.max if config.get(
            DATA_END_TIME) is None else config[DATA_END_TIME]
        measure_interval = 60 if config.get(
            DATA_COLLECTION_INTERVAL) is None else config[DATA_COLLECTION_INTERVAL]
        node_name = "1337" if config.get(
            NODE_NAME) is None else config[NODE_NAME]
        thread_count = os.cpu_count() if config.get(
            THREAD_COUNT) is None else config[THREAD_COUNT]

        self._log.debug("Creating measurement workers...")

        for _ in range(thread_count):
            DataCollectionWorker(SSH_DELAY,
                                 SSHCallback(config)).start()
            DataCollectionWorker(MTR_DELAY,
                                 MTRCallback(config)).start()

        self._log.debug("Creating RabbitMQ connection...")

        with pika.BlockingConnection(pika.ConnectionParameters(host='localhost')) as q_connection:

            channel = q_connection.channel()
            channel.queue_declare(queue=MTR_DELAY, durable=False)
            channel.queue_declare(queue=SSH_DELAY, durable=False)

            t_now = datetime.utcnow()
            while (end_time - t_now).total_seconds() > 0:
                t_now = datetime.utcnow()
                self._log.debug("Publishing at " + str(t_now))
                for target_node_name, target_node_adrs in nodes.items():
                    if not target_node_name.strip().lower() == node_name.strip().lower():
                        task_message = CollectionTaskMessage(
                            node_name, str(t_now), target_node_name, target_node_adrs, config[NODES_PRIVATE_KEY], config[NODES_PRIVATE_KEY_PASSPHRASE])

                        channel.basic_publish(
                            exchange='', routing_key=SSH_DELAY, body=json.dumps(vars(task_message), default=str))
                        channel.basic_publish(
                            exchange='', routing_key=MTR_DELAY, body=json.dumps(vars(task_message), default=str))

                self._log.debug("Sleeping...")
                time.sleep(measure_interval)
                t_now = datetime.utcnow()

            self._log.debug("Measurement finished")
