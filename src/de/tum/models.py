'''
Created on May 21, 2019

@author: foobar
'''


class Measurement(object):
    def __init__(self, node_name, dest_name, r_time, m_time, m_val, m_type):
        self.node_name = node_name
        self.dest_name = dest_name
        # Request time
        self.r_time = r_time
        # Measurement time
        self.m_time = m_time
        self.m_val = m_val
        self.m_type = m_type


class SSHDelay(object):

    def __init__(self, t0, t1, t2, t3, t4, t5):
        self.t0 = t0
        self.t1 = t1
        self.t2 = t2
        self.t3 = t3
        self.t4 = t4
        self.t5 = t5
