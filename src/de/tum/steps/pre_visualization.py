'''
Created on Oct 20, 2019

@author: foobar
'''
from datetime import datetime as dt
import os

from matplotlib import pyplot as plt

from de.tum.steps.models import Step
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger, empty_dir
import numpy as np
import pandas as pd


class PreVisualization(Step):
    '''
    Visualization of data
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.name = "pre_visualization"
        self._log = get_logger(__name__)

    def pre_work(self):
        def get_env_vars():
            # Get environment variables
            self.feature_dir = os.environ.get(
                FEATURE_CSV_DIR, os.path.join("/ADGLV", "feat"))
            self._log.debug("Feature directory: " + self.feature_dir)

            self.save_dir = os.environ.get(
                VIZ_SAVE_DIR, os.path.join("/ADGLV", "viz"))
            self.save_dir = os.path.join(self.save_dir, str(dt.utcnow()))

            empty_dir(self.save_dir)

            self._log.debug("Viz directory: " + self.save_dir)

            self.base_locs = os.environ[TRAIN_NODES_CSV]
            self.base_locs = [base_loc.strip()
                              for base_loc in self.base_locs.split(",")]
            self._log.debug("Base locations: " + str(self.base_locs))

        get_env_vars()

    def work(self, **kwargs):
        for base_loc in self.base_locs:
            self._log.debug("Generating image for: " + base_loc)
            base_dir = os.path.join(self.save_dir, base_loc)
            empty_dir(base_dir)
            csv_path = os.path.join(self.feature_dir, base_loc + ".csv")

            dataset = pd.read_csv(csv_path)
            self._log.debug(dataset)

            groups = dataset.groupby("label")
            landmarks = groups.groups.keys()

            for landmark in landmarks:
                plt.figure()

                landmark_measurement = groups.get_group(landmark)
                day_groups = landmark_measurement.groupby("m_day")
                days = day_groups.groups.keys()
                day_counter = 0
                for day in days:
                    day_counter += 1
                    d_measurement = day_groups.get_group(day)
                    plt.subplot(2, 4, day_counter)
                    plt.title(day)
                    plt.axis('off')
                    plt.plot(d_measurement["time_delta"])

                plt.savefig(os.path.join(
                    base_dir, str(landmark) + ".png"))
