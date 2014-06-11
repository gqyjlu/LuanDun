# -*- coding: utf-8 -*-

'''
Created on 2014年6月11日

@author: prstcsnpr
'''

import json
import logging
import string
import threading

import beanstalkc


producer_manager = None
producer_manager_lock = threading.Lock

def add(url, queue_name, method, params):
    body = {}
    body["url"] = url
    body["method"] = method
    body["params"] = params
    get_producer_manager().put(queue_name, json.dumps(body))
    

def get_producer_manager():
    if producer_manager is None:
        with producer_manager_lock:
            if producer_manager is None:
                producer_manager = ProducerManager()
    return producer_manager

    
class Producer(object):
    
    def __init__(self, host, port, tube="default"):
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
    
    def __init__(self, sockets):
        self.index = -1
        self.producers = []
        self.lock = threading.Lock()
        for socket in sockets:
            self.producers.append(Producer(socket[0], socket[1]))
        
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
        self.sockets = []
        self.lock = threading.Lock()
        for address in addresses.split(","):
            fields = address.split(":")
            socket = [fields[0], string.atoi(fields[1])]
            self.sockets.append(socket)
            
    def __get_producer_group(self, tube):
        with self.lock:
            if tube not in self.producer_groups:
                self.producer_groups[tube] = ProducerGroup(self.sockets)
            return self.producer_groups[tube]
        
    def put(self, tube, body):
        self.__get_producer_group(tube).put(body)
    