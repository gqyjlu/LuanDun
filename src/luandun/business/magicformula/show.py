# -*- coding: utf-8 -*-


'''
Created on 2014年8月15日

@author: prstcsnpr
'''


import datetime
import json

import tornado

from luandun.business.magicformula.handler import MagicFormulaHandler


class ShowMagicFormulaHandler(MagicFormulaHandler):
    
    @tornado.web.asynchronous
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.db.view.find_one({"key" : "magicformula_json"}, callback=self.bind(self.__db_callback))
        
    def __db_callback(self, response):
        result = {}
        result["list"] = json.loads(response["value"])
        result["error"] = 0
        result["description"] = "No error"
        result["date"] = datetime.date.today().strftime("%Y%m%d")
        self.write(json.dumps(result))
        self.finish()


class ShowGrahamFormulaHandler(MagicFormulaHandler):
    
    @tornado.web.asynchronous
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.db.view.find_one({"key" : "grahamformula_json"}, callback=self.bind(self.__db_callback))
        
    def __db_callback(self, response):
        result = {}
        result["list"] = json.loads(response["value"])
        result['error'] = 0
        result['description'] = 'No error'
        result['date'] = datetime.date.today().strftime("%Y%m%d")
        self.write(json.dumps(result))
        self.finish()
        

class ShowStockDataHandler(MagicFormulaHandler):
    
    @tornado.web.asynchronous
    def get(self, ticker):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.__ticker = ticker
        self.db.stock_view.find_one({"ticker" : self.__ticker}, callback=self.bind(self.__db_callback))
        
    def __db_callback(self, response):
        result = {}
        result["data"] = response["data"]
        result["error"] = 0
        result["description"] = "No error"
        result["date"] = datetime.date.today().strftime("%Y%m%d")
        self.write(json.dumps(result))
        self.finish()
        
