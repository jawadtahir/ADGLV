'''
Created on May 21, 2019

@author: foobar
'''
from datetime import datetime
import sys
import traceback

import paramiko

from de.tum.measurement.client import SSHProbeClient
from de.tum.models import Measurement
from de.tum.util.Constants import *
from nodes import Nodes


def ssh_connect_to_node(node_name, t_now, node_adrs, private_key, passphrase):

    with SSHProbeClient() as client:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        r_time = datetime.now()

        ssh_delay = client.connect(
            node_adrs, pkey=private_key, passphrase=passphrase)

        return Measurement(node_name, node_adrs, r_time,  t_now, vars(ssh_delay), SSH_DELAY)
