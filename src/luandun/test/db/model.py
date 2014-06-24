# -*- coding: utf-8 -*-


'''
Created on 2014年6月23日

@author: prstcsnpr
'''


from luandun.api import db

class TestModel(db.Model):
    ticker = db.StringProperty(indexed=False)
    title = db.StringProperty(indexed=False)

if __name__ == '__main__':
    entry = TestModel.get_or_insert("")
    #entry.ticker = "1"
    #entry.put()
