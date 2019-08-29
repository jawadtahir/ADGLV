'''
Created on 06.05.2019

@author: foobar
'''
from datetime import datetime
import json
import os

from de.tum.models import Measurement
from de.tum.util.Constants import *
from de.tum.util.utils import get_logger

log = get_logger(__name__)


def pinger(node_name, t_now, node_adrs, **kwargs):
    m_time = datetime.utcnow()
    command = r"mtr --json --max-ttl 250 --tcp --port 22 --show-ips " + node_adrs
#     command = r"mtr --json --max-ttl 250 --port 22 --show-ips " + node_adrs
    output = os.popen(command).read()
    log.debug(output)
    mtr_reponse = json.loads(output)

    return Measurement(node_name, node_adrs, t_now, str(m_time), mtr_reponse, MTR_DELAY)
