# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


import datetime
from HTMLParser import HTMLParser
import json
import logging
import re
import string
import urllib

import tornado.web

from luandun.api import taskqueue
from luandun.business.magicformula.exception import MagicFormulaException
from luandun.business.magicformula import stock
from luandun.business.magicformula.stock import FormulaResult
from luandun.business.magicformula.stock import MagicFormulaStockView
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
        taskqueue.add(url=URL_PREFIX + "/magicformula/updatefinancialstatement",
                      keyspace=KEYSPACE,
                      method="POST",
                      params={"ticker":ticker})
        
        
class UpdateFinancialStatementHandler(tornado.web.RequestHandler):
    
    def __parse(self, data):
        m = {}
        lines = data.split('\n')
        for line in lines:
            fields = line.split('\t')
            for i in range(len(fields) - 2):
                if i + 1 not in m:
                    m[i + 1] = {}
                m[i + 1][fields[0]] = fields[i + 1]
        results = {}
        for k in m:
            if '报表日期' in m[k]:
                results[m[k]['报表日期']] = m[k]
        if not results:
            raise MagicFormulaException('Content is %s' % (data))
        return results
    
    def __get_page_content(self, url):
        result = urllib.urlopen(url)
        if 200 == result.getcode():
            return result.read().decode('GBK').encode('UTF-8')
        else:
            raise LuanDunException("http code: " + str(result.getcode()))
    
    def __get_balance(self, ticker):
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_BalanceSheet/displaytype/4/stockid/%s/ctrl/all.phtml" % (ticker)
        data = self.__get_page_content(url)
        return self.__parse(data)
    
    def __load_balance(self, ticker):
        value = self.__get_balance(ticker)
        StockModel.create(ticker=ticker, balance=json.dumps(value))
    
    def __get_profit(self, ticker):
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_ProfitStatement/displaytype/4/stockid/%s/ctrl/all.phtml" % (ticker)
        data = self.__get_page_content(url)
        return self.__parse(data)
    
    def __load_profit(self, ticker):
        value = self.__get_profit(ticker)
        StockModel.create(ticker=ticker, profit=json.dumps(value))
    
    def __load_cash(self, ticker):
        pass
    
    def post(self):
        ticker = self.get_argument("ticker")
        if StockModel.get(ticker=ticker).market_capital > 0:
            self.__load_balance(ticker)
            self.__load_profit(ticker)
            self.__load_cash(ticker)
            taskqueue.add(url=URL_PREFIX + "/magicformula/updateformulaitem",
                          keyspace=KEYSPACE,
                          method="POST",
                          params={"ticker":ticker})

