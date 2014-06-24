# -*- coding: utf-8 -*-


'''
Created on 2014年6月24日

@author: prstcsnpr
'''


import tornado.ioloop
import tornado.web
from luandun.api import db
from luandun.business.magicformula.update_stock_info import UpdateStockInfoHandler
from luandun.business.magicformula.update_stock_info import UpdateMarketCapitalHandler
from luandun.config import config


application = tornado.web.Application([
    (r"/magicformula/updatestockinfo", UpdateStockInfoHandler),
    (r"/magicformula/updatemarketcapital", UpdateMarketCapitalHandler),
])


if __name__ == '__main__':
    config_manager = config.get_config_manager().initialize("magicformula")
    db.get_cassandra_manager().initialize("magicformula")
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()