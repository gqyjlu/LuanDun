# -*- coding: utf-8 -*-


'''
Created on 2014年8月9日

@author: prstcsnpr
'''

from HTMLParser import HTMLParser
import re


class BlankStockFinancialStatement(Exception):
    pass


class EastMoneyHTMLParser(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)
        self.__flag = False
        self.__list = []
        
    def get_list(self):
        return self.__list
        
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
                s = []
                s.append(ticker)
                s.append(title)
                self.__list.append(s)
                
                
class JRJYearListHTMLParser(HTMLParser):
    
    def __init__(self, ticker):
        HTMLParser.__init__(self)
        self.__ticker = ticker
        self.__flag = False
        self.__list = []
        
    def type(self):
        pass
        
    def handle_starttag(self, tag, attrs):
        if "a" == tag:
            for attr in attrs:
                if "href" == attr[0] and attr[1].find("/share," + self.__ticker + "," + self.type() + "_") >= 0:
                    self.__flag = True
        
    def handle_endtag(self, tag):
        if "a" == tag and self.__flag:
            self.__flag = False
        
    def handle_data(self, data):
        if self.__flag:
            line = re.split(" ", data)
            self.__list.append(line[0])
            
    def list(self):
        return self.__list
    
    
class JRJBalanceYearListHTMLParser(JRJYearListHTMLParser):
    def type(self):
        return "zcfzb"
    
    
class JRJProfitYearListHTMLParser(JRJYearListHTMLParser):
    def type(self):
        return "lrfpb"
    
    
class JRJCashYearListHTMLParser(JRJYearListHTMLParser):
    def type(self):
        return "xjllb"
    
    
class JRJFinancialStatementHTMLParser(HTMLParser):
    
    def __init__(self, ticker, year):
        HTMLParser.__init__(self)
        self.__ticker = ticker
        self.__year = year
        self.__table_flag = False
        self.__td_flag = False
        self.__key_flag = False
        self.__key = None
        self.__map = {}
        
    def handle_starttag(self, tag, attrs):
        if "table" == tag:
            for attr in attrs:
                if "class" == attr[0] and attr[1] == "tab1":
                    self.__table_flag = True
        if self.__table_flag and "td" == tag:
            self.__td_flag = True
            for attr in attrs:
                if "class" == attr[0] and attr[1] == "txl":
                    self.__key_flag = True
            if not self.__key_flag:
                self.__map[self.__key].append("")
        
    def handle_endtag(self, tag):
        if self.__table_flag and "td" == tag:
            self.__td_flag = False
            if self.__key_flag:
                self.__key_flag = False
        if "table" == tag:
            if self.__table_flag:
                self.__table_flag = False
        
    def handle_data(self, data):
        if self.__table_flag and self.__td_flag:
            if self.__key_flag:
                self.__key = data.strip()
                self.__map[self.__key] = []
            else:
                self.__map[self.__key][len(self.__map[self.__key]) - 1] = data.strip()
                
    def result(self):
        results = {}
        for i in range(len(self.__map["报告期"])):
            if not self.__map["报告期"][i]:
                continue
            result = {}
            for k in self.__map:
                if len(self.__map[k]) == 4:
                    result[k] = self.__map[k][i]
            results[self.__map["报告期"][i]] = result
        return results


def parse_sina_stock_financial_statement(body):
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
            raise BlankStockFinancialStatement('Content is %s' % (body))
        return results
    