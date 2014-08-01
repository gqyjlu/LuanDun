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

from tornado import gen
from tornado import httpclient
import tornado.web

from luandun.api import taskqueue
from luandun.business.magicformula import constant
from luandun.business.magicformula import stock
from luandun.business.magicformula.stock import GrahamData
from luandun.business.magicformula.stock import Stock
from luandun.business.magicformula.stock import StockData
from luandun.business.magicformula.stock import StockEarnings
from luandun.business.magicformula.stock import StockMarketCapital
from luandun.business.magicformula.stock import StockTitle


class UpdateTitleHandler(tornado.web.RequestHandler):
    
    def post(self):
        ticker = self.get_argument("ticker")
        title = self.get_argument("title")
        Stock.create(ticker=ticker, title=title)
        StockTitle.create(ticker=ticker, title=title)
        taskqueue.add(url=constant.URL_PREFIX + "/magicformula/updatemarketcapital",
                      keyspace=constant.KEYSPACE, 
                      method="POST", 
                      params={"ticker":ticker})
            

class UpdateMarketCapitalHandler(tornado.web.RequestHandler):
    
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
        
    @gen.coroutine
    def post(self):
        ticker = self.get_argument("ticker")
        if ticker[0] == "6":
            query = "sh" + ticker
        else:
            query = "sz" + ticker
        client = httpclient.AsyncHTTPClient()
        response = yield client.fetch("http://qt.gtimg.cn/S?q=" + query)
        value = self.__get_market_capital(ticker, response.body)
        Stock.create(ticker=ticker, market_capital=value)
        StockMarketCapital.create(ticker=ticker, market_capital=value)
        if value > 0:
            taskqueue.add(url=constant.URL_PREFIX + "/magicformula/updateearnings",
                          keyspace=constant.KEYSPACE,
                          method="POST",
                          params={"ticker":ticker})
        
        
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
                taskqueue.add(url=constant.URL_PREFIX + "/magicformula/updatetitle", 
                              keyspace=constant.KEYSPACE,
                              method="POST", 
                              params={"ticker":ticker, "title":title})
        

class BlankEarnings(Exception):
    
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)


class UpdateStockInfoHandler(tornado.web.RequestHandler):
    
    def post(self):
        taskqueue.add(url=constant.URL_PREFIX + '/magicformula/updatestocklist',
                      keyspace=constant.KEYSPACE,
                      method='POST')
        
        
class UpdateStockListHandler(tornado.web.RequestHandler):
    
    @gen.coroutine
    def post(self):
        client = httpclient.AsyncHTTPClient()
        response = yield client.fetch("http://quote.eastmoney.com/stocklist.html")
        data = response.body.decode("GBK").encode("UTF-8")
        parser = EastMoneyHTMLParser()
        parser.feed(data)
        parser.close()
        

