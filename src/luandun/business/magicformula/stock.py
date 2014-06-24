# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


class StockModel(object):
    
    def __init__(self):
        self.ticker = ""
        self.title = ""
        self.market_capital = 0.0
        self.financial_statement = ""

    @classmethod  
    def get_or_insert(cls, ticker):
        pass

    @classmethod
    def put(cls):
        pass