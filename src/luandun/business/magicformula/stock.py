# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


from cqlengine import columns
from cqlengine.models import Model


class Stock(Model):
    __keyspace__ = "magicformula"
    __table_name__ = "stock"
    ticker = columns.Text(primary_key=True)
    title = columns.Text()
    market_capital = columns.Float()
    market_capital_date = columns.Date()
    bank_flag = columns.Boolean()
    ebit = columns.Float()
    enterprise_value = columns.Float()
    income = columns.Float()
    tangible_asset = columns.Float()
    ownership_interest = columns.Float()
    net_profit = columns.Float()
    total_assets = columns.Float()
    current_assets = columns.Float()
    total_liability = columns.Float()
    earnings_date = columns.Date()
    category = columns.Text()
    subcategory = columns.Text()
    

class StockTitle(Model):
    __keyspace__ = "magicformula"
    __table_name__ = "stock_title"
    ticker = columns.Text(primary_key=True)
    title = columns.Text()
    
    
class StockMarketCapital(Model):
    __keyspace__ = "magicformula"
    __table_name__ = "stock_market_capital"
    ticker = columns.Text(primary_key=True)
    market_capital = columns.Float()
    
    
class StockEarnings(Model):
    __keyspace__ = "magicformula"
    __table_name__ = "stock_earnings"
    ticker = columns.Text(primary_key=True)
    balance = columns.Text()
    profit = columns.Text()
    cash = columns.Text()
    
    
class NetCurrentAssetApproachStockView(object):
    
    def __init__(self):
        self.ticker = ''
        self.title = ''
        self.market_capital = 0.0
        self.net_profit = 0.0
        self.ownership_interest = 0.0
        self.total_liability = 0.0
        self.current_assets = 0.0
        self.category = ""
        self.subcategory = ""
        self.earnings_date = None
        self.pe = 0.0
        self.pb = 0.0
        self.roe = 0.0
        self.net_current_assets = 0.0
        self.color = ""
        
    def parse(self, s):
        self.ticker = s.ticker
        self.title = s.title
        self.market_capital = s.market_capital
        self.net_profit = s.net_profit
        self.ownership_interest = s.ownership_interest
        self.total_liability = s.total_liability
        self.current_assets = s.current_assets
        self.earnings_date = s.earnings_date
        self.category = s.category
        self.subcategory = s.subcategory
        self.pe = self.market_capital / self.net_profit
        self.pb = self.market_capital / self.ownership_interest
        self.roe = self.net_profit * 100 / self.ownership_interest
        self.net_current_assets = self.current_assets - self.total_liability
        
    def format(self):
        if 3 * self.market_capital < 2 * self.net_current_assets:
            self.color = "green"
        else:
            self.color = "red"
        self.market_capital = "%.2f亿" % (self.market_capital / 100000000)
        self.roe = "%.1f%%" % (self.roe)
        self.pe = "%.1f" % (self.pe)
        self.pb = "%.1f" % (self.pb)
        self.net_current_assets = "%.2f亿" % (self.net_current_assets / 100000000)
        self.earnings_date = self.earnings_date.strftime("%Y%m%d")
        
   
    
class GrahamFormulaStockView(object):
    
    def __init__(self):
        self.ticker = ''
        self.title = ''
        self.market_capital = 0.0
        self.net_profit = 0.0
        self.ownership_interest = 0.0
        self.total_assets = 0.0
        self.total_liability = 0.0
        self.category = ""
        self.subcategory = ""
        self.earnings_date = None
        self.pe = 0.0
        self.pb = 0.0
        self.roe = 0.0
        self.debt_asset_ratio = 0.0
        self.color = ""
        
    def format(self):
        if self.roe >= 15:
            self.color = "#119911"
        else:
            self.color = "#991111"
        self.market_capital = "%.2f亿" % (self.market_capital / 100000000)
        self.roe = "%.1f%%" % (self.roe)
        self.pe = "%.1f" % (self.pe)
        self.pb = "%.1f" % (self.pb)
        self.debt_asset_ratio = "%.1f%%" % (self.debt_asset_ratio)
        self.earnings_date = self.earnings_date.strftime("%Y%m%d")
            
    def parse(self, s):
        self.ticker = s.ticker
        self.title = s.title
        self.market_capital = s.market_capital
        self.net_profit = s.net_profit
        self.ownership_interest = s.ownership_interest
        self.total_assets = s.total_assets
        self.total_liability = s.total_liability
        self.earnings_date = s.earnings_date
        self.category = s.category
        self.subcategory = s.subcategory
        self.pe = self.market_capital / self.net_profit
        self.pb = self.market_capital / self.ownership_interest
        self.roe = self.net_profit * 100 / self.ownership_interest
        self.debt_asset_ratio = self.total_liability * 100 / self.total_assets
    
