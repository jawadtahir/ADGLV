'''
Created on Aug 28, 2019

@author: foobar
'''
from datetime import datetime
import time

from de.tum.tool.glv_tool import GLVTool
from de.tum.util.utils import get_logger


if __name__ == "__main__":

    logger = get_logger(__name__)

    logger.debug("***************************************")
    logger.debug("***************started*****************")
    logger.debug("***************************************")
    logger.debug(str(datetime.utcnow()))
    logger.debug("***************************************")

    # wait for rabbbitMQ to set up
    # time.sleep(10)

    GLVTool().execute_pipeline()

# /home/foobar/eclipse-workspace/Thesis/data/2019-11-02 02:53:34.449501
