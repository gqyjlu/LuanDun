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
    return StockResult.get(key=key)
        
def set_html(ticker, entry):
    entry.save()
    
def create_html(ticker, content):
    key = "html" + ticker
    StockResult.create(key=key, content=content)

def get_json(ticker):
    key = 'json' + ticker
    return StockResult.get(key=key)
        
def set_json(ticker, entry):
    entry.save()
    
def create_json(ticker, content):
    key = "json" + ticker
    StockResult.create(key=key, content=content)
    
