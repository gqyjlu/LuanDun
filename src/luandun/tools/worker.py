#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2014年6月11日

@author: prstcsnpr
'''


import getopt
import sys
import threading
from luandun.api import taskqueue


def usage():
    print "worker.py usage:"
    print "-h, --help: print help message."
    print "-v, --version: print version message"
    print "-t, --tube: set taskqueue tube"
    print "-a, --address: set taskqueue address"
    print "-n, --number: set the number of workers"
    
    
def version():
    print "worker.py 0.1.0"
    
    
class WorkerThread(object):
    def __init__(self):
        
    
    
def main(argv):
    try:
        options, args = getopt.getopt(sys.argv[1:], "hvt:a:n:", ["help", "version", "tube=", "address=", "number="])
    except getopt.GetoptError:
        usage()
        sys.exit(1)  
    for o, a in options:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-v", "--version"):
            version()
            sys.exit(0)
        elif o in ("-t", "--tube"):
            tube = a
        elif o in ("-a", "--address"):
            address = a
        elif o in ("-n", "--number"):
            number = a
        else:
            print "unhandled option: " + o
            sys.exit(2)
    taskqueue.get_worker_manager().initialize(address)
    
            
if __name__ == "__main__":
    main(sys.argv)
