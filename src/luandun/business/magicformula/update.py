# -*- coding: utf-8 -*-


'''
Created on 2014年8月9日

@author: prstcsnpr
'''


import datetime
import json
import logging
import string

import tornado
from tornado import gen
from tornado import httpclient

from luandun.api import mq
from luandun.business.magicformula import constant
from luandun.business.magicformula.handler import MagicFormulaHandler
from luandun.business.magicformula import parser
from luandun.business.magicformula.parser import EastMoneyHTMLParser
from luandun.business.magicformula.version import StockViewVersion0


class UpdateStockInfoHandler(tornado.web.RequestHandler):
        
    @tornado.web.asynchronous
    def post(self):
        mq.add(url=constant.URL_PREFIX + '/magicformula/updatestocklist',
               keyspace=constant.KEYSPACE,
               method='POST',
               callback=self.__mq_callback)
        
    def __mq_callback(self, *args, **kwargs):
        self.finish()
        

class UpdateStockListHandler(tornado.web.RequestHandler):
        
    @tornado.web.asynchronous
    def post(self):
        self.__update_stock_list()

    @gen.coroutine
    def __update_stock_list(self):
        client = httpclient.AsyncHTTPClient()
        response = yield client.fetch("http://quote.eastmoney.com/stocklist.html")
        data = response.body.decode("GBK").encode("UTF-8")
        parser = EastMoneyHTMLParser()
        parser.feed(data)
        parser.close()
        self.__list = parser.get_list()
        self.__update_stock_title()
        
    def __update_stock_title(self, *args, **kwargs):
        if not self.__list:
            self.finish()
        else:
            s = self.__list.pop()
            mq.add(url=constant.URL_PREFIX + "/magicformula/updatestocktitle", 
                   keyspace=constant.KEYSPACE,
                   method="POST", 
                   params={"ticker" : s[0], "title" : s[1]},
                   callback=self.__update_stock_title)
        
        
class UpdateStockTitleHandler(MagicFormulaHandler):
    
    @tornado.web.asynchronous
    def post(self):
        self.__ticker = self.get_argument("ticker")
        self.__title = self.get_argument("title")
        self.db.stock_model.update({"ticker" : self.__ticker},
                                   {"$set" : {"title" : self.__title}},
                                   safe=True,
                                   upsert=True,
                                   callback=self.bind(self.__db_callback))
    
    def __db_callback(self, response):
        mq.add(url=constant.URL_PREFIX + "/magicformula/updatestockmarketcapital", 
               keyspace=constant.KEYSPACE, 
               method="POST", 
               params={"ticker" : self.__ticker}, 
               callback=self.__mq_callback)
        
    def __mq_callback(self, *args, **kwargs):
        self.finish()
        
        
class UpdateStockMarketCapitalHandler(MagicFormulaHandler):
    
    @gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.__ticker = self.get_argument("ticker")
        if self.__ticker[0] == "6":
            query = "sh" + self.__ticker
        else:
            query = "sz" + self.__ticker
        client = httpclient.AsyncHTTPClient()
        response = yield client.fetch("http://qt.gtimg.cn/S?q=" + query)
        self.__market_capital = self.__get_market_capital(self.__ticker, response.body)
        self.db.stock_model.update({"ticker" : self.__ticker},
                                   {"$set" : {"market_capital" : self.__market_capital}},
                                   safe=True,
                                   upsert=True,
                                   callback=self.bind(self.__db_callback))
        
    def __get_market_capital(self, ticker, body):
        data = body.split("~")
        if len(data) < 5 or not data[len(data) - 5]:
            logging.warn("There is no market capital for %s" % (ticker))
            return -1.0
        logging.info('The market capital of %s is %s' % (ticker, data[len(data) - 5]))
        value = string.atof(data[len(data) - 5]) * 100000000
        if not value:
            logging.warn("The market capital of %s is 0" % (ticker))
        return value
    
    def __db_callback(self, response):
        if self.__market_capital > 0:
            mq.add(url=constant.URL_PREFIX + "/magicformula/updatestockfinancialstatement", 
                   keyspace=constant.KEYSPACE, 
                   method="POST", 
                   params={"ticker" : self.__ticker}, 
                   callback=self.bind(self.__mq_callback))
        else:
            self.finish()
            
    def __mq_callback(self, *args, **kwargs):
        self.finish()


