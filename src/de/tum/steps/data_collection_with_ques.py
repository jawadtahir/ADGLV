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


SSH_PORT = 22


class WorkerCallback(ABC):
    def __init__(self):
        self._log = get_logger(__name__)

    @abstractmethod
    def callback_function(self, ch, method, properties, body):
        pass


class SSHCallback(WorkerCallback):

    def __init__(self, mongo_host: str, mongo_port: int, database: str, collection: str):
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.database = database
        self.collection = collection
        self._log = get_logger(__name__)

    def callback_function(self, ch, method, properties, body):
        body = body.decode("utf8")
        body = json.loads(body)
        body = CollectionTaskMessage(**body)

        try:
            measurement = ssh_connect_to_node(body.request_node_id, body.request_time, body.target_node_name, body.target_node_addr, body.target_node_port,
                                              body.target_node_pkey_path, body.target_node_pkey_passphrase)

            with MongoClient(self.mongo_host, self.mongo_port) as db_client:
                db = db_client[self.database]
                collection = db[self.collection]
                collection.insert(vars(measurement))
        except:
            print_exc()
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self._log.debug('SSH stored')


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

    def __init__(self):
        '''
        Constructor
        '''
        super().__init__("data_collection_step")
        self._log = get_logger(__name__)

    def work(self, **kwargs):
        # Getting environment variables
        self.nodes = os.environ.get(
            NODES_YAML_PATH, os.path.join("/ADGLV", "configs", "nodes.yaml"))
        self._log.debug("Nodes yaml path: " + self.nodes)
        self._log.debug('Reading nodes YAML')
        self.nodes = yaml.load(open(self.nodes, "r"))
        self.nodes = self.nodes[NODES_LIST]

        self.relayed_nodes = os.environ.get(RELAYED_NODES, None)
        if self.relayed_nodes is not None:
            self.relayed_nodes = [x.strip().upper()
                                  for x in self.relayed_nodes.split(",")]
        else:
            self.relayed_nodes = []
        self._log.debug("Relayed nodes: " + str(self.relayed_nodes))

        self.relayed_nodes_port = int(
            os.environ.get(RELAYED_NODES_PORT, 52923))
        self._log.debug("Relayed node port: " + str(self.relayed_nodes_port))

        self.database_name = os.environ.get(DATABASE_NAME, "thesis")
        self._log.debug("Database name: " + self.database_name)

        self.collection = os.environ.get(COLLECTION_NAME, "data_collection")
        self._log.debug("Collection name: " + self.collection)

        self.end_time = os.environ.get(DATA_END_TIME, None)
        if self.end_time is None:
            self.end_time = datetime.max
        else:
            self.end_time = datetime.strptime(
                self.end_time, "%Y-%m-%d %H:%M:%S")
        self._log.debug("Collection end time: " + str(self.end_time))

        self.measure_interval = int(
            os.environ.get(DATA_COLLECTION_INTERVAL, "60"))
        self._log.debug("Measure interval: " + str(self.measure_interval))

        self.node_name = os.environ.get(NODE_NAME, "1337")
        self._log.debug("Node name: " + self.node_name)

        self.thread_count = int(os.environ.get(THREAD_COUNT, os.cpu_count()))
        self._log.debug("Thread count: " + str(self.thread_count))

        self.private_key_path = os.environ.get(NODES_PRIVATE_KEY, str(
            os.path.join(str(Path.home()), ".ssh", "key.pem")))
        self._log.debug("Private key path: " + self.private_key_path)

        self.private_key_passphrase = os.environ.get(
            NODES_PRIVATE_KEY_PASSPHRASE, None)

        self.rabbitmq_host = os.environ.get(RABBITMQ_HOST, "localhost")
        self._log.debug("RabbitMQ host: " + self.rabbitmq_host)

        self.mongo_host = os.environ.get(MONGO_HOST, "localhost")
        self._log.debug("Mongo Host: " + str(self.mongo_host))

        self.mongo_port = os.environ.get(MONGO_PORT, "27017")
        self._log.debug("Mongo Port: " + self.mongo_port)
        self.mongo_port = int(self.mongo_port)

        self._log.debug("Creating measurement workers...")

        self.thread_array = []

        for _ in range(self.thread_count):
            worker_thread = DataCollectionWorker(SSH_DELAY, SSHCallback(
                self.mongo_host, self.mongo_port, self.database_name, self.collection))
            self.thread_array.append(worker_thread)
            worker_thread.start()

        self._log.debug("Creating RabbitMQ connection...")

        try:
            with pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host)) as q_connection:

                channel = q_connection.channel()
                channel.queue_declare(queue=SSH_DELAY, durable=False)

                t_now = datetime.utcnow()
                while (self.end_time - t_now).total_seconds() > 0:
                    t_now = datetime.utcnow()
                    self._log.debug("Publishing at " + str(t_now))
                    for target_node_name, target_node_adrs in self.nodes.items():
                        if not target_node_name.strip().upper() == self.node_name.strip().upper():
                            port = SSH_PORT
                            if target_node_name.strip().upper() in self.relayed_nodes:
                                self._log.debug(
                                    "Relayed node: " + target_node_name)
                                port = self.relayed_nodes_port

                            task_message = CollectionTaskMessage(
                                self.node_name, str(t_now), target_node_name, target_node_adrs, port, self.private_key_path, self.private_key_passphrase)
                            channel.basic_publish(
                                exchange='', routing_key=SSH_DELAY, body=json.dumps(vars(task_message), default=str))

                    self._log.debug("Sleeping...")
                    time.sleep(self.measure_interval)
                    t_now = datetime.utcnow()

                self._log.debug("Measurement finished")
        except:
            print_exc()
