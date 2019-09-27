'''
Created on Sep 13, 2019

@author: foobar
'''
from datetime import datetime
import os

from pymongo.mongo_client import MongoClient

from de.tum.steps.models import Step
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger
import pandas as pd


class FeatureVectorGeneration(Step):
    def __init__(self, name, node_map):
        super().__init__(name)
        self._log = get_logger(__name__)
        self.node_map = node_map

    def pre_work(self):
        pass

    def work(self, **kwargs):
        # Format YYYY-MM-DD HH:MM
        date_start = os.environ.get(FEATURE_DATA_START, datetime.min)
        self._log.debug("Start date: " + str(date_start))

        # Format YYYY-MM-DD HH:MM
        date_end = os.environ.get(FEATURE_DATA_END, datetime.max)
        self._log.debug("End date: " + str(date_end))

        mongo_host = os.environ.get(MONGO_HOST, "localhost")
        self._log.debug("Mongo Host: " + mongo_host)

        mongo_port = os.environ.get(MONGO_PORT, "27017")
        self._log.debug("Mongo Port: " + mongo_port)

        nodes_to_train = os.environ.get(TRAIN_NODES_CSV)
        self._log.debug("Nodes to train: " + nodes_to_train)

        csv_dir = os.environ.get(
            FEATURE_CSV_DIR, os.path.join("/ADGLV", "data"))
        self._log.debug("CSV Directory: " + csv_dir)

        query_filter = {"m_time": {"$gte": date_start, "$lte": date_end}}

        if nodes_to_train is not None:
            nodes_to_train = nodes_to_train.split(",")
            with MongoClient(mongo_host, int(mongo_port)) as db_client:
                db = db_client['thesis']
                collection = db['data_collection']
                for node in nodes_to_train:
                    ip_adrs = self.node_map.get(node.strip())
                    if ip_adrs is not None:
                        query_filter["dest_name"] = ip_adrs
                        measurments = collection.find(filter=query_filter)
                        time_deltas = []
                        labels = []
                        for measurment in measurments:
                            label = measurment["node_name"].strip()
                            label = label[len(label) - 2:]

                            t3 = measurment["m_val"]["t3"]
                            t5 = measurment["m_val"]["t5"]
                            time_delta = (t5 - t3) * 100
                            time_delta = format(time_delta, ".7f")
                            time_deltas.append(time_delta)
                            labels.append(label)

#                         time_deltas = np.array(time_deltas)
#                         labels = np.array(labels)

                        dataframe = pd.DataFrame(
                            {"time_delta": time_deltas, "label": labels})
                        csv_path = os.path.join(csv_dir, node + ".csv")
                        dataframe.to_csv(csv_path)

                    else:
                        self._log.debug("Training node " + node +
                                        " is not defined in nodes list")

        else:
            raise ValueError("Training node not defined")

    def post_work(self):
        pass
