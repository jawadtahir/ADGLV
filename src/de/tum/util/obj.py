'''
Created on Aug 16, 2019

@author: foobar
'''


class obj(object):
    '''
    dict to object
    '''

    def __init__(self, d):
        '''
        Constructor
        '''
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [obj(x) if isinstance(
                    x, dict) else x for x in b])
            else:
                setattr(self, a, obj(b) if isinstance(b, dict) else b)
