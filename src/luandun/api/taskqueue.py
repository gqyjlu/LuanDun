# -*- coding: utf-8 -*-


'''
Created on 2014年6月11日

@author: prstcsnpr
'''


import json
import logging
import random
import threading

import beanstalkc

from luandun.config import config


producer_manager = None
producer_manager_lock = threading.Lock

worker_manager = None
worker_manager_lock = threading.Lock


def add(url, queue_name, method, params):
    body = {}
    body["url"] = url
    body["method"] = method
    body["params"] = params
    get_producer_manager().put(queue_name, json.dumps(body))
    
    
def get_worker_manager():
    global worker_manager
    if worker_manager is None:
        with worker_manager_lock:
            if worker_manager is None:
                worker_manager = WorkerManager()
    return worker_manager
    

def get_producer_manager():
    global producer_manager
    if producer_manager is None:
        with producer_manager_lock:
            if producer_manager is None:
                producer_manager = ProducerManager(config.get_config_manager().producer_address())
    return producer_manager


class Job(object):
    
    def __init__(self, job):
        self.job = job
        self.body = json.loads(job.body)
        
    def delete(self):
        self.job.delete()
        
    def release(self):
        self.job.release()
        
    def execute(self):
        #url = self.body["url"]
        #method = self.body["method"]
        #params = self.body["params"]
        pass
        
class Worker(object):
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.beanstalk = beanstalkc.Connection(host, port)
            
    def reserve(self, timeout):
        return Job(self.beanstalk.reserve(timeout))
    
    def update_tubes(self, tubes=None):
        if tubes is None:
            tubes = self.beanstalk.tubes()
        for tube in tubes:
            self.beanstalk.watch(tube)
        

class WorkerManager(object):
    
    def __init__(self):
        self.workers = []
    
    def initialize(self, addresses):
        for address in addresses:
            self.workers.append(Worker(address[0], address[1]))
            
    def update_tubes(self, tubes=None):
        for worker in self.workers:
            worker.update_tubes(tubes)
            
    def reserve(self, timeout=None):
        return random.choice(self.workers).reserve(timeout)

    
class Producer(object):
    
    def __init__(self, host, port, tube):
        self.host = host
        self.port = port
        self.tube = tube
        self.beanstalk = beanstalkc.Connection(host, port)
        self.beanstalk.use(tube)
        
    def put(self, body):
        self.beanstalk.put(body)
        
    def __str__(self):
        return self.host + ":" + str(self.port) + "/" + self.tube
    
        
class ProducerGroup(object):
    
    def __init__(self, tube, sockets):
        self.index = -1
        self.tube = tube
        self.producers = []
        self.lock = threading.Lock()
        for socket in sockets:
            self.producers.append(Producer(socket[0], socket[1], self.tube))
            
    def __put(self, body):
        with self.lock:
            i = self.index = (self.index + 1) % len(self.producers)
        try:
            self.producers[i].put(body)
        except beanstalkc.BeanstalkcException as be:
            logging.exception(be + self.producers[i])
            raise be
    
    def put(self, body):
        for i in range(len(self.producers)):
            try:
                self.__put(body)
            except beanstalkc.BeanstalkcException:
                logging.warn("put failure " + i + "times")
                continue
        raise beanstalkc.BeanstalkcException()
    
    
class ProducerManager(object):
    
    def __init__(self, addresses):
        self.producer_groups = {}
        self.sockets = addresses
        self.lock = threading.Lock()
            
    def __get_producer_group(self, tube):
        with self.lock:
            if tube not in self.producer_groups:
                self.producer_groups[tube] = ProducerGroup(tube, self.sockets)
            return self.producer_groups[tube]
        
    def put(self, tube, body):
        self.__get_producer_group(tube).put(body)
    