class UpdateStockFinancialStatementHandler(MagicFormulaHandler):
    
    @gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.__ticker = self.get_argument('ticker')
        
        client = httpclient.AsyncHTTPClient()
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_BalanceSheet/displaytype/4/stockid/%s/ctrl/all.phtml" % (self.__ticker)
        response = yield client.fetch(url)
        balance_body = response.body
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_ProfitStatement/displaytype/4/stockid/%s/ctrl/all.phtml" % (self.__ticker)
        response = yield client.fetch(url)
        profit_body = response.body
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_CashFlow/displaytype/4/stockid/%s/ctrl/all.phtml" % (self.__ticker)
        response = yield client.fetch(url)
        cash_body = response.body
        
        if cash_body.find("报告期".encode("GBK")) < 0:
            self.__bank_flag = True
        else:
            self.__bank_flag = False
        self.__balance = parser.parse_sina_stock_financial_statement(balance_body)
        self.__profit = parser.parse_sina_stock_financial_statement(profit_body)
        self.__cash = parser.parse_sina_stock_financial_statement(cash_body)
        
        self.db.stock_model.update({"ticker" : self.__ticker},
                                   {"$set" : {"balance" : self.__balance, "profit" : self.__profit, "cash" : self.__cash, "bank_flag" : self.__bank_flag}},
                                   safe=True,
                                   upsert=True,
                                   callback=self.bind(self.__db_callback))
        
    def __db_callback(self, response):
        mq.add(url=constant.URL_PREFIX + "/magicformula/updatestockdata", 
               keyspace=constant.KEYSPACE, 
               method="POST", 
               params={"ticker" : self.__ticker}, 
               callback=self.bind(self.__mq_callback))
        
    def __mq_callback(self, *args, **kwargs):
        self.finish()
        
        
