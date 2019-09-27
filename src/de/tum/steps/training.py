'''
Created on Sep 22, 2019

@author: foobar
'''
import math
import os
from traceback import print_exc

from sklearn import metrics
from tensorflow.python.data import Dataset

from de.tum.steps.models import Step
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf


TRAINING_RATIO = 0.8


class ADGLVDNNClassifier(Step):
    '''
    classdocs
    '''

    def __init__(self, name):
        '''
        Constructor
        '''
        super().__init__(name)
        self._log = get_logger(__name__)
        self.base_loc_data_map = {}

    def pre_work(self):
        feature_csv_dir = os.environ.get(
            FEATURE_CSV_DIR, os.path.join("/ADGLV", "data"))
        self._log.debug("Feature CSV Dir: " + feature_csv_dir)

        self.base_locs = os.environ[TRAIN_NODES_CSV]
        self.base_locs = [base_loc.strip()
                          for base_loc in self.base_locs.split(",")]
        self._log.debug("Base locations: " + str(self.base_locs))

        for base_loc in self.base_locs:
            csv_path = os.path.join(feature_csv_dir, base_loc + ".csv")
            dataset = pd.read_csv(csv_path)
            dataset = dataset.reindex(np.random.permutation(dataset.index))
            print(dataset)
            groups = dataset.groupby("label")
            landmarks = groups.groups.keys()
            for landmark in landmarks:
                landmark_measurement = groups.get_group(landmark)
                limits = landmark_measurement["time_delta"].quantile([
                                                                     0.01, 0.99])
                filtered_data_ids = landmark_measurement["time_delta"].between(
                    limits[0.01], limits[0.99], True)
                filtered_data = landmark_measurement[filtered_data_ids]

                if self.base_loc_data_map.get(base_loc) is not None:
                    self.base_loc_data_map[base_loc].append(filtered_data)
                else:
                    self.base_loc_data_map[base_loc] = [filtered_data]

#                 landmark_measurement.hist(column="time_delta")
#                 filtered_data.hist(column="time_delta")

            self.base_loc_data_map[base_loc] = pd.concat(
                self.base_loc_data_map[base_loc])

            print(base_loc)

    def work(self, **kwargs):
        def my_input_fn(features, targets, batch_size=1, shuffle=False, num_epochs=None):
            """Trains a neural net classification model.

            Args:
              features: pandas DataFrame of features
              targets: pandas DataFrame of targets
              batch_size: Size of batches to be passed to the model
              shuffle: True or False. Whether to shuffle the data.
              num_epochs: Number of epochs for which data should be repeated. None = repeat indefinitely
            Returns:
              Tuple of (features, labels) for next data batch
            """

            # Convert pandas data into a dict of np arrays.
#             features = {key: np.array(value)
#                         for key, value in dict(features).items()}
            features = {"time_delta": np.array(features)}

            targets = np.array(targets)

            # Construct a dataset, and configure batching/repeating.
            ds = None
            ds = Dataset.from_tensor_slices(
                (features, targets))  # warning: 2GB limit

            ds = ds.batch(batch_size).repeat(num_epochs)

            # Shuffle the data, if specified.
            if shuffle:
                ds = ds.shuffle(10000)

            # Return the next batch of data.
            features, labels = ds.make_one_shot_iterator().get_next()
            return features, labels

        def construct_feature_columns(input_features):
            """Construct the TensorFlow Feature Columns.
            Args:
                input_features: The names of the numerical input features to use.
            Returns:
                A set of feature columns
            """
            return set([tf.feature_column.numeric_column(my_feature) for my_feature in input_features])

        def train_nn_regression_model(
                learning_rate,
                steps,
                batch_size,
                hidden_units,
                n_classes,
                training_examples,
                training_targets,
                validation_examples,
                validation_targets):
            """Trains a neural network Classification model.

            In addition to training, this function also prints training progress information,
            as well as a plot of the training and validation loss over time.

            Args:
              learning_rate: A `float`, the learning rate.
              steps: A non-zero `int`, the total number of training steps. A training step
                consists of a forward and backward pass using a single batch.
              batch_size: A non-zero `int`, the batch size.
              hidden_units: A `list` of int values, specifying the number of neurons in each layer.
              training_examples: A `DataFrame` containing one or more columns from
                `california_housing_dataframe` to use as input features for training.
              training_targets: A `DataFrame` containing exactly one column from
                `california_housing_dataframe` to use as target for training.
              validation_examples: A `DataFrame` containing one or more columns from
                `california_housing_dataframe` to use as input features for validation.
              validation_targets: A `DataFrame` containing exactly one column from
                `california_housing_dataframe` to use as target for validation.

            Returns:
              A `DNNRegressor` object trained on the training data.
            """

            periods = 10
            steps_per_period = steps / periods

