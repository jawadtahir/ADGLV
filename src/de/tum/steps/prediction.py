'''
Created on Nov 2, 2019

@author: foobar
'''
import os

from sklearn.metrics.classification import confusion_matrix
from sklearn.utils.multiclass import unique_labels

from de.tum.steps.models import Step
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger, create_dirs, empty_dir,\
    construct_feature_columns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf


class DNNPredictor(Step):
    '''
    classdocs
    '''

    def __init__(self, timestamp):
        '''
        Constructor
        '''
        super().__init__("adglv_predictor")
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

        # Ratio of dataset to be used as prediction.
        dataset_prediction_ratio = os.environ.get(
            PREDICT_DATASET_PREDICTION_RATIO, 0.75)
        self.prediction_ratio = float(dataset_prediction_ratio)
        self._log.debug("Prediction ratio: " + str(self.prediction_ratio))

        # Get CSV path
        csv_path = os.path.join(feature_csv_dir, "features.csv")
        dataset = pd.read_csv(csv_path)
        self.dataset = dataset.reindex(np.random.permutation(dataset.index))
        self._log.debug(self.dataset)

        # Learning rate for the classsifier
        self.learning_rate = os.environ.get(TRAIN_LEARNING_RATE, "0.01")
        self.learning_rate = float(self.learning_rate)
        self._log.debug("Learning rate: " + str(self.learning_rate))

        # Batch size
        self.batch_size = os.environ.get(TRAIN_BATCH_SIZE, "10")
        self.batch_size = int(self.batch_size)
        self._log.debug("Batch size: " + str(self.batch_size))

        # Hidden layers nodes
        hidden_units_csv = os.environ.get(
            TRAIN_HIDDEN_UNITS, "20,20,20,20,20")
        self.hidden_units = [int(unit) for unit in hidden_units_csv.split(",")]
        self._log.debug("Hidden units: " + str(self.hidden_units))

        # Prediction directory to store figures and tickets
        self.predict_dir = os.environ.get(
            PREDICT_ROOT_DIR, os.path.join("/ADGLV", "predict"))
        self._log.debug("Prediction root dir: " + str(self.predict_dir))
        create_dirs(self.predict_dir)
        empty_dir(self.predict_dir)

        # Model directory to store model
        self.model_dir = os.environ.get(
            TRAIN_MODEL_DIR, os.path.join("/ADGLV", "model"))
        self._log.debug("Model dir: " + str(self.model_dir))

        self.exe_dir = os.path.join(self.predict_dir, str(self.timestamp))
        self.exe_dir = self.exe_dir.split(".")[0]
        create_dirs(self.exe_dir)
        self._log.debug("Execution dir: " + str(self.exe_dir))

        # Get numeric features
        self.numeric_features = os.environ.get(
            TRAIN_NUMERIC_FEATURES, "t0,t1,t2,t3,t4,t5")
        self.numeric_features = [x.strip()
                                 for x in self.numeric_features.split(",")]
        self._log.debug("Numeric features: " + str(self.numeric_features))

        # Get catagorical features
        self.catagory_features = os.environ.get(TRAIN_CATAGORY_FEATURES, None)
        if self.catagory_features is not None:
            self.catagory_features = [x.strip()
                                      for x in self.catagory_features.split(",")]
        else:
            self.catagory_features = []
        self._log.debug("Catagory features: " + str(self.catagory_features))

    def work(self, **kwargs):

        def predict_in_fn(feats):
            features = {key: np.array(value)
                        for key, value in dict(feats).items()}

            return tf.data.Dataset.from_tensor_slices(features).batch(self.batch_size)

        def plot_confusion_matrix(y_true, y_pred, classes,
                                  normalize=False,
                                  title=None,
                                  cmap=plt.get_cmap("gnuplot")):
            """
            This function prints and plots the confusion matrix.
            Normalization can be applied by setting `normalize=True`.
            """
            if not title:
                if normalize:
                    title = 'Normalized confusion matrix'
                else:
                    title = 'Confusion matrix, without normalization'

            # Compute confusion matrix
            cm = confusion_matrix(y_true, y_pred)
            # Only use the labels that appear in the data
            classes = classes[unique_labels(y_true, y_pred)]
            if normalize:
                cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
                print("Normalized confusion matrix")
            else:
                print('Confusion matrix, without normalization')

            print(cm)

            self.cm = cm

            fig, ax = plt.subplots()
            im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
            ax.figure.colorbar(im, ax=ax)
            # We want to show all ticks...
            ax.set(xticks=np.arange(cm.shape[1]),
                   yticks=np.arange(cm.shape[0]),
                   # ... and label them with the respective list entries
                   xticklabels=classes, yticklabels=classes,
                   title=title,
                   ylabel='True label',
                   xlabel='Predicted label')

            # Rotate the tick labels and set their alignment.
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
                     rotation_mode="anchor")

            # Loop over data dimensions and create text annotations.
            fmt = '.2f' if normalize else 'd'
            thresh = cm.max() / 2.
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(j, i, format(cm[i, j], fmt),
                            ha="center", va="center",
                            color="white" if cm[i, j] > thresh else "black")
            fig.tight_layout()
            return ax

        data_size = len(self.dataset.index)

        prediction_size = int(data_size * self.prediction_ratio)

        predict_data = self.dataset.head(prediction_size)

#         feat_columns = predict_data.columns[1:len(predict_data.columns) - 1]
        feat_columns = self.numeric_features + self.catagory_features

        features = predict_data[feat_columns].copy()
        expected = predict_data["labels"].copy()

        classes = self.dataset.groupby("labels")
        num_classes = len(classes.groups.keys())

        model = tf.estimator.DNNClassifier(
            feature_columns=construct_feature_columns(
                self.numeric_features, self.catagory_features),
            hidden_units=self.hidden_units,
            n_classes=num_classes,
            optimizer=tf.train.AdagradOptimizer(
                learning_rate=self.learning_rate),
            warm_start_from=self.model_dir)

        predicts = model.predict(input_fn=lambda: predict_in_fn(features))

        correct = 0
        total = len(features.index)

        predictions = []
        expectations = []

        for p, e in zip(predicts, expected):
            cid = p["class_ids"][0]
            label = p["all_classes"][cid]
            prob = p["probabilities"][cid]

            predictions.append(int(label))
            expectations.append(int(e))

            if (int(label) == int(e)):
                correct += 1

        print(str(correct) + ", " + str(total))

        self.total_datapoints = total
        self.correct_datapoints = correct

        plot_confusion_matrix(expectations, predictions, np.arange(
            num_classes), True, "Confusion matrix")

        plt.savefig(os.path.join(self.exe_dir, "cm.png"))

    def post_work(self):
        ticket_path = os.path.join(self.exe_dir, "ticket.txt")
        with open(ticket_path, "w") as ticket_fd:
            ticket_fd.write("Prediction ratio: " +
                            str(self.prediction_ratio) + "\n")
            ticket_fd.write("Numeric features: " +
                            str(self.numeric_features) + "\n")
            ticket_fd.write("Catagorical features: " +
                            str(self.catagory_features) + "\n")
            ticket_fd.write("Total datapoints: " +
                            str(self.total_datapoints) + "\n")
            ticket_fd.write("Correct datapoints: " +
                            str(self.correct_datapoints) + "\n")
            ticket_fd.write("Confusion matrix: \n")
            ticket_fd.write(str(self.cm) + "\n")