class UpdateStockDataHandler(MagicFormulaHandler):
    
    @tornado.web.asynchronous
    def post(self):
        self.__ticker = self.get_argument("ticker")
        self.__views = {}
        self.db.stock_model.find_one({"ticker" : self.__ticker}, callback=self.bind(self.__db_stock_model_find_callback))
        
    def __db_stock_model_find_callback(self, response):
        self.__version0 = StockViewVersion0(response)
        self.__title = response["title"]
        self.__bank_flag = response["bank_flag"]
        self.__balance = response["balance"]
        self.__profit = response["profit"]
        self.__cash = response["cash"]
        self.__market_capital = response["market_capital"]
        self.__update_graham_formula_data()
        self.__update_magic_formula_data()
        self.__update_stock_view_0()
        self.db.stock_model.update({"ticker" : self.__ticker},
                                   {"$set" : {"graham_formula" : self.__graham_formula, "magic_formula" : self.__magic_formula}}, 
                                   safe=True,
                                   upsert=True,
                                   callback=self.bind(self.__db_stock_model_update_callback))
        
    def __db_stock_model_update_callback(self, response):
        self.db.stock_view.update({"ticker" : self.__ticker, "version" : 0},
                                  {"$set" : {"data" : self.__views[0]}},
                                  safe=True,
                                  upsert=True,
                                  callback=self.bind(self.__db_stock_view_update_callback))
        
    def __db_stock_view_update_callback(self, response):
        self.finish()
        
    def __update_graham_formula_data(self):
        self.__graham_formula = {}
        earnings_date = self.__get_recent_earnings_date(self.__for_graham_formula)
        self.__graham_formula["recentEarningsDate"] = earnings_date.strftime("%Y%m%d")
        self.__graham_formula["recentOwnersEquityRatio"] = self.__get_recent_owner_s_equity_ratio(earnings_date)
        self.__graham_formula["recentPE"] = self.__get_recent_pe(self.__ticker, earnings_date)
        
    def __for_graham_formula(self, year):
        balance = self.__balance
        profit = self.__profit
        cash = self.__cash
        q4 = datetime.date(year=year, month=12, day=31)
        q3 = datetime.date(year=year, month=9, day=30)
        q2 = datetime.date(year=year, month=6, day=30)
        q1 = datetime.date(year=year, month=3, day=31)
        last_year = year - 1
        if q4.strftime('%Y%m%d') in balance and q4.strftime('%Y%m%d') in profit and q4.strftime('%Y%m%d') in cash:
            return q4
        elif q4.replace(year=last_year).strftime('%Y%m%d') in balance and q4.replace(year=last_year).strftime('%Y%m%d') in profit and q4.replace(year=last_year).strftime('%Y%m%d') in cash:
            if q3.strftime('%Y%m%d') in balance and q3.strftime('%Y%m%d') in profit and q3.strftime('%Y%m%d') in cash and q3.replace(year=last_year).strftime('%Y%m%d') in balance and q3.replace(year=last_year).strftime('%Y%m%d') in profit and q3.replace(year=last_year).strftime('%Y%m%d') in cash:
                return q3
            elif q2.strftime('%Y%m%d') in balance and q2.strftime('%Y%m%d') in profit and q2.strftime('%Y%m%d') in cash and q2.replace(year=last_year).strftime('%Y%m%d') in balance and q2.replace(year=last_year).strftime('%Y%m%d') in profit and q2.replace(year=last_year).strftime('%Y%m%d') in cash:
                return q2
            elif q1.strftime('%Y%m%d') in balance and q1.strftime('%Y%m%d') in profit and q1.strftime('%Y%m%d') in cash and q1.replace(year=last_year).strftime('%Y%m%d') in balance and q1.replace(year=last_year).strftime('%Y%m%d') in profit and q1.replace(year=last_year).strftime('%Y%m%d') in cash:
                return q1
            else:
                return None
        else:
            return None
        
    def __get_recent_owner_s_equity_ratio(self, earnings_date):
        
        if earnings_date is None:
            return "-"
        
        balance = self.__balance
        if not self.__bank_flag:
            total_owner_s_equity = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'归属于母公司股东权益合计'])
            total_assets = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'资产总计'])
        else:
            total_owner_s_equity = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'归属于母公司股东的权益'])
            total_assets = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'资产总计'])
        
        if total_assets == 0:
            return "∞"
        else:
            return total_owner_s_equity / total_assets
        
    def __get_recent_pe(self, ticker, earnings_date):

        if earnings_date is None:
            return "-"
        
        if self.__bank_flag:
            key = u"归属于母公司的净利润"
        else:
            key = u'归属于母公司所有者的净利润'
        profit = self.__profit
        if earnings_date.month == 12:
            net_profit = string.atof(profit[earnings_date.strftime('%Y%m%d')][key])
        else:
            last_year_date = datetime.date(year=earnings_date.year - 1, month=12, day=31).strftime('%Y%m%d')
            last_earnings_date = earnings_date.replace(earnings_date.year - 1).strftime('%Y%m%d')
            net_profit = string.atof(profit[earnings_date.strftime('%Y%m%d')][key]) + string.atof(profit[last_year_date][key]) - string.atof(profit[last_earnings_date][key])
        
        if net_profit == 0:
            return "∞"
        else:
            return self.__market_capital / net_profit
        
    def __update_stock_view_0(self):
        self.__views[0] = self.__version0.data()

    def __update_magic_formula_data(self):
        self.__magic_formula = {}
        earnings_date = self.__get_recent_earnings_date(self.__for_magic_formula)
        self.__magic_formula["recentTA"] = self.__get_recent_ta(earnings_date) 
        self.__magic_formula["recentEBIT"] = self.__get_recent_ebit(earnings_date)
        self.__magic_formula["recentEV"] = self.__get_recent_ev(earnings_date)
        self.__magic_formula["recentIncome"] = self.__get_recent_income(earnings_date)
        self.__magic_formula["recentEarningsDate"] = earnings_date.strftime("%Y%m%d")
        
    def __get_recent_ta(self, earnings_date):
        if earnings_date is None:
            return "-"
        if self.__bank_flag:
            return "-"
        balance = self.__balance
        current_asset = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'流动资产合计'])
        current_liabilities = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'流动负债合计'])
        monetary_fund = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'货币资金'])
        transactional_financial_assets = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'交易性金融资产'])
        excess_cash = max(0, (monetary_fund + transactional_financial_assets) - max(0, current_liabilities - (current_asset - (monetary_fund + transactional_financial_assets))))
        tangible_asset = (string.atof(balance[earnings_date.strftime('%Y%m%d')][u'流动资产合计']) - string.atof(balance[earnings_date.strftime('%Y%m%d')][u'流动负债合计'])
                          + string.atof(balance[earnings_date.strftime('%Y%m%d')][u'短期借款']) + string.atof(balance[earnings_date.strftime('%Y%m%d')][u'应付票据'])
                          + string.atof(balance[earnings_date.strftime('%Y%m%d')][u'一年内到期的非流动负债'])
                          + string.atof(balance[earnings_date.strftime('%Y%m%d')][u'应付短期债券']) + string.atof(balance[earnings_date.strftime('%Y%m%d')][u'固定资产净值'])
                          + string.atof(balance[earnings_date.strftime('%Y%m%d')][u'投资性房地产']) - excess_cash)
        return tangible_asset
    
    def __get_recent_ebit(self, earnings_date):
        if earnings_date is None:
            return "-"
        if self.__bank_flag:
            return "-"
        profit = self.__profit
        if earnings_date.month == 12:
            ebit = (string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业收入']) 
                    - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业成本']) 
                    - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业税金及附加']) 
                    - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'管理费用']) 
                    - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'销售费用']))
        else:
            last_year_date = datetime.date(year=earnings_date.year - 1, month=12, day=31).strftime('%Y%m%d')
            last_earnings_date = earnings_date.replace(earnings_date.year - 1).strftime('%Y%m%d')
            this_earnings_ebit = (string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业收入']) 
                         - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业成本']) 
                         - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业税金及附加']) 
                         - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'管理费用']) 
                         - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'销售费用']))
            last_year_ebit = (string.atof(profit[last_year_date][u'营业收入']) 
                              - string.atof(profit[last_year_date][u'营业成本']) 
                              - string.atof(profit[last_year_date][u'营业税金及附加']) 
                              - string.atof(profit[last_year_date][u'管理费用']) 
                              - string.atof(profit[last_year_date][u'销售费用'])) 
            last_earnings_ebit = (string.atof(profit[last_earnings_date][u'营业收入']) 
                                  - string.atof(profit[last_earnings_date][u'营业成本']) 
                                  - string.atof(profit[last_earnings_date][u'营业税金及附加']) 
                                  - string.atof(profit[last_earnings_date][u'管理费用']) 
                                  - string.atof(profit[last_earnings_date][u'销售费用']))
            ebit = this_earnings_ebit + last_year_ebit - last_earnings_ebit
        return ebit
        
    def __get_recent_ev(self, earnings_date):
        if earnings_date is None:
            return "-"
        if self.__bank_flag:
            return "-"
        balance = self.__balance
        current_asset = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'流动资产合计'])
        current_liabilities = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'流动负债合计'])
        short_term_loans = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'短期借款'])
        notes_payable = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'应付票据'])
        a_maturity_of_non_current_liabilities = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'一年内到期的非流动负债'])
        cope_with_short_term_bond = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'应付短期债券'])
        monetary_fund = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'货币资金'])
        transactional_financial_assets = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'交易性金融资产'])
        long_term_loans = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'长期借款'])
        bonds_payable = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'应付债券'])
        minority_equity = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'少数股东权益'])
        available_for_sale_financial_assets = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'可供出售金融资产'])
        hold_expires_investment = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'持有至到期投资'])
        delay_income_tax_liabilities = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'递延所得税负债'])
        excess_cash = max(0, (monetary_fund + transactional_financial_assets) - max(0, current_liabilities - (current_asset - (monetary_fund + transactional_financial_assets))))
        enterprise_value = (short_term_loans + notes_payable + a_maturity_of_non_current_liabilities
                            + cope_with_short_term_bond + long_term_loans
                            + bonds_payable + minority_equity
                            - available_for_sale_financial_assets - hold_expires_investment
                            + delay_income_tax_liabilities - excess_cash + self.__market_capital)
        return enterprise_value
    
    def __get_recent_income(self, earnings_date):
        if earnings_date is None:
            return "-"
        if self.__bank_flag:
            return "-"
        profit = self.__profit
        if earnings_date.month == 12:
            income = (string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业收入']) 
                    - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业成本']) 
                    - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业税金及附加']) 
                    - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'管理费用']) 
                    - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'销售费用'])
                    + string.atof(profit[earnings_date.strftime('%Y%m%d')][u'其中:对联营企业和合营企业的投资收益']))
        else:
            last_year_date = datetime.date(year=earnings_date.year - 1, month=12, day=31).strftime('%Y%m%d')
            last_earnings_date = earnings_date.replace(earnings_date.year - 1).strftime('%Y%m%d')
            this_earnings_income = (string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业收入']) 
                         - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业成本']) 
                         - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'营业税金及附加']) 
                         - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'管理费用']) 
                         - string.atof(profit[earnings_date.strftime('%Y%m%d')][u'销售费用'])
                         + string.atof(profit[earnings_date.strftime('%Y%m%d')][u'其中:对联营企业和合营企业的投资收益']))
            last_year_income = (string.atof(profit[last_year_date][u'营业收入']) 
                              - string.atof(profit[last_year_date][u'营业成本']) 
                              - string.atof(profit[last_year_date][u'营业税金及附加']) 
                              - string.atof(profit[last_year_date][u'管理费用']) 
                              - string.atof(profit[last_year_date][u'销售费用'])
                              + string.atof(profit[last_year_date][u'其中:对联营企业和合营企业的投资收益'])) 
            last_earnings_income = (string.atof(profit[last_earnings_date][u'营业收入']) 
                                  - string.atof(profit[last_earnings_date][u'营业成本']) 
                                  - string.atof(profit[last_earnings_date][u'营业税金及附加']) 
                                  - string.atof(profit[last_earnings_date][u'管理费用']) 
                                  - string.atof(profit[last_earnings_date][u'销售费用'])
                                  + string.atof(profit[last_earnings_date][u'其中:对联营企业和合营企业的投资收益']))
            income = this_earnings_income + last_year_income - last_earnings_income
        return income
        
    def __get_recent_earnings_date(self, callback):
        year = datetime.date.today().year
        earnings_date = None
        for i in range(3):
            earnings_date = callback(year - i)
            if earnings_date is not None:
                break
        return earnings_date
    
    def __for_magic_formula(self, year):
        balance = self.__balance
        profit = self.__profit
        cash = self.__cash
        q4 = datetime.date(year=year, month=12, day=31)
        q2 = datetime.date(year=year, month=6, day=30)
        last_year = year - 1
        if q4.strftime('%Y%m%d') in balance and q4.strftime('%Y%m%d') in profit and q4.strftime('%Y%m%d') in cash:
            return q4
        elif q4.replace(year=last_year).strftime('%Y%m%d') in balance and q4.replace(year=last_year).strftime('%Y%m%d') in profit and q4.replace(year=last_year).strftime('%Y%m%d') in cash:
            if q2.strftime('%Y%m%d') in balance and q2.strftime('%Y%m%d') in profit and q2.strftime('%Y%m%d') in cash and q2.replace(year=last_year).strftime('%Y%m%d') in balance and q2.replace(year=last_year).strftime('%Y%m%d') in profit and q2.replace(year=last_year).strftime('%Y%m%d') in cash:
                return q2
            else:
                return None
        else:
            return None


