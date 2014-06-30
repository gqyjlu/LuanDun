# -*- coding: utf-8 -*-


'''
Created on 2014年6月27日

@author: prstcsnpr
'''


import tornado.web

from luandun.business.magicformula.stock import FormulaResult


class ShowMagicFormulaResultHandler(tornado.web.RequestHandler):
    
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.write(FormulaResult.get(name="magicformula").result)