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

        os.mkdir(dir_path)


if __name__ == '__main__':
    pass
