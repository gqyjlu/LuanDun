# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


import tornado.ioloop
import tornado.web

from luandun.business.magicformula.gdp import UpdateGDPHandler
from luandun.business.magicformula.show import ShowGrahamFormulaHandler
from luandun.business.magicformula.show import ShowMagicFormulaHandler
from luandun.business.magicformula.show import ShowStockDataHandler
from luandun.business.magicformula.update import UpdateGrahamFormulaHandler
from luandun.business.magicformula.update import UpdateMagicFormulaHandler
from luandun.business.magicformula.update import UpdateStockDataHandler
from luandun.business.magicformula.update import UpdateStockFinancialStatementHandler
from luandun.business.magicformula.update import UpdateStockInfoHandler
from luandun.business.magicformula.update import UpdateStockListHandler
from luandun.business.magicformula.update import UpdateStockMarketCapitalHandler
from luandun.business.magicformula.update import UpdateStockTitleHandler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")


application = tornado.web.Application([
    (r'/magicformula', MainHandler),
    
    (r"/magicformula/updategdp", UpdateGDPHandler),
    (r"/magicformula/updatestockinfo", UpdateStockInfoHandler),
    (r"/magicformula/updatestocklist", UpdateStockListHandler),
    (r"/magicformula/updatestockmarketcapital", UpdateStockMarketCapitalHandler),
    (r"/magicformula/updatestocktitle", UpdateStockTitleHandler),
    (r"/magicformula/updatemagicformula", UpdateMagicFormulaHandler),
    (r"/magicformula/updategrahamformula", UpdateGrahamFormulaHandler),
    (r"/magicformula/updatestockfinancialstatement", UpdateStockFinancialStatementHandler),
    (r"/magicformula/updatestockdata", UpdateStockDataHandler),
    
    (r"/magicformula/showmagicformula", ShowMagicFormulaHandler),
    (r"/magicformula/showgrahamformula", ShowGrahamFormulaHandler),
    (r"/magicformula/showstockdata/([0-9]+)", ShowStockDataHandler),
])


if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()