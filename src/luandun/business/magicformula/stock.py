# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


import json

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
    formula_item = columns.Text()
    

class FormulaResult(Model):
    __keyspace__ = "magicformula"
    __table_name__ = "formula_result"
    name = columns.Text(primary_key=True)
    result = columns.Text()
    
class MagicFormulaStockView(object):
    
    def __init__(self):
        self.tricker = ""
        self.title = ""
        self.market_capital = 0.0
        self.earnings_date = ""
        self.enterprise_value = 0.0
        self.ebit = 0.0
        self.income = 0.0
        self.tangible_asset = 0.0
        self.rotc_rank = 0
        self.ey_rank = 0
        self.rank = 0
    
    def parse(self, model):
        m = json.loads(model.formula_item)
        self.ticker = model.ticker
        self.title = model.title
        self.market_capital = model.market_capital
        self.earnings_date = m["earningsDate"]
        self.bank_flag = m["bankFlag"]
        self.income = m["income"]
        self.tangible_asset = m["tangibleAsset"]
        self.ebit = m["ebit"]
        self.enterprise_value = m["enterpriseValue"]
    
        
def cmp_rotc(s1, s2):
    if s1.tangible_asset == 0 or s2.tangible_asset == 0:
        if s1.tangible_asset == 0 and s2.tangible_asset == 0:
            return -cmp(s1.income, s2.income)
        elif s1.tangible_asset == 0:
            return -1
        else:
            return 1
    else:
        return -cmp(s1.income / s1.tangible_asset, s2.income / s2.tangible_asset)
    

def cmp_ey(s1, s2):
    if s1.enterprise_value == 0 or s2.enterprise_value == 0:
        if s1.enterprise_value == 0 and s2.enterprise_value == 0:
            return -cmp(s1.ebit, s2.ebit)
        if s1.enterprise_value == 0:
            return -1
        else:
            return 1
    else:
        return -cmp(s1.ebit / s1.enterprise_value, s2.ebit / s2.enterprise_value)
    