class UpdateFormulaItemHandler(tornado.web.RequestHandler):
    
    def post(self):
        ticker = self.get_argument("ticker")
        stock = StockModel.get(ticker=ticker)
        balance = json.loads(stock.balance, encoding="utf-8")
        profit = json.loads(stock.profit, encoding="utf-8")
        year = datetime.date.today().year
        item = {}
        for i in range(3):
            earnings_date = self.__get_recent_earnings_date(year - i, balance, profit)
            if earnings_date is not None:
                break
        if earnings_date is None:
            logging.warn('There is no earnings date for %s' % (ticker))
            return
        try:
            bank_flag = False
            this_earnings_date = earnings_date.strftime('%Y%m%d')
            tangible_asset = self.__get_tangible_asset(balance[this_earnings_date])
            enterprise_value = self.__get_enterprise_value(balance[this_earnings_date], stock.market_capital)
            #total_assets = self.__get_total_assets(balance[this_earnings_date])
            #total_liability = self.__get_total_liability(balance[this_earnings_date])
            #current_assets = self.__get_current_assets(balance[this_earnings_date])
            #ownership_interest = self.__get_ownership_interest(balance[this_earnings_date])
            if earnings_date.month == 12:
                ebit = self.__get_ebit(profit[this_earnings_date])
                income = self.__get_income(profit[this_earnings_date])
                #net_profit = self.__get_net_profit(profit[this_earnings_date])
            else:
                last_earnings_date = earnings_date.replace(earnings_date.year - 1).strftime('%Y%m%d')
                last_year_date = datetime.date(year=earnings_date.year - 1, month=12, day=31).strftime('%Y%m%d')
                ebit = (self.__get_ebit(profit[this_earnings_date]) 
                        + self.__get_ebit(profit[last_year_date]) 
                        - self.__get_ebit(profit[last_earnings_date]))
                income = (self.__get_income(profit[this_earnings_date]) 
                          + self.__get_income(profit[last_year_date]) 
                          - self.__get_income(profit[last_earnings_date]))
                #net_profit = (self.__get_net_profit(profit[this_earnings_date]) 
                #              + self.__get_net_profit(profit[last_year_date]) 
                #              - self.__get_net_profit(profit[last_earnings_date]))
        except KeyError as ke:
            logging.exception(ke)
            bank_flag = True
            this_earnings_date = earnings_date.strftime('%Y%m%d')
            #total_assets = string.atof(balance[this_earnings_date]['资产总计'])
            #total_liability = string.atof(balance[this_earnings_date]['负债合计'])
            #ownership_interest = string.atof(balance[this_earnings_date]['归属于母公司股东的权益'])
            if earnings_date.month == 12:
                pass
                #net_profit = string.atof(profit[this_earnings_date]['归属于母公司的净利润'])
            else:
                last_earnings_date = earnings_date.replace(earnings_date.year - 1).strftime('%Y%m%d')
                last_year_date = datetime.date(year=earnings_date.year - 1, month=12, day=31).strftime('%Y%m%d')
                #net_profit = (string.atof(profit[this_earnings_date]['归属于母公司的净利润'])
                #              + string.atof(profit[last_year_date]['归属于母公司的净利润'])
                #              - string.atof(profit[last_earnings_date]['归属于母公司的净利润']))
            logging.warn("Firstly %s is a bank" % (ticker))
        item["bankFlag"] = bank_flag
        item["earningsDate"] = earnings_date.strftime('%Y%m%d')
        if not bank_flag:
            item["tangibleAsset"] = tangible_asset
            item["income"] = income
            item["enterpriseValue"] = enterprise_value
            item["ebit"] = ebit
        StockModel.create(ticker=ticker, formula_item=json.dumps(item))
        
    def __get_tangible_asset(self, balance):
        current_asset = string.atof(balance[u'流动资产合计'])
        current_liabilities = string.atof(balance[u'流动负债合计'])
        short_term_loans = string.atof(balance[u'短期借款'])
        notes_payable = string.atof(balance[u'应付票据'])
        a_maturity_of_non_current_liabilities = string.atof(balance[u'一年内到期的非流动负债'])
        cope_with_short_term_bond = string.atof(balance[u'应付短期债券'])
        fixed_assets_net_value = string.atof(balance[u'固定资产净值'])
        investment_real_estate = string.atof(balance[u'投资性房地产'])
        monetary_fund = string.atof(balance[u'货币资金'])
        transactional_financial_assets = string.atof(balance[u'交易性金融资产'])
        excess_cash = max(0, (monetary_fund + transactional_financial_assets) - max(0, current_liabilities - (current_asset - (monetary_fund + transactional_financial_assets))))
        tangible_asset = (current_asset - current_liabilities
                          + short_term_loans + notes_payable
                          + a_maturity_of_non_current_liabilities
                          + cope_with_short_term_bond + fixed_assets_net_value
                          + investment_real_estate - excess_cash)
        return tangible_asset
    
    def __get_enterprise_value(self, balance, market_capital):
        current_asset = string.atof(balance[u'流动资产合计'])
        current_liabilities = string.atof(balance[u'流动负债合计'])
        short_term_loans = string.atof(balance[u'短期借款'])
        notes_payable = string.atof(balance[u'应付票据'])
        a_maturity_of_non_current_liabilities = string.atof(balance[u'一年内到期的非流动负债'])
        cope_with_short_term_bond = string.atof(balance[u'应付短期债券'])
        monetary_fund = string.atof(balance[u'货币资金'])
        transactional_financial_assets = string.atof(balance[u'交易性金融资产'])
        long_term_loans = string.atof(balance[u'长期借款'])
        bonds_payable = string.atof(balance[u'应付债券'])
        minority_equity = string.atof(balance[u'少数股东权益'])
        available_for_sale_financial_assets = string.atof(balance[u'可供出售金融资产'])
        hold_expires_investment = string.atof(balance[u'持有至到期投资'])
        delay_income_tax_liabilities = string.atof(balance[u'递延所得税负债'])
        excess_cash = max(0, (monetary_fund + transactional_financial_assets) - max(0, current_liabilities - (current_asset - (monetary_fund + transactional_financial_assets))))
        enterprise_value = (short_term_loans + notes_payable + a_maturity_of_non_current_liabilities
                            + cope_with_short_term_bond + long_term_loans
                            + bonds_payable + minority_equity
                            - available_for_sale_financial_assets - hold_expires_investment
                            + delay_income_tax_liabilities - excess_cash) + market_capital
        return enterprise_value
        
    def __get_ebit(self, profit):
        income_from_main = string.atof(profit[u'营业收入'])
        cost_of_main_operation = string.atof(profit[u'营业成本'])
        tax_and_additional_expense = string.atof(profit[u'营业税金及附加'])
        general_and_administrative_expense = string.atof(profit[u'管理费用'])
        sales_expenses = string.atof(profit[u'销售费用'])
        investment_income = string.atof(profit[u'其中:对联营企业和合营企业的投资收益'])
        ebit = (income_from_main - cost_of_main_operation - tax_and_additional_expense - general_and_administrative_expense - sales_expenses + investment_income)
        return ebit
    
    def __get_income(self, profit):
        income_from_main = string.atof(profit[u'营业收入'])
        cost_of_main_operation = string.atof(profit[u'营业成本'])
        tax_and_additional_expense = string.atof(profit[u'营业税金及附加'])
        general_and_administrative_expense = string.atof(profit[u'管理费用'])
        sales_expenses = string.atof(profit[u'销售费用'])
        income = (income_from_main - cost_of_main_operation - tax_and_additional_expense - general_and_administrative_expense - sales_expenses)
        return income
        
    def __get_recent_earnings_date(self, year, balance, profit):
        q4 = datetime.date(year=year, month=12, day=31)
        #q3 = datetime.date(year=year, month=9, day=30)
        q2 = datetime.date(year=year, month=6, day=30)
        #q1 = datetime.date(year=year, month=3, day=31)
        last_year = year - 1
        if q4.strftime('%Y%m%d') in balance and q4.strftime('%Y%m%d') in profit:
            return q4
        elif q4.replace(year=last_year).strftime('%Y%m%d') in balance and q4.replace(year=last_year).strftime('%Y%m%d') in profit:
            #if q3.strftime('%Y%m%d') in balance and q3.strftime('%Y%m%d') in profit and q3.replace(year=last_year).strftime('%Y%m%d') in balance and q3.replace(year=last_year).strftime('%Y%m%d') in profit:
            #    return q3
            if q2.strftime('%Y%m%d') in balance and q2.strftime('%Y%m%d') in profit and q2.replace(year=last_year).strftime('%Y%m%d') in balance and q2.replace(year=last_year).strftime('%Y%m%d') in profit:
                return q2
            #elif q1.strftime('%Y%m%d') in balance and q1.strftime('%Y%m%d') in profit and q1.replace(year=last_year).strftime('%Y%m%d') in balance and q1.replace(year=last_year).strftime('%Y%m%d') in profit:
            #    return q1
            else:
                return None
        else:
            return None


