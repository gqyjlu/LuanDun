# -*- coding: utf-8 -*-


'''
Created on 2014年7月2日

@author: prstcsnpr
'''


import datetime
from HTMLParser import HTMLParser
import logging
import string

from cqlengine import columns
from cqlengine.models import Model
from tornado import gen
from tornado import httpclient
import tornado.web

from luandun.api import taskqueue


class GDPHTMLParser(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)
        self.map = {}
        self.map_flag = False
        self.list = []
        self.list_flag = False
        
    def handle_starttag(self, tag, attrs):
        if 'table' == tag:
            for name, value in attrs:
                if 'id' == name and 'tb' == value:
                    self.map_flag = True
        elif 'tr' == tag:
            if self.map_flag:
                if 0 == len(attrs):
                    self.list_flag = True
                    
    def __get_key(self, data):
        if data.find('1-4') > 0:
            return data[0:4] + '1231'
        elif data.find('1-3') > 0:
            return data[0:4] + '0930'
        elif data.find('1-2') > 0:
            return data[0:4] + '0630'
        else:
            return data[0:4] + '0331'
            
    def handle_endtag(self, tag):
        if 'table' == tag:
            self.map_flag = False
        elif 'tr' == tag:
            if self.map_flag:
                if self.list_flag:
                    self.map[self.__get_key(self.list[0])] = self.list[1]
                self.list_flag = False
                self.list = []
            
    def handle_data(self, data):
        if self.map_flag and self.list_flag and data.strip():
            self.list.append(data.strip())


class GDP(Model):
    __keyspace__ = "magicformula"
    __table_name__ = "gdp"
    key = columns.Text(primary_key=True)
    value = columns.Float()
    date = columns.Date()
    

def get():
    return GDP.get(key='gdp')


def put(entry):
    entry.save()
    
    
class UpdateGDPHandler(tornado.web.RequestHandler):
    
    def __get_recent_gdp_date(self, year, m):
        q4 = datetime.date(year=year, month=12, day=31)
        q3 = datetime.date(year=year, month=9, day=30)
        q2 = datetime.date(year=year, month=6, day=30)
        q1 = datetime.date(year=year, month=3, day=31)
        last_year = year - 1
        if q4.strftime('%Y%m%d') in m:
            return q4
        elif q4.replace(year=last_year).strftime('%Y%m%d') in m:
            if q3.strftime('%Y%m%d') in m and q3.replace(year=last_year).strftime('%Y%m%d') in m:
                return q3
            elif q2.strftime('%Y%m%d') in m and q2.replace(year=last_year).strftime('%Y%m%d') in m:
                return q2
            elif q1.strftime('%Y%m%d') in m and q1.replace(year=last_year).strftime('%Y%m%d') in m:
                return q1
            else:
                return None
        else:
            return None
    
    def __get_gdp(self, body):
        parser = GDPHTMLParser()
        parser.feed(body.decode('GBK').encode('UTF-8'))
        for i in range(2):
            recent_gdp_date = self.__get_recent_gdp_date(datetime.date.today().year - i, parser.map)
            if recent_gdp_date is not None:
                break
        if recent_gdp_date is None:
            logging.warn('There is no gdp date')
            return
        if recent_gdp_date.month == 12:
            this_gdp_date = recent_gdp_date.strftime('%Y%m%d')
            return (string.atof(parser.map[this_gdp_date]) * 100000000, recent_gdp_date)
        else:
            this_gdp_date = recent_gdp_date.strftime('%Y%m%d')
            last_gdp_date = recent_gdp_date.replace(recent_gdp_date.year - 1).strftime('%Y%m%d')
            last_year_date = datetime.date(recent_gdp_date.year - 1, 12, 31).strftime('%Y%m%d')
            return ((string.atof(parser.map[this_gdp_date])
                    + string.atof(parser.map[last_year_date])
                    - string.atof(parser.map[last_gdp_date]))
                    * 100000000, recent_gdp_date)
    
    @gen.coroutine    
    def get(self):
        try:
            url = "http://data.eastmoney.com/cjsj/gdp.html"
            client = httpclient.AsyncHTTPClient()
            response = yield client.fetch(url)
            if response.code == 200:
                value, date = self.__get_gdp(response.body)
                entry = get()
                entry.value = value
                entry.date = date
                put(entry)
        except Exception as e:
            logging.exception(e)
            taskqueue.add(url='/tasks/updategdp',
                          queue_name='updategdp',
                          method='GET')
