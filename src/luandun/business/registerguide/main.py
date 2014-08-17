# -*- coding: utf-8 -*-


'''
Created on 2014年8月11日

@author: prstcsnpr
'''


import tornado

from luandun.business.registerguide.handler import CountHandler


application = tornado.web.Application([
    (r'/registerguide/count', CountHandler),
])


if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()