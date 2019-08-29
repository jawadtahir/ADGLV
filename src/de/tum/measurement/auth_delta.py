'''
Created on May 21, 2019

@author: foobar
'''
from datetime import datetime

import paramiko

from de.tum.measurement.client import SSHProbeClient
from de.tum.models import Measurement
from de.tum.util.Constants import *


def ssh_connect_to_node(node_name, t_now, node_adrs, private_key, passphrase):

    with SSHProbeClient() as client:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        m_time = datetime.utcnow()

        ssh_delay = client.connect(
            node_adrs, pkey=private_key, passphrase=passphrase)

        return Measurement(node_name, node_adrs, t_now, str(m_time), vars(ssh_delay), SSH_DELAY)
