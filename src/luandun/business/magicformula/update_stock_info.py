# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


import logging
import re
import string
import urllib
import tornado.web
from luandun.api import taskqueue
from luandun.business.magicformula.stock import StockModel


#ToDo 改成配置
URL_PREFIX="http://localhost:8888"


class UpdateStockInfoHandler(tornado.web.RequestHandler):
    
    def get(self):
        result = urllib.urlopen("http://quote.eastmoney.com/stocklist.html")
        data = result.read().decode("GBK").encode("UTF-8")
        for line in re.compile(r"http:\/\/quote\.eastmoney\.com\/s.*\.html").findall(data):
            ticker = line[29:35]
            if ticker[0] == "0" or ticker[0] == "3" or ticker[0] == "6":
                taskqueue.add(url=URL_PREFIX + "/magicformula/updatemarketcapital", 
                              method="POST", 
                              params={"ticker":ticker})
            

class UpdateMarketCapitalHandler(tornado.web.RequestHandler):
    
    def __get_market_capital(self, ticker):
        if ticker[0] == "6":
            query = "sh" + ticker
        else:
            query = "sz" + ticker
        result = urllib.urlopen("http://qt.gtimg.cn/S?q=" + query)
        if 200 == result.getcode():
            data = result.read().split("~")
            logging.info('The market capital of %s is %s' % (ticker, data[len(data) - 5]))
            if not data[len(data) - 5]:
                logging.warn("There is no market capital for %s" % (ticker))
                return -1.0
            value = string.atof(data[len(data) - 5]) * 100000000
            if not value:
                logging.warn("The market capital of %s is 0" % (ticker))
            return value
        
    def __update_market_capital(self, ticker, value):
        pass
    
    def post(self):
        ticker = self.get_argument("ticker")
        value = self.__get_market_capital(ticker)
        self.__update_market_capital(ticker, value)
        