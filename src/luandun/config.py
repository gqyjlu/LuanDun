# -*- coding: utf-8 -*-


'''
Created on 2014年6月19日

@author: prstcsnpr
'''


import ConfigParser
import string
import threading
import os


config_manager = None
config_manager_lock = threading.Lock()


def parse_address(s):
    addresses = []
    for address in s.split(","):
        fields = address.split(":")
        addresses.append([fields[0], string.atoi(fields[1])])
    return addresses

def parse_tube(s):
    tubes = []
    for tube in s.split(","):
        tubes.append(tube)
    return tubes


def get_config_manager():
    global config_manager
    if config_manager is None:
        with config_manager_lock:
            if config_manager is None:
                config_manager = ConfigManager()
                config_manager.initialize()
    return config_manager


class ConfigManager(object):
    
    def __init__(self):
        self.__config = ConfigParser.ConfigParser()
    
    def initialize(self):
        self.__config.read(os.path.expanduser("~/.luandun.ini"))
        
    def business(self):
        return self.__business
        
    def producer_address(self):
        return parse_address(self.__config.get("producer", "address"))
    
    def mq_address(self):
        return parse_address(self.__config.get("mq", "address"))
