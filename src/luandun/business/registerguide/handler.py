# -*- coding: utf-8 -*-


'''
Created on 2014年8月11日

@author: prstcsnpr
'''


import tornado

from luandun.api.db import MongoHandler


class RegisterGuideHandler(MongoHandler):
    @property
    def dbname(self):
        if not hasattr(self, "__dbname"):
            self.__dbname = "registerguide"
            return self.__dbname

class CountHandler(RegisterGuideHandler):
    
    @tornado.web.asynchronous
    def get(self):
        self.db.test.update({"key" : "count"},
                            {"$inc" : {"value" : 1}},
                            safe=True, 
                            upsert=True,
                            callback=self.bind(self.__db_test_update_callback))
        
    def __db_test_update_callback(self, response):
        self.db.test.find_one({"key" : "count"}, callback=self.bind(self.__db_test_find_callback))
        
    def __db_test_find_callback(self, response):
        self.write("Count: " + str(response["value"]))
        self.finish()