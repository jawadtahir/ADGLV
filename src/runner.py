'''
Created on Aug 28, 2019

@author: foobar
'''
from datetime import datetime
import logging
import os
from pathlib import Path

from de.tum.tool.glv_tool import GLVTool
from de.tum.util.Constants import GLV_TOOL_ROOT


if __name__ == "__main__":
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename="app.log",
                        level=logging.DEBUG, format=formatter)

    logger = logging.getLogger(__name__)

    logger.debug("***************************************")
    logger.debug("***************started*****************")
    logger.debug("***************************************")
    logger.debug(str(datetime.now()))
    logger.debug("***************************************")

    project_root = Path(__file__).parent.parent.absolute()
    logger.debug("project root: " + str(project_root))
    os.environ[GLV_TOOL_ROOT] = str(project_root)

    config_path = os.path.join(project_root, "config", "config.yaml")
    logger.debug("Config path: " + config_path)

    GLVTool(config_path).execute_pipeline()
