# -*- coding: utf-8 -*-


'''
Created on 2014年6月23日

@author: prstcsnpr
'''


import functools

import asyncmongo
import tornado
from tornado.web import RequestHandler


class UpdateException(Exception):
    pass


class MongoHandler(RequestHandler):
    @property
    def db(self):
        if not hasattr(self, "_db"):
            self._db = asyncmongo.Client(pool_id=self.dbname, 
                                         mincached=0, 
                                         maxcached=10, 
                                         maxconnections=50, 
                                         maxusage=10, 
                                         dbname="magicformula",
                                         host="127.0.0.1",
                                         port=27017)
        return self._db
    
    def __db_onsponse(self, response, error, callback):
        if error:
            raise tornado.web.HTTPError(500, 'QUERY_ERROR')
        callback(response)
        
    def bind(self, callback):
        return functools.partial(self.__db_onsponse, callback=callback)