class MagicFormulaStockView(object):
    
    def __init__(self):
        self.rank = 0
        self.roic_rank = 0
        self.roic = 0.0
        self.ebit_ev_rank = 0
        self.ebit_ev = 0.0
        self.ticker = ''
        self.title = ''
        self.market_capital = 0.0
        self.income = 0.0
        self.tangible_asset = 0.0
        self.ebit = 0.0
        self.enterprise_value = 0.0
        self.net_profit = 0.0
        self.ownership_interest = 0.0
        self.total_assets = 0.0
        self.total_liability = 0.0
        self.category = ""
        self.subcategory = ""
        self.earnings_date = None
        self.pe = 0.0
        self.pb = 0.0
        self.roe = 0.0
        self.debt_asset_ratio = 0.0
        self.color = ""
        
    def format(self):
        if self.roe >= 15 and self.pe <= 15 and self.pe > 0:
            self.color = "#119911"
        else:
            self.color = "#991111"
        if self.enterprise_value != 0.0:
            self.ebit_ev = "%d%%" % (self.ebit_ev * 100)
        else:
            self.ebit_ev = "∞"
        if self.tangible_asset != 0.0:
            self.roic = "%d%%" % (self.roic * 100)
        else:
            self.roic = "∞"
        self.market_capital = "%.2f亿" % (self.market_capital / 100000000)
        self.roe = "%.1f%%" % (self.roe)
        self.pe = "%.1f" % (self.pe)
        self.pb = "%.1f" % (self.pb)
        self.debt_asset_ratio = "%.1f%%" % (self.debt_asset_ratio)
        self.earnings_date = self.earnings_date.strftime("%Y%m%d")
            
    def parse(self, s):
        self.ticker = s.ticker
        self.title = s.title
        self.market_capital = s.market_capital
        self.income = s.income
        self.tangible_asset = s.tangible_asset
        self.ebit = s.ebit
        self.enterprise_value = s.enterprise_value + s.market_capital
        self.net_profit = s.net_profit
        self.ownership_interest = s.ownership_interest
        self.total_assets = s.total_assets
        self.total_liability = s.total_liability
        self.earnings_date = s.earnings_date
        self.category = s.category
        self.subcategory = s.subcategory
        self.pe = self.market_capital / self.net_profit
        self.pb = self.market_capital / self.ownership_interest
        self.roe = self.net_profit * 100 / self.ownership_interest
        self.debt_asset_ratio = self.total_liability * 100 / self.total_assets
        if self.tangible_asset != 0.0:
            self.roic = self.income / self.tangible_asset
        else:
            self.roic = '∞'
        if self.enterprise_value != 0.0:
            self.ebit_ev = self.ebit / self.enterprise_value
        else:
            self.ebit_ev = '∞'
            

def cmp_roic(s1, s2):
    if s1.tangible_asset * s2.tangible_asset == 0:
        if s1.tangible_asset == 0:
            return -1
        else:
            return 1
    else:
        return -cmp(s1.roic, s2.roic)
    

def cmp_ebit_ev(s1, s2):
    if s1.enterprise_value * s2.enterprise_value == 0:
        if s1.enterprise_value == 0:
            return -1
        else:
            return 1
    else:
        return -cmp(s1.ebit_ev, s2.ebit_ev)
    
    
def get(ticker):
    return Stock.get(ticker=ticker)
    #entry = memcache.get(ticker)
    #if entry is None:
    #    entry = Stock.get_or_insert(ticker)
    #    memcache.add(ticker, entry)
    #return entry


def put(ticker, entry):
    entry.save()
    #memcache.set(ticker, entry)