#             optimizer = tf.keras.optimizers.Adagrad(
#                 learning_rate=learning_rate)

            dnn_regressor = tf.estimator.DNNClassifier(
                feature_columns=[
                    tf.feature_column.numeric_column("time_delta")],
                hidden_units=hidden_units,
                n_classes=n_classes,
                optimizer=tf.train.AdagradOptimizer(
                    learning_rate=learning_rate)
            )

            # Create input functions.
            def training_input_fn(): return my_input_fn(training_examples,
                                                        training_targets,
                                                        batch_size=batch_size)

            def predict_training_input_fn(): return my_input_fn(training_examples,
                                                                training_targets,
                                                                num_epochs=1,
                                                                shuffle=False)

            def predict_validation_input_fn(): return my_input_fn(validation_examples,
                                                                  validation_targets,
                                                                  num_epochs=1,
                                                                  shuffle=False)

            # Train the model, but do so inside a loop so that we can periodically assess
            # loss metrics.
            print("Training model...")
            print("RMSE (on training data):")
            training_rmse = []
            validation_rmse = []
            for period in range(0, periods):
                # Train the model, starting from the prior state.
                dnn_regressor.train(
                    input_fn=training_input_fn,
                    steps=steps_per_period
                )
                # Take a break and compute predictions.
                training_predictions = dnn_regressor.evaluate(
                    input_fn=predict_training_input_fn)
                training_predictions = training_predictions['accuracy']

                validation_predictions = dnn_regressor.evaluate(
                    input_fn=predict_validation_input_fn)
                validation_predictions = validation_predictions['accuracy']

                # Compute training and validation loss.
#                 training_root_mean_squared_error = math.sqrt(
# metrics.mean_squared_error(training_predictions, training_targets))
                training_root_mean_squared_error = training_predictions

#                 validation_root_mean_squared_error = math.sqrt(
# metrics.mean_squared_error(validation_predictions, validation_targets))
                validation_root_mean_squared_error = validation_predictions
                # Occasionally print the current loss.
                print("  period %02d : %0.2f" %
                      (period, training_root_mean_squared_error))
                # Add the loss metrics from this period to our list.
                training_rmse.append(training_root_mean_squared_error)
                validation_rmse.append(validation_root_mean_squared_error)
            print("Model training finished.")

            # Output a graph of loss metrics over periods.
            plt.ylabel("RMSE")
            plt.xlabel("Periods")
            plt.title("Root Mean Squared Error vs. Periods")
            plt.tight_layout()
            plt.plot(training_rmse, label="training")
            plt.plot(validation_rmse, label="validation")
            plt.legend()

            print("Final RMSE (on training data):   %0.2f" %
                  training_root_mean_squared_error)
            print("Final RMSE (on validation data): %0.2f" %
                  validation_root_mean_squared_error)

            return dnn_regressor

        for base_loc, dataset in self.base_loc_data_map.items():

            learning_rate = os.environ.get(TRAIN_LEARNING_RATE, "0.01")
            learning_rate = float(learning_rate)

            batch_size = os.environ.get(TRAIN_BATCH_SIZE, "10")
            batch_size = int(batch_size)

            steps = os.environ.get(TRAIN_STEPS, "500")
            steps = int(steps)

            hidden_units_csv = os.environ.get(
                TRAIN_HIDDEN_UNITS, "10,10,10,10,10,10")
            hidden_units = [int(unit) for unit in hidden_units_csv.split(",")]

            dataset = dataset.reindex(np.random.permutation(dataset.index))

            data_size = len(dataset)
            training_data_size = int(data_size * TRAINING_RATIO)

            training_data = dataset.head(training_data_size)
            training_feature = training_data["time_delta"].copy()
            training_label = training_data["label"].copy()

            validation_data = dataset.tail(data_size - training_data_size)
            validation_feature = validation_data["time_delta"].copy()
            validation_label = validation_data["label"].copy()

            classes = dataset.groupby("label")
            num_classes = len(classes.groups.keys())

            train_nn_regression_model(learning_rate, steps, batch_size, hidden_units, num_classes,
                                      training_feature, training_label, validation_feature, validation_label)
