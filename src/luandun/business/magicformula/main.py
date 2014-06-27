# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


from cqlengine import connection
from cqlengine.management import sync_table
import tornado.ioloop
import tornado.web

from luandun.business.magicformula.show_stock_info import ShowMagicFormulaResultHandler
from luandun.business.magicformula.stock import FormulaResult
from luandun.business.magicformula.stock import StockModel
from luandun.business.magicformula.update_stock_info import UpdateFinancialStatementHandler
from luandun.business.magicformula.update_stock_info import UpdateFormulaItemHandler
from luandun.business.magicformula.update_stock_info import UpdateMagicFormulaResultHandler
from luandun.business.magicformula.update_stock_info import UpdateMarketCapitalHandler
from luandun.business.magicformula.update_stock_info import UpdateStockInfoHandler
from luandun.business.magicformula.update_stock_info import UpdateTitleHandler


application = tornado.web.Application([
    (r"/magicformula/updatestockinfo", UpdateStockInfoHandler),
    (r"/magicformula/updatemarketcapital", UpdateMarketCapitalHandler),
    (r"/magicformula/updatetitle", UpdateTitleHandler),
    (r"/magicformula/updatefinancialstatement", UpdateFinancialStatementHandler),
    (r"/magicformula/updateformulaitem", UpdateFormulaItemHandler),
    (r"/magicformula/updatemagicformularesult", UpdateMagicFormulaResultHandler),
    (r"/magicformula/showmagicformularesult", ShowMagicFormulaResultHandler),
])


if __name__ == '__main__':
    connection.setup(['127.0.0.1'])
    sync_table(StockModel)
    sync_table(FormulaResult)
    
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()