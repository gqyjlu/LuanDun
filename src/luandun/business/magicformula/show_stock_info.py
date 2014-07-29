# -*- coding: utf-8 -*-


import datetime
import logging
import json

import tornado.web

from luandun.business.magicformula import gdp
from luandun.business.magicformula import stock
from luandun.business.magicformula.stock import StockData
from luandun.business.magicformula.stock import StockTitle
from luandun.business.magicformula import stock_result


class ShowStockDataHandler(tornado.web.RequestHandler):
    
    def get(self):
        ticker = self.get_argument("ticker")
        title = StockTitle.get(ticker=ticker).title
        data = json.loads(StockData.get(ticker=ticker).view)
        data["title"] = title
        self.write(self.__generate_json(data))
        
    
    def __generate_json(self, data):
        total_results = {}
        total_results['error'] = 0
        total_results['description'] = 'No error'
        total_results['date'] = datetime.date.today().strftime("%Y%m%d")
        total_results['data'] = data
        return json.dumps(total_results)

    
class ShowNetCurrentAssetApproachHandler(tornado.web.RequestHandler):
    def get(self):
        entry = stock_result.get_html('netcurrentassetapproach')
        self.write(entry.content)
    
    
class ShowGrahamFormulaHandler(tornado.web.RequestHandler):
    def get(self):
        entry = stock_result.get_html('grahamformula')
        self.write(entry.content)
        
        
class ShowMagicFormulaHandler(tornado.web.RequestHandler):
    def get(self):
        entry = stock_result.get_json('magicformula')
        self.set_header("Access-Control-Allow-Origin", "*")
        self.write(entry.content)
        
        
