# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


import beanstalkc


if __name__ == '__main__':
    b = beanstalkc.Connection(host="127.0.0.1", port=11300)
    b.tubes()