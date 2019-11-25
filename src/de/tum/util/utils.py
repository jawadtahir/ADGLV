'''
Created on Aug 29, 2019

@author: foobar
'''
import logging
import os

from tensorflow.python.data import Dataset

from de.tum.util.Constants import LOG_FILE_PATH
import numpy as np
import tensorflow as tf


log_file_path = os.environ.get(LOG_FILE_PATH, "app.log")
fh = logging.FileHandler(log_file_path)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)


def get_logger(package_name):
    logger = logging.getLogger(package_name)

    # TODO: get it from configuration
    logger.setLevel(logging.DEBUG)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def empty_dir(dir_path):
    if os.path.exists(dir_path):

        for file_fd in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_fd)

            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(e)
    else:

        os.makedirs(dir_path)


def create_dirs(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)


def construct_feature_columns(input_features):
    """Construct the TensorFlow Feature Columns.
    Args:
        input_features: The names of the numerical input features to use.
    Returns:
        A set of feature columns
    """
    return set([tf.feature_column.numeric_column(my_feature) for my_feature in input_features])


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


if __name__ == '__main__':
    pass
