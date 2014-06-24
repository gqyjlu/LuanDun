# -*- coding: utf-8 -*-


'''
Created on 2014年6月23日

@author: prstcsnpr
'''


import threading

from cassandra.cluster import Cluster


cassandra_manager = None
cassandra_manager_lock = threading.Lock()


def get_cassandra_manager():
    global cassandra_manager
    if cassandra_manager is None:
        with cassandra_manager_lock:
            if cassandra_manager is None:
                cassandra_manager = CassandraManager()
                cassandra_manager.initialize("")
    return cassandra_manager


class CassandraManager(object):
    
    def __init__(self):
        self.cluster = Cluster()
        self.session = None
        
    def initialize(self, keyspace):
        self.session = self.cluster.connect(keyspace)
    
    def cql(self, cql):
        pass


class CqlQuery(object):
    
    def __init__(self, cql):
        pass
    

class Model(object):
    
    def cql(self, cql):
        pass
    
    @classmethod
    def get_or_insert(cls, key):
        print type(cls.__name__)
        #print self.__class__.__name__
        #for i in dir(self.__class__):
        #    print i
        #for i in dir(self):
        #    print i
        #    print isinstance(getattr(self, i), Property)
      
    @classmethod      
    def get(cls, key):
        pass
    
    def put(self):
        pass
        

class Property(object):
    def __init__(self, indexed):
        pass

class StringProperty(Property):
    pass