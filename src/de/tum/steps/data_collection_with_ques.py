'''
Created on Aug 15, 2019

@author: foobar
'''
from abc import ABC, abstractmethod
from datetime import datetime
import json
import os
from pathlib import Path
from threading import Thread
import time
from traceback import print_exc

import pika
from pymongo import MongoClient
import yaml

from de.tum.measurement.auth_delta import ssh_connect_to_node
from de.tum.measurement.pinger import pinger
from de.tum.steps.models import Step, CollectionTaskMessage
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger


class WorkerCallback(ABC):
    def __init__(self):
        self._log = get_logger(__name__)

    @abstractmethod
    def callback_function(self, ch, method, properties, body):
        pass


class SSHCallback(WorkerCallback):

    def callback_function(self, ch, method, properties, body):
        body = body.decode("utf8")
        body = json.loads(body)
        body = CollectionTaskMessage(**body)

        try:
            measurement = ssh_connect_to_node(body.request_node_id, body.request_time, body.target_node_addr,
                                              body.target_node_pkey_path, body.target_node_pkey_passphrase)

            with MongoClient(os.environ.get(MONGO_HOST, "localhost"), int(os.environ.get(MONGO_PORT, "27017"))) as db_client:
                db = db_client['thesis']
                collection = db['data_collection']
                collection.insert(vars(measurement))
        except:
            print_exc()
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self._log.debug('SSH stored')


class MTRCallback(WorkerCallback):

    def callback_function(self, ch, method, properties, body):
        body = body.decode("utf8")
        body = json.loads(body)
        body = CollectionTaskMessage(**body)

        try:
            measurement = pinger(body.request_node_id,
                                 body.request_time, body.target_node_addr)

            with MongoClient(os.environ.get(MONGO_HOST, "localhost"), int(os.environ.get(MONGO_PORT, "27017"))) as db_client:
                db = db_client['thesis']
                collection = db['data_collection']
                collection.insert(vars(measurement))
        except:
            print_exc()
        finally:
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

        rabbitmq_host = os.environ.get(RABBITMQ_HOST, "localhost")

        with pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host)) as q_connection:

            channel = q_connection.channel()
            channel.queue_declare(queue=self.collectoin_type)
            channel.basic_consume(
                queue=self.collectoin_type, auto_ack=False, on_message_callback=self.collection_callback.callback_function)
            channel.start_consuming()


class DataCollectionStepQ(Step):
    '''
    classdocs
    '''

    def __init__(self, name, nodes):
        '''
        Constructor
        '''
        super().__init__(name)
        self._log = get_logger(__name__)
        self.nodes = nodes

    def work(self, **kwargs):

        end_time = os.environ.get(DATA_END_TIME, datetime.max)

        measure_interval = int(os.environ.get(DATA_COLLECTION_INTERVAL, "60"))

        node_name = os.environ.get(NODE_NAME, "1337")

        thread_count = int(os.environ.get(THREAD_COUNT, os.cpu_count()))

        private_key_path = os.environ.get(NODES_PRIVATE_KEY, str(
            os.path.join(str(Path.home()), ".ssh", "key.pem")))

        private_key_passphrase = os.environ.get(
            NODES_PRIVATE_KEY_PASSPHRASE, None)

        rabbitmq_host = os.environ.get(RABBITMQ_HOST, "localhost")

        self._log.debug('Reading nodes YAML')
        self.nodes = yaml.load(open(self.nodes, "r"))
        self.nodes = self.nodes[NODES_LIST]

        self._log.debug("Creating measurement workers...")

        self.thread_array = []

        for _ in range(thread_count):
            worker_thread = DataCollectionWorker(SSH_DELAY, SSHCallback())
            self.thread_array.append(worker_thread)
            worker_thread.start()

        self._log.debug("Creating RabbitMQ connection...")

        try:
            with pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host)) as q_connection:

                channel = q_connection.channel()
                channel.queue_declare(queue=SSH_DELAY, durable=False)

                t_now = datetime.utcnow()
                while (end_time - t_now).total_seconds() > 0:
                    t_now = datetime.utcnow()
                    self._log.debug("Publishing at " + str(t_now))
                    for target_node_name, target_node_adrs in self.nodes.items():
                        if not target_node_name.strip().lower() == node_name.strip().lower():
                            task_message = CollectionTaskMessage(
                                node_name, str(t_now), target_node_name, target_node_adrs, private_key_path, private_key_passphrase)
                            channel.basic_publish(
                                exchange='', routing_key=SSH_DELAY, body=json.dumps(vars(task_message), default=str))

                    self._log.debug("Sleeping...")
                    time.sleep(measure_interval)
                    t_now = datetime.utcnow()

                self._log.debug("Measurement finished")
        except:
            print_exc()
