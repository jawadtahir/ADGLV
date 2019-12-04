'''
Created on Sep 13, 2019

@author: foobar
'''
from datetime import datetime as dt
import os
import traceback

from pymongo.mongo_client import MongoClient

from de.tum.steps.models import Step
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger, create_dirs, empty_dir
import pandas as pd


class FeatureVectorGeneration(Step):
    def __init__(self, timestamp):
        super().__init__("feat_vec_step")
        self._log = get_logger(__name__)
        self.timestamp = timestamp

    def pre_work(self):
        def get_env_vars():
            # Format YYYY-MM-DD HH:MM
            self.date_start = os.environ.get(FEATURE_DATA_START, str(dt.min))
            self._log.debug("Start date: " + str(self.date_start))

            # Format YYYY-MM-DD HH:MM
            self.date_end = os.environ.get(FEATURE_DATA_END, str(dt.max))
            self._log.debug("End date: " + str(self.date_end))

            self.mongo_host = os.environ.get(MONGO_HOST, "localhost")
            self._log.debug("Mongo Host: " + str(self.mongo_host))

            self.mongo_port = os.environ.get(MONGO_PORT, "27017")
            self._log.debug("Mongo Port: " + self.mongo_port)
            self.mongo_port = int(self.mongo_port)

            self.csv_dir = os.environ.get(
                FEATURE_CSV_DIR, os.path.join("/ADGLV", "feat"))
            self._log.debug("Feature Directory: " + self.csv_dir)

            self.exe_dir = os.path.join(self.csv_dir, str(self.timestamp))
            self.exe_dir = self.exe_dir.split(".")[0]
            self._log.debug("Execution Directory: " + self.exe_dir)

            self.database_name = os.environ.get(DATABASE_NAME, "thesis")
            self._log.debug("Database name: " + self.database_name)

            self.collection_name = os.environ.get(
                COLLECTION_NAME, "data_collection")
            self._log.debug("Collection name: " + self.collection_name)

            self.percentile_upper_limit = float(
                os.environ.get(FEATURE_DATASET_UPPER_CUT_OFF, 0))
            self.percentile_lower_limit = float(
                os.environ.get(FEATURE_DATASET_LOWER_CUT_OFF, 0))

            self._log.debug("Percentile upper limit: " +
                            str(self.percentile_upper_limit))
            self._log.debug("Percentile lower limit: " +
                            str(self.percentile_lower_limit))

        get_env_vars()
        self._log.debug("Creating Feature Dictionary...")
        create_dirs(self.csv_dir)
        self._log.debug("Emptying Feature Dictionary...")
        empty_dir(self.csv_dir)
        self._log.debug("Creating Execution Dictionary...")
        create_dirs(self.exe_dir)

    def work(self, **kwargs):

        def clean_data(dataframe, upper_limit, lower_limit):
            limits = dataframe["time_deltas"].quantile(
                [upper_limit, lower_limit])
            clean_data_ids = dataframe["time_deltas"].between(
                limits[lower_limit], limits[upper_limit], True)
            cleaned_data = dataframe[clean_data_ids]

            return cleaned_data.copy()

        query_filter = {"m_time": {
            "$gte": self.date_start, "$lte": self.date_end}}
        self._log.debug("Connecting MongoDB...")
        with MongoClient(self.mongo_host, self.mongo_port) as db_client:
            db = db_client[self.database_name]
            collection = db[self.collection_name]

            self._log.debug("Running query...")
            measurments = collection.find(
                filter=query_filter).batch_size(10000)

            m_months = []
            m_dates = []
            m_hours = []
            m_minutes = []

            origins = []
            time_deltas = []
            labels = []

            # counter
            i = 0
            j = 0

            for measurment in measurments:
                i += 1
                if (i % 10000) == 0:
                    self._log.debug("Processed records: " + str(i))

                m_month = None
                m_date = None
                m_hour = None
                m_minute = None

                origin = None
                time_delta = None
                label = None
                try:
                    # Get measurement time
                    measurment_time_str = measurment["m_time"]
                    measurment_time_str = measurment_time_str.split(".")[
                        0]

                    # Convert it to datetime object
                    measurment_time = dt.strptime(
                        measurment_time_str, "%Y-%m-%d %H:%M:%S")

                    m_month = measurment_time.month
                    m_date = measurment_time.day
                    m_hour = measurment_time.hour
                    m_minute = measurment_time.minute

                    # Get the name of source machine
                    origin = measurment["node_name"].strip()
                    origin = origin[len(origin) - 2:]

                    # Measure time between t3 and t5 (Read thesis)
                    t3 = measurment["m_val"]["t3"]
                    t5 = measurment["m_val"]["t5"]
                    time_delta = (t5 - t3) * 100
                    time_delta = float(format(time_delta, ".4f"))

                    # Get the name of target machine
                    label = measurment["dest_name"].strip()