class UpdateGrahamFormulaHandler(MagicFormulaHandler):
    
    @tornado.web.asynchronous
    def post(self):
        self.db.stock_model.find({},
                                 {"title" : 1, "graham_formula" : 1, "ticker" : 1, "market_capital" : 1}, 
                                 limit = 10000, 
                                 callback=self.bind(self.__db_find_callback))
        
    def __db_find_callback(self, response):
        stocks = []
        for item in response:
            if "graham_formula" not in item:
                continue
            s = item["graham_formula"]
            if s["recentOwnersEquityRatio"] >= 0.5 and s["recentOwnersEquityRatio"] <= 1 and s["recentPE"] <= 10 and s["recentPE"] > 0:
                stock = {}
                stock["PE"] = "%.1f" % (s["recentPE"])
                stock["ownersEquityRatio"] = "%.1f%%" % (s["recentOwnersEquityRatio"] * 100)
                stock["earningsDate"] = s["recentEarningsDate"]
                stock["title"] = item["title"]
                stock["ticker"] = item["ticker"]
                stock["marketCapital"] = "%.2f亿" % (item["market_capital"] / 100000000)
                stocks.append(stock)
        results = sorted(stocks, cmp=lambda a, b : cmp(a["ticker"], b["ticker"]))
        json_result = json.dumps(results)
        self.db.view.update({"key" : "grahamformula_json"},
                            {"$set" : {"value" : json_result}},
                            safe=True,
                            upsert=True,
                            callback=self.bind(self.__db_update_callback))
    
    def __db_update_callback(self, response):
        self.finish()
        
        
