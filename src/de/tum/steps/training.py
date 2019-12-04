'''
Created on Sep 22, 2019

@author: foobar
'''
import os
from traceback import print_exc

from tensorflow.python.data import Dataset

from de.tum.steps.models import Step
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger, create_dirs, empty_dir, construct_feature_columns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf


class ADGLVDNNClassifier(Step):
    '''
    DNN classifier for the 
    '''

    def __init__(self, timestamp):
        '''
        Constructor
        '''
        super().__init__("adglv_dnn_classifier")
        self._log = get_logger(__name__)
        self.timestamp = timestamp

    def pre_work(self):
        '''
        Get config from env vars and perform data cleaning
        '''
        # get feature vector directory
        feature_csv_dir = os.environ.get(
            FEATURE_CSV_DIR, os.path.join("/ADGLV", "feat"))
        self._log.debug("Feature CSV Dir: " + str(feature_csv_dir))

        # Ratio of training dataset. Remaining will be used for validation
        dataset_training_ratio = os.environ.get(
            TRAIN_DATASET_TRAINING_RATIO, 0.75)
        self.training_ratio = float(dataset_training_ratio)
        self._log.debug("Training ratio: " + str(self.training_ratio))

        # Learning rate for the classsifier
        self.learning_rate = os.environ.get(TRAIN_LEARNING_RATE, "0.01")
        self.learning_rate = float(self.learning_rate)
        self._log.debug("Learning rate: " + str(self.learning_rate))

        # Batch size
        self.batch_size = os.environ.get(TRAIN_BATCH_SIZE, "10")
        self.batch_size = int(self.batch_size)
        self._log.debug("Batch size: " + str(self.batch_size))

        # Number of training steps
        self.steps = os.environ.get(TRAIN_STEPS, "500")
        self.steps = int(self.steps)
        self._log.debug("Training steps: " + str(self.steps))

        # Hidden layers nodes
        hidden_units_csv = os.environ.get(
            TRAIN_HIDDEN_UNITS, "20,20,20,20,20")
        self.hidden_units = [int(unit) for unit in hidden_units_csv.split(",")]
        self._log.debug("Hidden units: " + str(self.hidden_units))

        # Training directory to store figures and models
        self.train_dir = os.environ.get(
            TRAIN_ROOT_DIR, os.path.join("/ADGLV", "train"))
        self._log.debug("Training root dir: " + str(self.train_dir))
        create_dirs(self.train_dir)
        empty_dir(self.train_dir)

        # Model directory to store model
        self.model_dir = os.environ.get(
            TRAIN_MODEL_DIR, os.path.join("/ADGLV", "model"))
        self._log.debug("Model dir: " + str(self.model_dir))
        create_dirs(self.model_dir)
        empty_dir(self.model_dir)

        self.exe_dir = os.path.join(self.train_dir, str(self.timestamp))
        self.exe_dir = self.exe_dir.split(".")[0]
        create_dirs(self.exe_dir)
        self._log.debug("Execution dir: " + str(self.exe_dir))

        # Get CSV path
        csv_path = os.path.join(feature_csv_dir, "features.csv")
        dataset = pd.read_csv(csv_path)
        self.dataset = dataset.reindex(np.random.permutation(dataset.index))
        self._log.debug(self.dataset)

        # Get number of periods
        periods = os.environ.get(TRAIN_PERIODS, "50")
        self._log.debug("Training periods: " + periods)
        self.periods = int(periods)

    def work(self, **kwargs):

        def my_input_fn(features, targets, batch_size=1, num_epochs=None):
            """Get dataset.

            Args:
              features: pandas DataFrame of features
              targets: pandas DataFrame of targets
              batch_size: Size of batches to be passed to the model
              num_epochs: Number of epochs for which data should be repeated. None = repeat indefinitely
            Returns:
              Tuple of (features, labels) for next data batch
            """

            # Convert pandas data into a dict of np arrays.
            features = {key: np.array(value)
                        for key, value in dict(features).items()}

            targets = np.array(targets)

            # Construct a dataset, and configure batching/repeating.
            ds = None
            ds = Dataset.from_tensor_slices(
                (features, targets))  # warning: 2GB limit

            ds = ds.batch(batch_size).repeat(num_epochs)

            # Return the next batch of data.
            features, labels = ds.make_one_shot_iterator().get_next()
            return features, labels

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
            as well as a plot of the accuracy loss over time.

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
              A `DNNClassifier` object trained on the training data.
            """

            steps_per_period = steps / self.periods

            self._log.debug("Creating classifier...")
            dnn_classifier = tf.estimator.DNNClassifier(
                feature_columns=construct_feature_columns(training_examples),
                hidden_units=hidden_units,
                n_classes=n_classes,
                model_dir=self.model_dir,
                optimizer=tf.train.AdagradOptimizer(
                    learning_rate=learning_rate)
            )

            # Create input functions.
            def training_input_fn(): return my_input_fn(training_examples,
                                                        training_targets,
                                                        batch_size=batch_size)

            def predict_training_input_fn(): return my_input_fn(training_examples,
                                                                training_targets,
                                                                batch_size=10,
                                                                num_epochs=1)

            def predict_validation_input_fn(): return my_input_fn(validation_examples,
                                                                  validation_targets,
                                                                  batch_size=10,
                                                                  num_epochs=1)

            # Train the model, but do so inside a loop so that we can periodically assess
            # loss metrics.
            print("Training model...")
            print("Accuracies (on validation data):")

            self._log.debug("Training model...")
            self._log.debug("Accuracies (on validation data):")

            training_accuracies = []
            validation_accuracies = []

            for period in range(0, self.periods):
                # Train the model, starting from the prior state.
                dnn_classifier.train(
                    input_fn=training_input_fn,
                    steps=steps_per_period
                )
                # Take a break and predict
                training_predictions = dnn_classifier.evaluate(
                    input_fn=predict_training_input_fn)
                training_predictions_accuracy = training_predictions['accuracy']

                validation_predictions = dnn_classifier.evaluate(
                    input_fn=predict_validation_input_fn)
                validation_predictions_accuracy = validation_predictions['accuracy']

                # Print the current accuracy.
                print("  period %02d : %0.2f" %
                      (period, validation_predictions_accuracy))
                self._log.debug("  period %02d : %0.2f" %
                                (period, validation_predictions_accuracy))

                # Add the loss metrics from this period to our list.
                training_accuracies.append(training_predictions_accuracy)
                validation_accuracies.append(validation_predictions_accuracy)
            print("Model training finished.")
            self._log.debug("Model training finished.")

            self._log.debug("Creating accuracy graph")
            # Output a graph of loss metrics over periods.
            plt.figure()
            plt.ylabel("Accuracy")
            plt.xlabel("Periods")
            plt.title("Accuracy vs. Periods")
            plt.tight_layout()
            plt.plot(training_accuracies, label="training")
            plt.plot(validation_accuracies, label="validation")
            plt.legend()
#             plt.savefig(os.path.join(self.train_dir, "accuracy.png"))
            plt.savefig(os.path.join(self.exe_dir, "accuracy.png"))

            print("Final accuracy (on training data):   %0.2f" %
                  training_accuracies[-1])
            print("Final accuracy (on validation data): %0.2f" %
                  validation_accuracies[-1])
            self._log.debug("Final accuracy (on training data):   %0.2f" %
                            training_accuracies[-1])
            self._log.debug("Final accuracy (on validation data): %0.2f" %
                            validation_accuracies[-1])

            self.training_accuracies = training_accuracies
            self.validation_accuracies = validation_accuracies

            return dnn_classifier

        data_size = len(self.dataset.index)
        self._log.debug("Dataset size: " + str(data_size))

        # Get training data size
        training_data_size = int(data_size * self.training_ratio)
        self._log.debug("Training dataset size: " + str(training_data_size))

        training_data = self.dataset.head(training_data_size)

        # Get training features. First is index and last is label so we ommit
        # them
        training_feats = training_data.columns[1:len(
            training_data.columns) - 1]

        # Create features and labels
        training_feature = training_data[training_feats].copy()
        training_label = training_data["labels"].copy()

        # Get validation dataset
        self._log.debug("Validation dataset size: " +
                        str(data_size - training_data_size))
        validation_data = self.dataset.tail(data_size - training_data_size)

        validation_feature = validation_data[training_feats].copy()
        validation_label = validation_data["labels"].copy()

        classes = self.dataset.groupby("labels")
        num_classes = len(classes.groups.keys())

        # Start training
        model = train_nn_regression_model(self.learning_rate, self.steps, self.batch_size, self.hidden_units, num_classes,
                                          training_feature, training_label, validation_feature, validation_label)

    def post_work(self):
        text_file_path = os.path.join(self.exe_dir, "ticket.txt")
        with open(text_file_path, "w") as text_file:
            text_file.write("Training ratio: " +
                            str(self.training_ratio) + "\n")
            text_file.write("Learning rate: " + str(self.learning_rate) + "\n")
            text_file.write("Batch size: " + str(self.batch_size) + "\n")
            text_file.write("Hidden units: " + str(self.hidden_units) + "\n")
            text_file.write("Steps: " + str(self.steps) + "\n")
            text_file.write("Validation acc: " +
                            str(self.validation_accuracies) + "\n")
            text_file.write("Training acc: " +
                            str(self.training_accuracies) + "\n")
