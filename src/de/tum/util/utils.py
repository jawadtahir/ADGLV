'''
Created on Aug 29, 2019

@author: foobar
'''
import logging
import os


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

DAYS_VOCAB = {"MO", "TU", "WE", "TH", "FR", "SA", "SU"}

CAT_VOCAB_MAPPING = {"m_day": DAYS_VOCAB}


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


def construct_feature_columns(numeric_features, catagory_features):
    """Construct the TensorFlow Feature Columns.
    Args:
        input_features: The names of the numerical input features to use.
    Returns:
        A set of feature columns
    """
    cat_cols = []
    num_cols = [tf.feature_column.numeric_column(
        my_feature) for my_feature in numeric_features]
    for cat_feat in catagory_features:
        feat_cat_col = tf.feature_column.categorical_column_with_vocabulary_list(
            cat_feat, CAT_VOCAB_MAPPING[cat_feat])
        cat_cols.append(tf.feature_column.indicator_column(feat_cat_col))

    feat_cols = num_cols + cat_cols

    return set(feat_cols)


if __name__ == '__main__':
    pass
