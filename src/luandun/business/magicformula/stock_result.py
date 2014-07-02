# -*- coding: utf-8 -*-


from cqlengine import columns
from cqlengine.models import Model


class StockResult(Model):
    __keyspace__ = "magicformula"
    __table_name__ = "stock_result"
    key = columns.Text(primary_key=True)
    content = columns.Text()
    
def get_html(ticker):
    key = 'html' + ticker
    return StockResult.create(key=key)
        
def set_html(ticker, entry):
    entry.save()

def get_json(ticker):
    key = 'json' + ticker
    return StockResult.create(key=key)
        
def set_json(ticker, entry):
    entry.save()
