'''
Created on Aug 29, 2019

@author: foobar
'''
import logging
import os
from de.tum.util.Constants import LOG_FILE_PATH


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


if __name__ == '__main__':
    pass