class UpdateMagicFormulaResultHandler(tornado.web.RequestHandler):
    
    def __filter(self, stocks):
        results = []
        content = []
        miss = []
        for s in StockModel.all().limit(10):
            if s.market_capital == 0.0:
                content.append("The market capital is 0 for %s %s\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            sv = MagicFormulaStockView()
            try:
                sv.parse(s)
            except Exception as e:
                logging.exception(e)
                content.append("Parse stock (%s, %s) for %s %s\n" % (s.ticker, s.title, e, repr(s)))
                continue
            if sv.bank_flag:
                content.append("The stock (%s, %s) is a bank\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            results.append(sv)
        content.append("Total: %s, Sorted: %s Miss: %s" % (len(stocks), len(results), len(miss)))
        return results
    
    def __magicformula(self, stocks):
        results = sorted(stocks, cmp=lambda a, b : stock.cmp_rotc(a, b))
        for i in range(len(results)):
            if i != 0 and stock.cmp_rotc(results[i], results[i-1]) == 0:
                results[i].rotc_rank = results[i-1].rotc_rank
            else:
                results[i].rotc_rank = i + 1
        results = sorted(results, cmp=lambda a, b : stock.cmp_ey(a, b))
        for i in range(len(results)):
            if i != 0 and stock.cmp_ey(results[i], results[i-1]) == 0:
                results[i].ey_rank = results[i-1].ey_rank
            else:
                results[i].ey_rank = i + 1
        results = sorted(results, key=lambda stock : stock.rotc_rank + stock.ey_rank)
        for i in range(len(results)):
            if i != 0 and results[i].rotc_rank + results[i].ey_rank == results[i-1].rotc_rank + results[i-1].ey_rank:
                results[i].rank = results[i-1].rank
            else:
                results[i].rank = i + 1
        return results
    
    def __update_formula_result(self, data):
        results = {}
        results['error'] = 0
        results['description'] = 'No error'
        results['date'] = datetime.date.today().strftime("%Y%m%d")
        results['list'] = data
        FormulaResult.create(name="magicformula", result=json.dumps(results))
    
    def get(self):
        stocks = self.__filter(StockModel.all().limit(100))
        results = self.__magicformula(stocks)
        data = []
        for result in results:
            d = {}
            if result.tangible_asset != 0.0:
                d["rotc"] = "%d%%" % (result.income * 100 / result.tangible_asset)
            else:
                d["rotc"] = "∞"
            if result.enterprise_value != 0.0:
                d["ey"] = "%d%%" % (result.ebit * 100 / result.enterprise_value)
            else:
                d["ey"] = "∞"
            d["earningsDate"] = result.earnings_date
            d["ticker"] = result.ticker
            d["title"] = result.title
            d["marketCapital"] = "%.2f亿" % (result.market_capital / 100000000)
            d["rank"] = result.rank
            data.append(d)
        self.__update_formula_result(data)
    
    
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
        