class UpdateMagicFormulaHandler(MagicFormulaHandler):
    
    @tornado.web.asynchronous
    def post(self):
        self.db.stock_model.find({},
                                 {"title" : 1, "magic_formula" : 1, "ticker" : 1, "market_capital" : 1, "bank_flag" : 1, "subcategory" : 1},
                                 limit=10000,
                                 callback=self.bind(self.__db_find_callback))
        
    def __db_find_callback(self, response):
        stocks = []
        for item in response:
            if "magic_formula" not in item:
                continue
            if item["bank_flag"]:
                continue
            if "subcategory" in item:
                if item["subcategory"].find("D") > 0 or item["subcategory"].find("G") > 0 or item["subcategory"].find("N") > 0 or item["subcategory"].find("J") > 0:
                    continue
            stocks.append(item) 
        stocks = self.__magicformula(stocks)
        position = 30
        while position<len(stocks):
            if stocks[position]["rank"] == stocks[position - 1]["rank"]:
                position = position + 1
            else:
                break
        results = []
        for s in stocks[0 : position]:
            result = {}
            result["rank"] = s["rank"]
            result["ticker"] = s["ticker"]
            result["title"] = s["title"]
            result["marketCapital"] = "%.2f亿" % (s["market_capital"] / 100000000)
            result["earningsDate"] = s["magic_formula"]["recentEarningsDate"]
            if s["magic_formula"]["recentTA"] == 0:
                result["rotc"] = "∞"
            else:
                result["rotc"] = "%d%%" % (s["magic_formula"]["recentEBIT"] * 100 / s["magic_formula"]["recentTA"])
            if s["magic_formula"]["recentEV"] == 0:
                result["ey"] = "∞"
            else:
                result["ey"] = "%d%%" % (s["magic_formula"]["recentIncome"] * 100 / s["magic_formula"]["recentEV"])
            results.append(result)
        self.db.view.update({"key" : "magicformula_json"},
                            {"$set" : {"value" : json.dumps(results)}},
                            safe=True,
                            upsert=True,
                            callback=self.bind(self.__db_update_callback))
        
    def __db_update_callback(self, response):
        self.finish()
        
    def __magicformula(self, stocks):
        results = sorted(stocks, cmp=lambda a, b : self.__cmp_rotc(a, b))
        for i in range(len(results)):
            if i != 0 and self.__cmp_rotc(results[i], results[i-1]) == 0:
                results[i]["rotcRank"] = results[i-1]["rotcRank"]
            else:
                results[i]["rotcRank"] = i + 1
        results = sorted(results, cmp=lambda a, b : self.__cmp_ey(a, b))
        for i in range(len(results)):
            if i != 0 and self.__cmp_ey(results[i], results[i-1]) == 0:
                results[i]["eyRank"] = results[i-1]["eyRank"]
            else:
                results[i]["eyRank"] = i + 1
        results = sorted(results, key=lambda stock : stock["rotcRank"] + stock["eyRank"])
        for i in range(len(results)):
            if i != 0 and results[i]["rotcRank"] + results[i]["eyRank"] == results[i-1]["rotcRank"] + results[i-1]["eyRank"]:
                results[i]["rank"] = results[i-1]["rank"]
            else:
                results[i]["rank"] = i + 1
        return results
    
    def __cmp_ey(self, s1, s2):
        if s1["magic_formula"]["recentEV"] * s2["magic_formula"]["recentEV"] == 0:
            if s1["magic_formula"]["recentEV"] == 0:
                return -1
            else:
                return 1
        else:
            return -cmp(s1["magic_formula"]["recentIncome"] / s1["magic_formula"]["recentEV"], s2["magic_formula"]["recentIncome"] / s2["magic_formula"]["recentEV"])
    
    def __cmp_rotc(self, s1, s2):
        if s1["magic_formula"]["recentTA"] * s2["magic_formula"]["recentTA"] == 0:
            if s1["magic_formula"]["recentTA"] == 0:
                return -1
            else:
                return 1
        else:
            return -cmp(s1["magic_formula"]["recentEBIT"] / s1["magic_formula"]["recentTA"], s2["magic_formula"]["recentEBIT"] / s2["magic_formula"]["recentTA"])
    