class UpdateEarningsHandler(tornado.web.RequestHandler):
    
    def __get_page_content(self, body):
        data = body
        mp = {}
        lines = data.decode('GBK').encode('UTF-8').split('\n')
        for line in lines:
            fields = line.split('\t')
            for i in range(len(fields) - 2):
                if i + 1 not in mp:
                    mp[i + 1] = {}
                mp[i + 1][fields[0]] = fields[i + 1]
        results = {}
        for k in mp:
            if '报表日期' in mp[k]:
                results[mp[k]['报表日期']] = mp[k]
            elif '报告期' in mp[k]:
                results[mp[k]['报告期']] = mp[k]
        if not results:
            raise BlankEarnings('Content is %s' % (body))
        return results
    
    def __get_ebit(self, profit):
        income_from_main = string.atof(profit['营业收入'])
        cost_of_main_operation = string.atof(profit['营业成本'])
        tax_and_additional_expense = string.atof(profit['营业税金及附加'])
        general_and_administrative_expense = string.atof(profit['管理费用'])
        sales_expenses = string.atof(profit['销售费用'])
        investment_income = string.atof(profit['其中:对联营企业和合营企业的投资收益'])
        ebit = (income_from_main - cost_of_main_operation - tax_and_additional_expense - general_and_administrative_expense - sales_expenses + investment_income)
        return ebit
    
    def __get_income(self, profit):
        income_from_main = string.atof(profit['营业收入'])
        cost_of_main_operation = string.atof(profit['营业成本'])
        tax_and_additional_expense = string.atof(profit['营业税金及附加'])
        general_and_administrative_expense = string.atof(profit['管理费用'])
        sales_expenses = string.atof(profit['销售费用'])
        income = (income_from_main - cost_of_main_operation - tax_and_additional_expense - general_and_administrative_expense - sales_expenses)
        return income
    
    def __get_enterprise_value(self, balance):
        current_asset = string.atof(balance['流动资产合计'])
        current_liabilities = string.atof(balance['流动负债合计'])
        short_term_loans = string.atof(balance['短期借款'])
        notes_payable = string.atof(balance['应付票据'])
        a_maturity_of_non_current_liabilities = string.atof(balance['一年内到期的非流动负债'])
        cope_with_short_term_bond = string.atof(balance['应付短期债券'])
        monetary_fund = string.atof(balance['货币资金'])
        transactional_financial_assets = string.atof(balance['交易性金融资产'])
        long_term_loans = string.atof(balance['长期借款'])
        bonds_payable = string.atof(balance['应付债券'])
        minority_equity = string.atof(balance['少数股东权益'])
        available_for_sale_financial_assets = string.atof(balance['可供出售金融资产'])
        hold_expires_investment = string.atof(balance['持有至到期投资'])
        delay_income_tax_liabilities = string.atof(balance['递延所得税负债'])
        excess_cash = max(0, (monetary_fund + transactional_financial_assets) - max(0, current_liabilities - (current_asset - (monetary_fund + transactional_financial_assets))))
        enterprise_value = (short_term_loans + notes_payable + a_maturity_of_non_current_liabilities
                            + cope_with_short_term_bond + long_term_loans
                            + bonds_payable + minority_equity
                            - available_for_sale_financial_assets - hold_expires_investment
                            + delay_income_tax_liabilities - excess_cash)
        return enterprise_value
    
    def __get_tangible_asset(self, balance):
        current_asset = string.atof(balance['流动资产合计'])
        current_liabilities = string.atof(balance['流动负债合计'])
        short_term_loans = string.atof(balance['短期借款'])
        notes_payable = string.atof(balance['应付票据'])
        a_maturity_of_non_current_liabilities = string.atof(balance['一年内到期的非流动负债'])
        cope_with_short_term_bond = string.atof(balance['应付短期债券'])
        fixed_assets_net_value = string.atof(balance['固定资产净值'])
        investment_real_estate = string.atof(balance['投资性房地产'])
        monetary_fund = string.atof(balance['货币资金'])
        transactional_financial_assets = string.atof(balance['交易性金融资产'])
        excess_cash = max(0, (monetary_fund + transactional_financial_assets) - max(0, current_liabilities - (current_asset - (monetary_fund + transactional_financial_assets))))
        tangible_asset = (current_asset - current_liabilities
                          + short_term_loans + notes_payable
                          + a_maturity_of_non_current_liabilities
                          + cope_with_short_term_bond + fixed_assets_net_value
                          + investment_real_estate - excess_cash)
        return tangible_asset
    
    def __get_net_profit(self, profit):
        net_profit = string.atof(profit['归属于母公司所有者的净利润'])
        return net_profit
    
    def __get_ownership_interest(self, balance):
        total_owner_s_equity = string.atof(balance['归属于母公司股东权益合计'])
        return total_owner_s_equity
    
    def __get_total_assets(self, balance):
        total_assets = string.atof(balance['资产总计'])
        return total_assets
    
    def __get_total_liability(self, balance):
        total_liability = string.atof(balance['负债合计'])
        return total_liability
    
    def __get_current_assets(self, balance):
        current_assets = string.atof(balance['流动资产合计'])
        return current_assets
        
    def __update_earnings(self, ticker, balance, profit):
        entry = stock.get(ticker)
        year = datetime.date.today().year
        for i in range(3):
            earnings_date = self.__get_recent_earnings_date(year - i, balance, profit)
            if earnings_date is not None:
                break
        if earnings_date is None:
            logging.warn('There is no earnings date for %s' % (ticker))
            return
        else:
            try:
                bank_flag = False
                if earnings_date.month == 12:
                    this_earnings_date = earnings_date.strftime('%Y%m%d')
                    ebit = self.__get_ebit(profit[this_earnings_date])
                    income = self.__get_income(profit[this_earnings_date])
                    enterprise_value = self.__get_enterprise_value(balance[this_earnings_date])
                    tangible_asset = self.__get_tangible_asset(balance[this_earnings_date])
                    ownership_interest = self.__get_ownership_interest(balance[this_earnings_date])
                    net_profit = self.__get_net_profit(profit[this_earnings_date])
                    total_assets = self.__get_total_assets(balance[this_earnings_date])
                    total_liability = self.__get_total_liability(balance[this_earnings_date])
                    current_assets = self.__get_current_assets(balance[this_earnings_date])
                else:
                    this_earnings_date = earnings_date.strftime('%Y%m%d')
                    last_earnings_date = earnings_date.replace(earnings_date.year - 1).strftime('%Y%m%d')
                    last_year_date = datetime.date(year=earnings_date.year - 1, month=12, day=31).strftime('%Y%m%d')
                    enterprise_value = self.__get_enterprise_value(balance[this_earnings_date])
                    tangible_asset = self.__get_tangible_asset(balance[this_earnings_date])
                    ownership_interest = self.__get_ownership_interest(balance[this_earnings_date])
                    total_assets = self.__get_total_assets(balance[this_earnings_date])
                    total_liability = self.__get_total_liability(balance[this_earnings_date])
                    current_assets = self.__get_current_assets(balance[this_earnings_date])
                    ebit = (self.__get_ebit(profit[this_earnings_date]) 
                            + self.__get_ebit(profit[last_year_date]) 
                            - self.__get_ebit(profit[last_earnings_date]))
                    income = (self.__get_income(profit[this_earnings_date]) 
                              + self.__get_income(profit[last_year_date]) 
                              - self.__get_income(profit[last_earnings_date]))
                    net_profit = (self.__get_net_profit(profit[this_earnings_date]) 
                                  + self.__get_net_profit(profit[last_year_date]) 
                                  - self.__get_net_profit(profit[last_earnings_date]))
            except KeyError as ke:
                logging.exception(ke)
                bank_flag = True
                if earnings_date.month == 12:
                    this_earnings_date = earnings_date.strftime('%Y%m%d')
                    ownership_interest = string.atof(balance[this_earnings_date]['归属于母公司股东的权益'])
                    net_profit = string.atof(profit[this_earnings_date]['归属于母公司的净利润'])
                    total_assets = string.atof(balance[this_earnings_date]['资产总计'])
                    total_liability = string.atof(balance[this_earnings_date]['负债合计'])
                else:
                    this_earnings_date = earnings_date.strftime('%Y%m%d')
                    last_earnings_date = earnings_date.replace(earnings_date.year - 1).strftime('%Y%m%d')
                    last_year_date = datetime.date(year=earnings_date.year - 1, month=12, day=31).strftime('%Y%m%d')
                    ownership_interest = string.atof(balance[this_earnings_date]['归属于母公司股东的权益'])
                    total_assets = string.atof(balance[this_earnings_date]['资产总计'])
                    total_liability = string.atof(balance[this_earnings_date]['负债合计'])
                    net_profit = (string.atof(profit[this_earnings_date]['归属于母公司的净利润'])
                                  + string.atof(profit[last_year_date]['归属于母公司的净利润'])
                                  - string.atof(profit[last_earnings_date]['归属于母公司的净利润']))
                entry.bank_flag = bank_flag
                entry.earnings_date = earnings_date
                entry.ownership_interest = ownership_interest
                entry.net_profit = net_profit
                entry.total_assets = total_assets
                entry.total_liability = total_liability
                stock.put(ticker, entry)
                logging.info("Firstly %s is a bank" % (ticker))
                return
            entry.bank_flag = bank_flag
            entry.earnings_date = earnings_date
            entry.ebit = ebit
            entry.income = income
            entry.enterprise_value = enterprise_value
            entry.tangible_asset = tangible_asset
            entry.ownership_interest = ownership_interest
            entry.net_profit = net_profit
            entry.total_assets = total_assets
            entry.total_liability = total_liability
            entry.current_assets = current_assets
            stock.put(ticker, entry)
        
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
        
    @gen.coroutine
    def post(self):
        ticker = self.get_argument('ticker')
        
        client = httpclient.AsyncHTTPClient()
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_BalanceSheet/displaytype/4/stockid/%s/ctrl/all.phtml" % (ticker)
        response = yield client.fetch(url)
        balance_body = response.body
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_ProfitStatement/displaytype/4/stockid/%s/ctrl/all.phtml" % (ticker)
        response = yield client.fetch(url)
        profit_body = response.body
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_CashFlow/displaytype/4/stockid/%s/ctrl/all.phtml" % (ticker)
        response = yield client.fetch(url)
        cash_body = response.body
        
        if cash_body.find("报告期".encode("GBK")) < 0:
            bank_flag = True
        else:
            bank_flag = False
        balance = self.__get_page_content(balance_body)
        profit = self.__get_page_content(profit_body)
        cash = self.__get_page_content(cash_body)
        StockEarnings.create(ticker=ticker, bank_flag=bank_flag, balance=json.dumps(balance), profit=json.dumps(profit), cash=json.dumps(cash))
        
        taskqueue.add(url=constant.URL_PREFIX + "/magicformula/updatedata",
                      keyspace=constant.KEYSPACE, 
                      method="POST", 
                      params={"ticker":ticker})
        
        self.__update_earnings(ticker, balance, profit)
        
        
