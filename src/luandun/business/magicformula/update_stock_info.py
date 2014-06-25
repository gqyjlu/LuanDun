# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


from HTMLParser import HTMLParser
import logging
import re
import string
import urllib
import tornado.web
from luandun.api import taskqueue
from luandun.business.magicformula.stock import StockModel
from luandun.exception import LuanDunException


#ToDo 改成配置
URL_PREFIX="http://localhost:8888"
KEYSPACE="magicformula"


class UpdateStockInfoHandler(tornado.web.RequestHandler):
    
    def get(self):
        result = urllib.urlopen("http://quote.eastmoney.com/stocklist.html")
        if 200 == result.getcode():
            data = result.read().decode("GBK").encode("UTF-8")
            parser = EastMoneyHTMLParser()
            parser.feed(data)
            parser.close()
        else:
            raise LuanDunException("http code: " + str(result.getcode()))
        
        
class UpdateTitleHandler(tornado.web.RequestHandler):
    
    def post(self):
        ticker = self.get_argument("ticker")
        title = self.get_argument("title")
        StockModel.create(ticker=ticker, title=title)
        taskqueue.add(url=URL_PREFIX + "/magicformula/updatemarketcapital",
                      keyspace=KEYSPACE, 
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
        else:
            raise LuanDunException("http code: " + str(result.getcode()))
        
    def __update_market_capital(self, ticker, value):
        StockModel.create(ticker=ticker, market_capital=value)
    
    def post(self):
        ticker = self.get_argument("ticker")
        value = self.__get_market_capital(ticker)
        StockModel.create(ticker=ticker, market_capital=value)
        self.__update_market_capital(ticker, value)
        

class EastMoneyHTMLParser(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)
        self.__flag = False
        
    def handle_starttag(self, tag, attrs):
        if "a" == tag:
            for attr in attrs:
                if "href" == attr[0] and attr[1].find("http://quote.eastmoney.com/s") >= 0:
                    self.__flag = True
        
    def handle_endtag(self, tag):
        if "a" == tag and self.__flag:
            self.__flag = False
        
    def handle_data(self, data):
        if self.__flag:
            line = re.split("[()]+", data)
            ticker = line[1].strip()
            title = line[0].strip()
            if ticker[0:2] == "00" or ticker[0] == "3" or ticker[0] == "6":
                taskqueue.add(url=URL_PREFIX + "/magicformula/updatetitle", 
                              keyspace=KEYSPACE,
                              method="POST", 
                              params={"ticker":ticker, "title":title})
        