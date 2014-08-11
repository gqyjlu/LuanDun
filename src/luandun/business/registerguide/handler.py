# -*- coding: utf-8 -*-


'''
Created on 2014年8月11日

@author: prstcsnpr
'''

from luandun.api.db import MongoHandler


class RegisterGuideHandler(MongoHandler):
    @property
    def dbname(self):
        if not hasattr(self, "__dbname"):
            self.__dbname = "registerguide"
            return self.__dbname

class SampleHandler(RegisterGuideHandler):
    
    def get(self):
        self.write("Hello, world!")