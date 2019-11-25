'''
Created on Nov 2, 2019

@author: foobar
'''
import os

from de.tum.steps.models import Step
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger
import numpy as np
import pandas as pd
import tensorflow as tf


class DNNPredictor(Step):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super().__init__("adglv_predictor")
        self._log = get_logger(__name__)

    def pre_work(self):
        # get feature vector directory
        #         feature_csv_dir = os.environ.get(
        #             FEATURE_CSV_DIR, os.path.join("/ADGLV", "feat"))
        #         self._log.debug("Feature CSV Dir: " + str(feature_csv_dir))
        #
        #         # Hidden layers nodes
        #         hidden_units_csv = os.environ.get(
        #             TRAIN_HIDDEN_UNITS, "20,20,20,20,20")
        #         self.hidden_units = [int(unit) for unit in hidden_units_csv.split(",")]
        #         self._log.debug("Hidden units: " + str(self.hidden_units))
        pass

    def work(self, **kwargs):

        def predict_in_fn(feats):
            features = {key: np.array(value)
                        for key, value in dict(feats).items()}

            return tf.data.Dataset.from_tensor_slices(features).batch(10)

        dataset = pd.read_csv(
            r"/home/foobar/eclipse-workspace/Thesis/feat/features.csv")
        dataset = dataset.reindex(np.random.permutation(dataset.index))

        predict_data = dataset.head(1000)

        feat_columns = predict_data.columns[1:len(predict_data.columns) - 1]
        features = predict_data[feat_columns].copy()
        expected = predict_data["labels"].copy()

        model = tf.estimator.DNNClassifier(
            feature_columns=[
                tf.feature_column.numeric_column("t0"),
                tf.feature_column.numeric_column("t1"),
                tf.feature_column.numeric_column("t2"),
                tf.feature_column.numeric_column("t3"),
                tf.feature_column.numeric_column("t4")],
            hidden_units=[120, 20, 20],
            n_classes=6,
            optimizer=tf.train.AdagradOptimizer(
                learning_rate=0.03),
            warm_start_from=r"/home/foobar/eclipse-workspace/Thesis/data/2019-11-02 04:23:42.688722")

        predicts = model.predict(input_fn=lambda: predict_in_fn(features))

        correct = 0
        total = 0

        for p, e in zip(predicts, expected):
            total += 1
            id = p["class_ids"][0]
            label = p["all_classes"][id]
            prob = p["probabilities"][id]

            if (int(label) == int(e)):
                correct += 1

        print(str(correct) + ", " + str(total))

#         print(list(predicts))
#         print(expected)
