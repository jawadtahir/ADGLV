'''
Created on 06.05.2019

@author: foobar
'''
from datetime import datetime
import json
import os

from de.tum.models import Measurement
from de.tum.util.Constants import *
from nodes import Nodes


class Pinger(object):
    def __init__(self, nodes_list):
        object.__init__(self)
        self.nodes_list = nodes_list

    def ping(self, nodes_list=None):
        if nodes_list is None:
            nodes_list = self.nodes_list

        for (node_name, node_adrs) in nodes_list.items():
            command = r"mtr --json --max-ttl 250 --tcp --port 22 --show-ips " + node_adrs
            output = os.popen(command).read()
            print(output)
            mtr_reponse = json.loads(output)
            print(mtr_reponse['report']['hubs'])


def pinger(node_name, t_now, node_adrs, **kwargs):
    r_time = datetime.now()
#     command = r"mtr --json --max-ttl 250 --tcp --port 22 --show-ips " + node_adrs
    command = r"mtr --json --max-ttl 250 --port 22 --show-ips " + node_adrs
    output = os.popen(command).read()
    mtr_reponse = json.loads(output)

    return Measurement(node_name, node_adrs, r_time, t_now, mtr_reponse, MTR_DELAY)


if __name__ == '__main__':
    nodes_list = Nodes().nodes_list
    pinger = Pinger(nodes_list)
    pinger.ping()
