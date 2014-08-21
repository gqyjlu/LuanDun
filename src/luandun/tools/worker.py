#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2014年6月11日

@author: prstcsnpr
'''


import getopt
import logging
import string
import sys
import threading

from luandun.api import taskqueue
from luandun import config


def usage():
    print "worker.py usage:"
    print "-h, --help: print help message."
    print "-v, --version: print version message"
    print "-t, --tube: set taskqueue tube"
    print "-a, --address: set taskqueue address(default localhost:11300)"
    print "-n, --number: set the number of workers(default: 1)"
    
    
def version():
    print "worker.py 0.1.0"
    
    
class WorkerThread(threading.Thread):
    
    def run(self):
        while True:
            try:
                job = taskqueue.get_worker_manager().reserve()
                try:
                    job.execute()
                    job.delete()
                except Exception as e:
                    logging.exception(e)
                    job.release()
            except Exception as e:
                logging.exception(e)
    
    
def main(argv):
    try:
        options, args = getopt.getopt(sys.argv[1:], "hvt:a:n:", ["help", "version", "tube=", "address=", "number="])
    except getopt.GetoptError:
        usage()
        sys.exit(1)
    number = 1
    address = "localhost:11300"
    tube = None
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
            number = string.atoi(a)
        else:
            print "unhandled option: " + o
            sys.exit(2)
    taskqueue.get_worker_manager().initialize(config.parse_address(address))
    taskqueue.get_worker_manager().update_tubes(config.parse_tube(tube))
    threads = []
    for i in range(number):
        threads.append(WorkerThread())
        threads[i].setDaemon(True)
        threads[i].start()
    for i in range(number):
        threads[i].join()
    
            
if __name__ == "__main__":
    main(sys.argv)
