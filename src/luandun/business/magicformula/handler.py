# -*- coding: utf-8 -*-


'''
Created on 2014年8月9日

@author: prstcsnpr
'''


from luandun.api.db import MongoHandler


class MagicFormulaHandler(MongoHandler):
    @property
    def dbname(self):
        if not hasattr(self, "__dbname"):
            self.__dbname = "magicformula"
            return self.__dbname
        