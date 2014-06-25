# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


from cqlengine import columns
from cqlengine.models import Model


class StockModel(Model):
    __keyspace__ = "magicformula"
    __table_name__ = "stock"
    ticker = columns.Text(primary_key=True)
    title = columns.Text()
    market_capital = columns.Float()
    balance = columns.Text()
    profit = columns.Text()
    cash = columns.Text()
    
    @classmethod
    def get_or_create(cls, **kwargs):
        pass