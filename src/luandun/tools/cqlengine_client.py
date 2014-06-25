# -*- coding: utf-8 -*-


'''
Created on 2014年6月25日

@author: prstcsnpr
'''


from cqlengine import connection
from cqlengine.management import sync_table

from luandun.business.magicformula.stock import StockModel


if __name__ == '__main__':
    connection.setup(['127.0.0.1'])
    sync_table(StockModel)
    sm = StockModel.create(ticker="2", title="f")
    print sm.ticker