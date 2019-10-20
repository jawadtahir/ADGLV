'''
Created on Sep 13, 2019

@author: foobar
'''
from datetime import datetime
import os

from pymongo.mongo_client import MongoClient

from de.tum.steps.models import Step
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger, empty_dir
import pandas as pd


class FeatureVectorGeneration(Step):
    def __init__(self, node_map):
        super().__init__("feat_vec_step")
        self._log = get_logger(__name__)
        self.node_map = node_map

    def pre_work(self):
        def get_env_vars():
            # Format YYYY-MM-DD HH:MM
            self.date_start = os.environ.get(FEATURE_DATA_START, datetime.min)
            self._log.debug("Start date: " + str(self.date_start))

            # Format YYYY-MM-DD HH:MM
            self.date_end = os.environ.get(FEATURE_DATA_END, datetime.max)
            self._log.debug("End date: " + str(self.date_end))

            self.mongo_host = os.environ.get(MONGO_HOST, "localhost")
            self._log.debug("Mongo Host: " + self.mongo_host)

            self.mongo_port = os.environ.get(MONGO_PORT, "27017")
            self._log.debug("Mongo Port: " + self.mongo_port)

            self.nodes_to_train = os.environ.get(TRAIN_NODES_CSV)
            self._log.debug("Nodes to train: " + self.nodes_to_train)

            self.csv_dir = os.environ.get(
                FEATURE_CSV_DIR, os.path.join("/ADGLV", "feat"))
            self._log.debug("Feature Directory: " + self.csv_dir)

            self.data_dir = os.environ.get(
                TRAIN_CSV_DIR, os.path.join("/ADGLV", "data"))
            self._log.debug("Data Directory: " + self.data_dir)

        get_env_vars()
        empty_dir(self.csv_dir)
        empty_dir(self.data_dir)

    def work(self, **kwargs):

        query_filter = {"m_time": {
            "$gte": self.date_start, "$lte": self.date_end}}

        if self.nodes_to_train is not None:
            nodes_to_train = self.nodes_to_train.split(",")
            with MongoClient(self.mongo_host, int(self.mongo_port)) as db_client:
                db = db_client['thesis']
                collection = db['data_collection']
                for node in nodes_to_train:
                    ip_adrs = self.node_map.get(node.strip())
                    if ip_adrs is not None:
                        query_filter["dest_name"] = ip_adrs
                        measurments = collection.find(filter=query_filter)
                        time_deltas = []
                        m_times = []
                        m_days = []
                        labels = []
                        for measurment in measurments:
                            label = measurment["node_name"].strip()
                            label = label[len(label) - 2:]
                            labels.append(label)

                            t3 = measurment["m_val"]["t3"]
                            t5 = measurment["m_val"]["t5"]
                            time_delta = (t5 - t3) * 100
                            time_delta = format(time_delta, ".7f")
                            time_deltas.append(time_delta)

                            measurment_time_str = measurment["m_time"]
                            measurment_time_str = measurment_time_str.split(".")[
                                0]
                            measurment_time = datetime.strptime(
                                measurment_time_str, "%Y-%m-%d %H:%M:%S")
                            m_times.append(measurment_time.hour)

                            day = measurment_time.strftime("%a")
                            m_days.append(day[:2].upper())


#                         time_deltas = np.array(time_deltas)
#                         labels = np.array(labels)

                        dataframe = pd.DataFrame(
                            {"time_delta": time_deltas, "m_time": m_times, "m_day": m_days, "label": labels})
                        csv_path = os.path.join(self.csv_dir, node + ".csv")
                        dataframe.to_csv(csv_path)

                    else:
                        self._log.debug("Training node " + node +
                                        " is not defined in nodes list")

        else:
            raise ValueError("Training node not defined")

    def post_work(self):
        pass