class UpdateNetCurrentAssetApproachHandler(tornado.web.RequestHandler):
    
    def post(self):
        values = {}
        stocks = stock.Stock.all()
        stocks, pb, pe, roe, mc_gdp = self.__filter(stocks)
        values['stocks'] = stocks[0 : len(stocks)]
        values['PB'] = "%.4f" % (pb)
        values['PE'] = "%.2f" % (pe)
        values['ROE'] = "%.1f%%" % (roe)
        values['MCGDP'] = "%.0f%%" % (mc_gdp)
        entry = stock_result.get_html('netcurrentassetapproach')
        stock_result.set_html('netcurrentassetapproach', entry)
        
    def __send_mail(self, content):
        receiver="magicformula@googlegroups.com"
        logging.info('Mail result for netcurrentassetapproach to %s' % (receiver))
        
    def __filter(self, stocks):
        content = []
        results = []
        miss = []
        p = 0.0
        b = 0.0
        net_profit = 0.0
        ownership_interest = 0.0
        gdp_value = gdp.get().value
        for s in stocks:
            if s.ticker[0] == '2' or s.ticker[0] == '9':
                logging.warn("%s %s is B Stock" % (s.ticker, s.title))
                continue
            if s.market_capital == 0.0:
                logging.warn("The market capital is 0 for %s %s" % (s.ticker, s.title))
                continue
            if s.earnings_date is None:
                logging.warn("There is no earnings for %s %s" % (s.ticker, s.title))
                continue
            if datetime.date.today().year - s.earnings_date.year > 2:
                logging.warn("The earnings is too old for %s %s %s" % (s.ticker, s.title, s.earnings_date.strftime("%Y%m%d")))
                continue
            p += s.market_capital
            b += s.ownership_interest
            net_profit += s.net_profit
            ownership_interest += s.ownership_interest
            if s.bank_flag == True:
                content.append("The stock (%s, %s) is a bank\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if s.market_capital_date != datetime.date.today():
                logging.warn("The stock (%s, %s) is not in Google List" % (s.ticker, s.title))
            sv = stock.NetCurrentAssetApproachStockView()
            try:
                sv.parse(s)
            except Exception as e:
                logging.warn("Parse stock (%s, %s) for %s" % (s.ticker, s.title, e))
                continue
            if sv.pe > 0 and sv.net_current_assets > sv.market_capital:
                sv.format()
                results.append(sv)
        return (results, p / b, p / net_profit, net_profit * 100/ownership_interest, p * 100 / gdp_value)

class UpdateGrahamFormulaHandler(tornado.web.RequestHandler):
    
    def __filter(self, stocks):
        results = []
        p = 0.0
        b = 0.0
        net_profit = 0.0
        ownership_interest = 0.0
        gdp_value = gdp.get().value
        for s in stocks:
            if s.ticker[0] == '2' or s.ticker[0] == '9':
                logging.warn("%s %s is B Stock" % (s.ticker, s.title))
                continue
            if s.market_capital == 0.0:
                logging.warn("The market capital is 0 for %s %s" % (s.ticker, s.title))
                continue
            if s.earnings_date is None:
                logging.warn("There is no earnings for %s %s" % (s.ticker, s.title))
                continue
            if datetime.date.today().year - s.earnings_date.year > 2:
                logging.warn("The earnings is too old for %s %s %s" % (s.ticker, s.title, s.earnings_date.strftime("%Y%m%d")))
                continue
            p += s.market_capital
            b += s.ownership_interest
            net_profit += s.net_profit
            ownership_interest += s.ownership_interest
            if s.market_capital_date != datetime.date.today():
                logging.warn("The stock (%s, %s) is not in Google List" % (s.ticker, s.title))
            sv = stock.GrahamFormulaStockView()
            try:
                sv.parse(s)
            except Exception as e:
                logging.warn("Parse stock (%s, %s) for %s" % (s.ticker, s.title, e))
                continue
            if sv.pe <= 10 and sv.pe > 0 and sv.debt_asset_ratio <= 50 and sv.debt_asset_ratio > 0:
                sv.format()
                results.append(sv)
        return (results, p / b, p / net_profit, net_profit * 100/ownership_interest, p * 100 / gdp_value)
    
    def __send_mail(self, content):
        #receiver="magicformula@googlegroups.com"
        receiver="prstcsnpr@gmail.com"
        logging.info('Mail result for grahamformula to %s' % (receiver))
            
    def post(self):
        values = {}
        stocks = stock.Stock.all()
        stocks, pb, pe, roe, mc_gdp = self.__filter(stocks)
        values['stocks'] = stocks[0 : len(stocks)]
        values['PB'] = "%.4f" % (pb)
        values['PE'] = "%.2f" % (pe)
        values['ROE'] = "%.1f%%" % (roe)
        values['MCGDP'] = "%.0f%%" % (mc_gdp)
        entry = stock_result.get_html('grahamformula')
        stock_result.set_html('grahamformula', entry)
        self.generate_json(values)
        
    def __generate_json(self, stocks):
        results = []
        for stock in stocks[0 : 50]:
            result = {}
            result['code'] = stock.ticker
            result['name'] = stock.title
            result['marketCap'] = stock.market_capital
            result['roe'] = stock.roe
            result['pb'] = stock.pb
            result['pe'] = stock.pe
            result['earningsDate'] = stock.earnings_date
            result['catetory'] = stock.subcategory
            result['debt_asset_ratio'] = stock.debt_asset_ratio
            results.append(result)
        total_results = {}
        total_results['error'] = 0
        total_results['description'] = 'No error'
        total_results['date'] = datetime.date.today().strftime("%Y%m%d")
        total_results['list'] = results
        json_result = json.dumps(total_results)
        entry = stock_result.get_json('grahamformula')
        entry.content = json_result
        stock_result.set_json('grahamformula', entry)

        
class UpdateMagicFormulaHandler(tornado.web.RequestHandler):
    
    def __filter(self, stocks):
        content = []
        results = []
        miss = []
        p = 0.0
        b = 0.0
        net_profit = 0.0
        ownership_interest = 0.0
        gdp_value = gdp.get().value
        for s in stocks:
            if s.ticker[0] == '2' or s.ticker[0] == '9':
                content.append("%s %s is B Stock\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if s.market_capital == 0.0:
                content.append("The market capital is 0 for %s %s\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if s.earnings_date is None:
                content.append("There is no earnings for %s %s\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if datetime.date.today().year - s.earnings_date.year > 2:
                content.append("The earnings is too old for %s %s %s\n" % (s.ticker, s.title, s.earnings_date.strftime("%Y%m%d")))
                miss.append(s.ticker)
                continue
            p += s.market_capital
            b += s.ownership_interest
            net_profit += s.net_profit
            ownership_interest += s.ownership_interest
            if s.bank_flag == True:
                content.append("The stock (%s, %s) is a bank\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if s.category == None:
                s.category = ""
            if s.subcategory == None:
                s.subcategory = ""
            if (s.category.find('D') > 0 or s.category.find('G') > 0 or s.category.find('N') > 0):
                content.append("The stock (%s, %s) is Public Utilities\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if s.category.find('J') > 0:
                content.append('The stock (%s, %s) is Finance\n' % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if s.market_capital_date != datetime.date.today():
                content.append("The stock (%s, %s) is not in Google List\n" % (s.ticker, s.title))
            sv = stock.MagicFormulaStockView()
            try:
                sv.parse(s)
            except Exception as e:
                content.append("Parse stock (%s, %s) for %s %s\n" % (s.ticker, s.title, e, repr(s)))
                continue
            results.append(sv)
        content.append("Total: %s, Sorted: %s Miss: %s" % (len(stocks), len(results), len(miss)))
        return (results, p / b, p / net_profit, net_profit * 100 / ownership_interest, p * 100 / gdp_value)
            
    
    def __magicformula(self, stocks, roic_rate = 1, ebit_ev_rate = 1):
        results = sorted(stocks, cmp=lambda a, b : stock.cmp_roic(a, b))
        for i in range(len(results)):
            if i != 0 and stock.cmp_roic(results[i], results[i-1]) == 0:
                results[i].roic_rank = results[i-1].roic_rank
            else:
                results[i].roic_rank = i + 1
        results = sorted(results, cmp=lambda a, b : stock.cmp_ebit_ev(a, b))
        for i in range(len(results)):
            if i != 0 and stock.cmp_ebit_ev(results[i], results[i-1]) == 0:
                results[i].ebit_ev_rank = results[i-1].ebit_ev_rank
            else:
                results[i].ebit_ev_rank = i + 1
        results = sorted(results, key=lambda stock : stock.roic_rank * roic_rate + stock.ebit_ev_rank * ebit_ev_rate)
        for i in range(len(results)):
            if i != 0 and results[i].roic_rank * roic_rate + results[i].ebit_ev_rank * ebit_ev_rate == results[i-1].roic_rank * roic_rate + results[i-1].ebit_ev_rank * ebit_ev_rate:
                results[i].rank = results[i-1].rank
            else:
                results[i].rank = i + 1
            results[i].format()
        return results
    
    def post(self):
        values = {}
        stocks = stock.Stock.all()
        stocks, pb, pe, roe, mc_gdp = self.__filter(stocks)
        stocks = self.__magicformula(stocks)
        position = 100
        while position<len(stocks):
            if stocks[position].rank == stocks[position - 1].rank:
                position = position + 1
            else:
                break
        values['stocks'] = stocks[0 : position]
        values['PB'] = "%.4f" % (pb)
        values['PE'] = "%.2f" % (pe)
        values['ROE'] = "%.1f%%" % (roe)
        values['MCGDP'] = "%.0f%%" % (mc_gdp)
        entry = stock_result.get_html('magicformula')
        stock_result.set_html('magicformula', entry)
        self.__generate_json(values['stocks'])
        
    def __generate_json(self, stocks):
        results = []
        for stock in stocks[0 : 30]:
            result = {}
            result['rank'] = stock.rank
            result['ticker'] = stock.ticker
            result['title'] = stock.title
            result['marketCapital'] = stock.market_capital
            result['rotc'] = stock.roic
            result['rotcRank'] = stock.roic_rank
            result['ey'] = stock.ebit_ev
            result['eyRank'] = stock.ebit_ev_rank
            result['roe'] = stock.roe
            result['pb'] = stock.pb
            result['pe'] = stock.pe
            result['earningsDate'] = stock.earnings_date
            result['catetory'] = stock.subcategory
            results.append(result)
        total_results = {}
        total_results['error'] = 0
        total_results['description'] = 'No error'
        total_results['date'] = datetime.date.today().strftime("%Y%m%d")
        total_results['list'] = results
        json_result = json.dumps(total_results)
        entry = stock_result.get_json('magicformula')
        entry.content = json_result
        stock_result.set_json('magicformula', entry)
