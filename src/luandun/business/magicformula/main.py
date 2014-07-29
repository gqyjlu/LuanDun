# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


from cqlengine import connection
from cqlengine.management import sync_table
import tornado.ioloop
import tornado.web

from luandun.business.magicformula.gdp import GDP
from luandun.business.magicformula.gdp import UpdateGDPHandler
from luandun.business.magicformula.show_stock_info import ShowGrahamFormulaHandler
from luandun.business.magicformula.show_stock_info import ShowMagicFormulaHandler
from luandun.business.magicformula.show_stock_info import ShowNetCurrentAssetApproachHandler
from luandun.business.magicformula.show_stock_info import ShowStockDataHandler
from luandun.business.magicformula.show_stock_info import UpdateGrahamFormulaHandler
from luandun.business.magicformula.show_stock_info import UpdateMagicFormulaHandler
from luandun.business.magicformula.show_stock_info import UpdateNetCurrentAssetApproachHandler
from luandun.business.magicformula.stock import Stock
from luandun.business.magicformula.stock import StockData
from luandun.business.magicformula.stock import StockEarnings
from luandun.business.magicformula.stock import StockMarketCapital
from luandun.business.magicformula.stock import StockTitle
from luandun.business.magicformula.stock_result import StockResult
from luandun.business.magicformula.update_stock_info import UpdateDataHandler
from luandun.business.magicformula.update_stock_info import UpdateEarningsHandler
from luandun.business.magicformula.update_stock_info import UpdateMarketCapitalHandler
from luandun.business.magicformula.update_stock_info import UpdateStockInfoHandler
from luandun.business.magicformula.update_stock_info import UpdateStockListHandler
from luandun.business.magicformula.update_stock_info import UpdateTitleHandler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")


application = tornado.web.Application([
    (r'/magicformula', MainHandler),
    (r"/magicformula/updategdp", UpdateGDPHandler),
    (r"/magicformula/updatedata", UpdateDataHandler),
    (r"/magicformula/updatestockinfo", UpdateStockInfoHandler),
    (r"/magicformula/updatestocklist", UpdateStockListHandler),
    (r"/magicformula/updatemarketcapital", UpdateMarketCapitalHandler),
    (r"/magicformula/updateearnings", UpdateEarningsHandler),
    (r"/magicformula/updatetitle", UpdateTitleHandler),
    (r"/magicformula/updatemagicformula", UpdateMagicFormulaHandler),
    (r"/magicformula/updategrahamformula", UpdateGrahamFormulaHandler),
    (r"/magicformula/updatenetcurrentassetapproach", UpdateNetCurrentAssetApproachHandler),
    (r"/magicformula/showmagicformula", ShowMagicFormulaHandler),
    (r"/magicformula/showgrahamformula", ShowGrahamFormulaHandler),
    (r"/magicformula/shownetcurrentassetapproach", ShowNetCurrentAssetApproachHandler),
    (r"/magicformula/showstockdata", ShowStockDataHandler),
])


if __name__ == '__main__':
    connection.setup(['127.0.0.1'])
    sync_table(Stock)
    sync_table(GDP)
    sync_table(StockResult)
    sync_table(StockTitle)
    sync_table(StockMarketCapital)
    sync_table(StockEarnings)
    sync_table(StockData)
    
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()