class UpdateAllDataHandler(tornado.web.RequestHandler):
    
    def get(self):
        for i in StockData.all():
            taskqueue.add(url=constant.URL_PREFIX + "/magicformula/updatedata",
                          keyspace=constant.KEYSPACE, 
                          method="POST", 
                          params={"ticker":str(i.ticker)})
        

class UpdateDataHandler(tornado.web.RequestHandler):
    
    def __get_annual_oer(self, balance, bank_flag):
        if not bank_flag:
            total_owner_s_equity = string.atof(balance[u'归属于母公司股东权益合计'])
            total_assets = string.atof(balance[u'资产总计'])
        else:
            total_owner_s_equity = string.atof(balance[u'归属于母公司股东的权益'])
            total_assets = string.atof(balance[u'资产总计'])
        if total_assets == 0:
            return "∞"
        else:
            return "%.1f%%" % (total_owner_s_equity * 100 / total_assets)
    
    def __get_annual_roe(self, balance, profit, bank_flag):
        if not bank_flag:
            net_profit = string.atof(profit[u'归属于母公司所有者的净利润'])
            total_owner_s_equity = string.atof(balance[u'归属于母公司股东权益合计'])
        else:
            net_profit = string.atof(profit[u'归属于母公司的净利润'])
            total_owner_s_equity = string.atof(balance[u'归属于母公司股东的权益'])
        if total_owner_s_equity == 0:
            return "∞"
        else:
            return "%.1f%%" % (net_profit * 100 / total_owner_s_equity)
        
    def __get_annual_fcf(self, profit, cash):
        if string.atof(profit[u"利润总额"]) == 0:
            return "∞"
        capital_expenditure = string.atof(cash[u"购建固定资产、无形资产和其他长期资产所支付的现金"])
        depreciation_and_amortization = string.atof(cash[u"资产减值准备"]) + string.atof(cash[u"固定资产折旧、油气资产折耗、生产性物资折旧"]) + string.atof(cash[u"无形资产摊销"]) + string.atof(cash[u"长期待摊费用摊销"]) + string.atof(cash[u"固定资产报废损失"])
        working_capital_to_reduce = string.atof(cash[u"存货的减少"]) + string.atof(cash[u"经营性应收项目的减少"]) + string.atof(cash[u"待摊费用的减少"]) + string.atof(cash[u"经营性应付项目的增加"]) + string.atof(cash[u"预提费用的增加"])
        noplat = (string.atof(profit[u"三、营业利润"]) + string.atof(profit[u"营业外收入"]) - string.atof(profit[u"营业外支出"]) - string.atof(profit[u"所得税费用"]) + string.atof(profit[u"财务费用"])) * (1 - string.atof(profit[u"所得税费用"]) / string.atof(profit[u"利润总额"]))
        return "%.2f亿" % ((noplat + depreciation_and_amortization + working_capital_to_reduce - capital_expenditure) / 100000000)
        
    def __get_annual_npm(self, profit):
        income_from_main = string.atof(profit[u'营业收入'])
        net_profit = string.atof(profit[u'归属于母公司所有者的净利润'])
        
        if income_from_main == 0:
            return "∞"
        else:
            return "%.1f%%" % (net_profit * 100 / income_from_main)
        
    def __get_annual_gpm(self, profit):
        income_from_main = string.atof(profit[u'营业收入'])
        cost_of_main_operation = string.atof(profit[u'营业成本'])
        
        if income_from_main == 0:
            return "∞"
        else:
            return "%.1f%%" % ((income_from_main - cost_of_main_operation) * 100 / income_from_main)
        
    def __get_annual_3fee(self, profit):
        income_from_main = string.atof(profit[u'营业收入'])
        general_and_administrative_expense = string.atof(profit[u'管理费用'])
        sales_expenses = string.atof(profit[u'销售费用'])
        financial_expense = string.atof(profit[u"财务费用"])
        
        if income_from_main == 0:
            return "∞"
        else:
            return "%.2f%%" % ((general_and_administrative_expense + sales_expenses + financial_expense) * 100 / income_from_main)
        
    def __get_annual_qr(self, balance):
        current_asset = string.atof(balance[u'流动资产合计'])
        inventory = string.atof(balance[u"存货"])
        current_liabilities = string.atof(balance[u'流动负债合计'])
        if current_liabilities == 0:
            return "∞"
        else:
            return "%.2f" % ((current_asset - inventory) / current_liabilities)
        
    def __get_annual_cr(self, balance):
        current_asset = string.atof(balance[u'流动资产合计'])
        current_liabilities = string.atof(balance[u'流动负债合计'])
        if current_liabilities == 0:
            return "∞"
        else:
            return "%.2f" % (current_asset / current_liabilities)
    
    def __get_annual_rotc(self, balance, profit):
        
        income_from_main = string.atof(profit[u'营业收入'])
        cost_of_main_operation = string.atof(profit[u'营业成本'])
        tax_and_additional_expense = string.atof(profit[u'营业税金及附加'])
        general_and_administrative_expense = string.atof(profit[u'管理费用'])
        sales_expenses = string.atof(profit[u'销售费用'])
        income = (income_from_main - cost_of_main_operation - tax_and_additional_expense - general_and_administrative_expense - sales_expenses)

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
        
        if tangible_asset == 0:
            return "∞"
        else:
            return "%d%%" % (income * 100 / tangible_asset)
    
    def __get_annual_rotc_list(self, earnings):
        result = []
        last_year = datetime.date.today().year - 1
        balance = json.loads(earnings.balance)
        profit = json.loads(earnings.profit)
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance and k in profit and not earnings.bank_flag:
                item.append(self.__get_annual_rotc(balance[k], profit[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_fcf_list(self, earnings):
        result = []
        last_year = datetime.date.today().year - 1
        profit = json.loads(earnings.profit)
        cash = json.loads(earnings.cash)
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in profit and not earnings.bank_flag:
                try:
                    item.append(self.__get_annual_fcf(profit[k], cash[k]))
                except KeyError as ke:
                    logging.exception(ke)
                    item.append("-")
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_npm_list(self, earnings):
        result = []
        last_year = datetime.date.today().year - 1
        profit = json.loads(earnings.profit)
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in profit and not earnings.bank_flag:
                item.append(self.__get_annual_npm(profit[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_gpm_list(self, earnings):
        result = []
        last_year = datetime.date.today().year - 1
        profit = json.loads(earnings.profit)
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in profit and not earnings.bank_flag:
                item.append(self.__get_annual_gpm(profit[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_oer_list(self, earnings):
        result = []
        last_year = datetime.date.today().year - 1
        balance = json.loads(earnings.balance)
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance:
                item.append(self.__get_annual_oer(balance[k], earnings.bank_flag))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_3fee_list(self, earnings):
        result = []
        last_year = datetime.date.today().year - 1
        profit = json.loads(earnings.profit)
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in profit and not earnings.bank_flag:
                item.append(self.__get_annual_3fee(profit[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_qr_list(self, earnings):
        result = []
        last_year = datetime.date.today().year - 1
        balance = json.loads(earnings.balance)
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance and not earnings.bank_flag:
                item.append(self.__get_annual_qr(balance[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_cr_list(self, earnings):
        result = []
        last_year = datetime.date.today().year - 1
        balance = json.loads(earnings.balance)
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance and not earnings.bank_flag:
                item.append(self.__get_annual_cr(balance[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_roe_list(self, earnings):
        result = []
        last_year = datetime.date.today().year - 1
        balance = json.loads(earnings.balance)
        profit = json.loads(earnings.profit)
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance and k in profit:
                item.append(self.__get_annual_roe(balance[k], profit[k], earnings.bank_flag))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_recent_earnings_date_by_year(self, year, earnings):
        balance = earnings.balance
        profit = earnings.profit
        cash = earnings.cash
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
        
    def __get_recent_earnings_date(self, earnings):
        year = datetime.date.today().year
        earnings_date = None
        for i in range(3):
            earnings_date = self.__get_recent_earnings_date_by_year(year - i, earnings)
            if earnings_date is not None:
                break
        return earnings_date
        
    def __get_recent_owner_s_equity_ratio(self, earnings_date, earnings):
        
        if earnings_date is None:
            return "-"
        
        balance = json.loads(earnings.balance)
        if not earnings.bank_flag:
            total_owner_s_equity = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'归属于母公司股东权益合计'])
            total_assets = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'资产总计'])
        else:
            total_owner_s_equity = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'归属于母公司股东的权益'])
            total_assets = string.atof(balance[earnings_date.strftime('%Y%m%d')][u'资产总计'])
        
        if total_assets == 0:
            return "∞"
        else:
            return total_owner_s_equity / total_assets
        
    def __get_recent_pe(self, ticker, earnings_date, earnings):

        if earnings_date is None:
            return "-"
        
        if earnings.bank_flag:
            key = u"归属于母公司的净利润"
        else:
            key = u'归属于母公司所有者的净利润'
        profit = json.loads(earnings.profit)
        if earnings_date.month == 12:
            net_profit = string.atof(profit[earnings_date.strftime('%Y%m%d')][key])
        else:
            last_year_date = datetime.date(year=earnings_date.year - 1, month=12, day=31).strftime('%Y%m%d')
            last_earnings_date = earnings_date.replace(earnings_date.year - 1).strftime('%Y%m%d')
            net_profit = string.atof(profit[earnings_date.strftime('%Y%m%d')][key]) + string.atof(profit[last_year_date][key]) - string.atof(profit[last_earnings_date][key])
        
        if net_profit == 0:
            return "∞"
        else:
            return StockMarketCapital.get(ticker=ticker).market_capital / net_profit
        
    def __update_graham_data(self, ticker, earnings):
        data = {}
        earnings_date = self.__get_recent_earnings_date(earnings)
        data["recentEarningsDate"] = earnings_date.strftime("%Y%m%d")
        data["recentPE"] = self.__get_recent_pe(ticker, earnings_date, earnings)
        data["recentOwnersEquityRatio"] = self.__get_recent_owner_s_equity_ratio(earnings_date, earnings)
        GrahamData.create(ticker=ticker, data=json.dumps(data))
        
    def __update_stock_data(self, ticker, earnings):
        view = {}
        model = {}
        view["annualRotc"] = self.__get_annual_rotc_list(earnings)
        view["annualRoe"] = self.__get_annual_roe_list(earnings)
        view["annualCR"] = self.__get_annual_cr_list(earnings)
        view["annualQR"] = self.__get_annual_qr_list(earnings)
        view["annual3Fee"] = self.__get_annual_3fee_list(earnings)
        view["annualOER"] = self.__get_annual_oer_list(earnings)
        view["annualGPM"] = self.__get_annual_gpm_list(earnings)
        view["annualNPM"] = self.__get_annual_npm_list(earnings)
        view["annualFCF"] = self.__get_annual_fcf_list(earnings)
        StockData.create(ticker=ticker, view=json.dumps(view), model=json.dumps(model))
    
    def post(self):
        ticker = self.get_argument('ticker')
        earnings = StockEarnings.get(ticker=ticker)
        self.__update_graham_data(ticker, earnings)
        self.__update_stock_data(ticker, earnings)
        