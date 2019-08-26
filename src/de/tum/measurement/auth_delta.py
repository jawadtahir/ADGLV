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


SSH_PORT = 22


def ssh_connect_to_node(node_name, t_now, node_adrs, private_key, passphrase):
    try:
        client = SSHProbeClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        r_time = datetime.now()

        ssh_delay = client.connect(
            node_adrs, pkey=private_key, passphrase=passphrase)

        return Measurement(node_name, node_adrs, r_time,  t_now, vars(ssh_delay), SSH_DELAY)

    except Exception as e:
        print("*** Caught exception: %s: %s" % (e.__class__, e))
        traceback.print_exc()
        try:
            client.close()
        except:
            pass
        sys.exit(1)


if __name__ == '__main__':
    for node in Nodes().nodes_list:
        ssh_connect_to_node(node)