#                     if self.relay_map.get(label):
#                         label = self.relay_map.get(label)

                    label = label[len(label) - 2:]

                except Exception as e:
                    self._log.debug(repr(e))
                    traceback.print_exc(e)

                # Create data arrays
                m_months.append(m_month)
                m_dates.append(m_date)
                m_hours.append(m_hour)
                m_minutes.append(m_minute)

                origins.append(origin)
                time_deltas.append(time_delta)
                labels.append(label)

            self._log.debug("Total records processed: " + str(i))

            dataframe = pd.DataFrame(
                {"m_months": m_months,
                 "m_dates": m_dates,
                 "m_hours": m_hours,
                 "m_minutes": m_minutes,
                 "origins": origins,
                 "time_deltas": time_deltas,
                 "labels": labels})

            # Get measurement data of each target location
            dfg_per_location = dataframe.groupby("labels")
            locations = dfg_per_location.groups.keys()
            n_locs = len(locations)
            self._log.debug("Number of base locations: " + str(n_locs))

            # create feature columns
            col_names = ["t" + str(n) for n in range(n_locs - 1)]
            col_names.append("labels")

            dataset = pd.DataFrame(columns=col_names)

            for location in locations:
                # Get measurement set for each base location
                df_per_location = dfg_per_location.get_group(location)
                # optionally clean it
                if self.percentile_upper_limit > 0 and self.percentile_lower_limit > 0:
                    df_per_location = clean_data(
                        df_per_location, self.percentile_upper_limit, self.percentile_lower_limit)
                # Group by timestamp
                measurement_group = df_per_location.groupby([
                    "m_months", "m_dates", "m_hours", "m_minutes"])
                timestamps = measurement_group.groups.keys()
                # Iterate over timestamps
                for ts in timestamps:
                    ms = measurement_group.get_group(ts)
                    ms = ms.sort_values("origins")
                    td = ms.iloc[:, -2]
                    td = [t for t in td]
                    # We dont have data from all machines for that timestamp
                    if (len(td) != (n_locs - 1)):
                        continue

                    j += 1
                    td.append(location)
                    dataset.loc[len(dataset)] = td

            self._log.debug("Total datapoints: " + str(j))

            self._log.debug("Writing dataset to disk...")
            csv_path = os.path.join(self.csv_dir,   "features.csv")
            dataset.to_csv(csv_path)

            csv_path = os.path.join(self.exe_dir,   "features.csv")
            dataset.to_csv(csv_path)

    def post_work(self):
        ticket_path = os.path.join(self.exe_dir, "ticket.txt")
        with open(ticket_path, "w") as ticket_fd:
            ticket_fd.write("Start date: " + str(self.date_start) + "\n")
            ticket_fd.write("End date: " + str(self.date_end) + "\n")
            ticket_fd.write("Mongo Host: " + str(self.mongo_host) + "\n")
            ticket_fd.write("Mongo Port: " + str(self.mongo_port) + "\n")
            ticket_fd.write("Database name: " + self.database_name + "\n")
            ticket_fd.write("Collection name: " + self.collection_name + "\n")
            ticket_fd.write("Percentile upper limit: " +
                            str(self.percentile_upper_limit) + "\n")
            ticket_fd.write("Percentile lower limit: " +
                            str(self.percentile_lower_limit) + "\n")
