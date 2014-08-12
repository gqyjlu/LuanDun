# -*- coding: utf-8 -*-


'''
Created on 2014年8月11日

@author: prstcsnpr
'''


import datetime
import logging
import string

class StockViewVersion0(object):
    
    def __init__(self, response):
        self.__ticker = response["ticker"]
        self.__bank_flag = response["bank_flag"]
        self.__balance = response["balance"]
        self.__profit = response["profit"]
        self.__cash = response["cash"]
        self.__market_capital = response["market_capital"]
        
    def data(self):
        data = {}
        data["annualRotc"] = self.__get_annual_rotc_list()
        data["annualRoe"] = self.__get_annual_roe_list()
        data["annualCR"] = self.__get_annual_cr_list()
        data["annualQR"] = self.__get_annual_qr_list()
        data["annual3Fee"] = self.__get_annual_3fee_list()
        data["annualOER"] = self.__get_annual_oer_list()
        data["annualGPM"] = self.__get_annual_gpm_list()
        data["annualNPM"] = self.__get_annual_npm_list()
        data["annualFCF"] = self.__get_annual_fcf_list()
        return data
    
    def __get_annual_rotc_list(self):
        result = []
        last_year = datetime.date.today().year - 1
        balance = self.__balance
        profit = self.__profit
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance and k in profit and not self.__bank_flag:
                item.append(self.__get_annual_rotc(balance[k], profit[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
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
        
    def __get_annual_fcf_list(self):
        result = []
        last_year = datetime.date.today().year - 1
        profit = self.__profit
        cash = self.__cash
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in profit and not self.__bank_flag:
                try:
                    item.append(self.__get_annual_fcf(profit[k], cash[k]))
                except KeyError as ke:
                    logging.exception(ke)
                    item.append("-")
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_npm_list(self):
        result = []
        last_year = datetime.date.today().year - 1
        profit = self.__profit
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in profit and not self.__bank_flag:
                item.append(self.__get_annual_npm(profit[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_gpm_list(self):
        result = []
        last_year = datetime.date.today().year - 1
        profit = self.__profit
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in profit and not self.__bank_flag:
                item.append(self.__get_annual_gpm(profit[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_oer_list(self):
        result = []
        last_year = datetime.date.today().year - 1
        balance = self.__balance
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance:
                item.append(self.__get_annual_oer(balance[k], self.__bank_flag))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_3fee_list(self):
        result = []
        last_year = datetime.date.today().year - 1
        profit = self.__profit
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in profit and not self.__bank_flag:
                item.append(self.__get_annual_3fee(profit[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_qr_list(self):
        result = []
        last_year = datetime.date.today().year - 1
        balance = self.__balance
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance and not self.__bank_flag:
                item.append(self.__get_annual_qr(balance[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_cr_list(self):
        result = []
        last_year = datetime.date.today().year - 1
        balance = self.__balance
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance and not self.__bank_flag:
                item.append(self.__get_annual_cr(balance[k]))
            else:
                item.append("-")
            result.append(item)
        return result
    
    def __get_annual_roe_list(self):
        result = []
        last_year = datetime.date.today().year - 1
        balance = self.__balance
        profit = self.__profit
        for i in range(7):
            year = last_year - i
            k = datetime.date(year=year, month=12, day=31).strftime('%Y%m%d')
            item = []
            item.append(year)
            if k in balance and k in profit:
                item.append(self.__get_annual_roe(balance[k], profit[k], self.__bank_flag))
            else:
                item.append("-")
            result.append(item)
        return result
    
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
        
