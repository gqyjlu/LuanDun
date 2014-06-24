# -*- coding: utf-8 -*-


'''
Created on 2014年6月19日

@author: prstcsnpr
'''

import beanstalkc
from luandun.api import taskqueue


if __name__ == '__main__':
    beanstalkc.Connection(host="localhost", port=11300)
    taskqueue.add(url="http://luandun",
                  queue_name="me",
                  method="POST",
                  params={"name":"n",
                          "city":"c"})