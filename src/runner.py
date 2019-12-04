'''
Created on Aug 28, 2019

@author: foobar
'''
from datetime import datetime
import os

from de.tum.tool.glv_tool import GLVTool
from de.tum.util.Constants import PHASE, PHASE_FTP
from de.tum.util.utils import get_logger


if __name__ == "__main__":

    logger = get_logger(__name__)
    ts = datetime.utcnow()

    logger.debug("***************************************")
    logger.debug("***************started*****************")
    logger.debug("***************************************")
    logger.debug(str(ts))
    logger.debug("***************************************")

    phase = os.environ.get(PHASE, PHASE_FTP)

    GLVTool(phase.strip().upper(), ts).execute_pipeline()
