# -*- coding: utf-8 -*-


'''
Created on 2014年8月4日

@author: prstcsnpr
'''


import json
import logging
import random
import uuid

from beanstalkt.beanstalkt import Client

from luandun import config


class TooManyConnectionsException(Exception):
    pass


class ProgrammingException(Exception):
    pass


class ProducerManager(object):
    
    def __init__(self):
        self.__producer_groups = {}
        
    def get_producer_group(self, tube):
        if tube not in self.__producer_groups:
            addresses = config.get_config_manager().mq_address()
            self.__producer_groups[tube] = []
            for address in addresses:
                self.__producer_groups[tube].append(ProducerGroup(host=address[0], port=address[1], tube=tube))
        return random.choice(self.__producer_groups[tube])
    
    def close_idle_producer_groups(self, tube=None):
        if tube:
            if tube not in self.__producer_groups:
                raise ProgrammingException("pool %r does not exist" % tube)
            else:
                producer_group = self.__producer_groups[tube]
                producer_group.close()
        else:
            for tube, producer in self.__producer_groups.items():
                producer.close()
                

producer_manager = ProducerManager()


class Producer(object):
    
    def __init__(self, host, port, tube, group):
        self.__host = host
        self.__port = port
        self.__tube = tube
        self.__group = group
        self.__is_closed = True
        self.__uuid = uuid.uuid4()
        self.__client = Client(host, port)
        
    def __put_response(self, *args, **kwargs):
        self.__put_cb(args, kwargs)
        self.complete()
        
    def __use_response(self, *args, **kwargs):
        self.__client.put(body=self.__put_body, callback=self.__put_response)
        self.__is_closed = False
        
    def __connect_response(self, *args, **kwargs):
        self.__client.use(self.__tube, self.__use_response)
        
    def put(self, body, cb):
        self.__put_body = body
        self.__put_cb = cb
        if self.__is_closed:
            self.__client.connect(self.__connect_response)
        else:
            self.__client.put(body=body, callback=self.__put_response)
            
    def close(self):
        self.__client.close(None)
    
    def complete(self):
        self.__group.cache(self)


class ProducerGroup(object):
    
    def __init__(self, numcached=10, maxconnections=0, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs
        self.__numcached = numcached
        self.__maxconnections = maxconnections
        self.__idle_cache = []
        self.__connections = 0
        self.__uuid=uuid.uuid4()
        
        idle = [self.connection() for i in range(numcached)]
        while idle:
            self.cache(idle.pop())
            
    def new_connection(self):
        args = self.__args
        kwargs = self.__kwargs
        kwargs['group'] = self
        return Producer(*args, **kwargs)

    def connection(self):
        if (self.__maxconnections and self.__connections >= self.__maxconnections):
            raise TooManyConnectionsException("%d connections are already equal to the max: %d" % (self.__connections, self.__maxconnections))
        try:
            con = self.__idle_cache.pop(0)
        except IndexError:
            con = self.new_connection()
        self.__connections += 1
        return con

    def cache(self, con):
        if con in self.__idle_cache:
            return
        if not self.__numcached or len(self.__idle_cache) < self.__numcached:
            self.__idle_cache.append(con)
        else:
            logging.debug('dropping connection. connection pool (%s) is full. maxcached %s' % (len(self.__idle_cache), self.__numcached))
            con.close()
        self.__connections -= 1
    
    def close(self):
        while self.__idle_cache:
            con = self.__idle_cache.pop(0)
            try:
                con.close()
            except Exception as e:
                logging.exception(e)
            self.__connections -=1
    
    
def add(url, keyspace, queue_name=None, method="GET", params={}, callback=None):
    body = {}
    body["url"] = url
    body["method"] = method
    body["params"] = params
    if queue_name is None:
        tube = keyspace
    else:
        tube = keyspace + "_" + queue_name
    c = producer_manager.get_producer_group(tube).connection()
    c.put(json.dumps(body), callback)
