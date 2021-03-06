# -*- coding: utf-8 -*-


'''
Created on 2014年8月16日

@author: prstcsnpr
'''


import sys

import asyncmongo
import tornado


lines = []
db = asyncmongo.Client(pool_id="magicformula", 
                       dbname="magicformula",
                       host="127.0.0.1",
                       port=27017)


def db_callback(response, error):
    if len(lines) > 0:
        fields = lines.pop()
        db.stock_model.update({"ticker" : fields[2]},
                              {"$set" : {"category" : fields[1], "subcategory" : fields[0]}},
                              safe=True,
                              callback=db_callback)
    else:
        tornado.ioloop.IOLoop.instance().stop()
        

def main(argv):
    with open(argv[1]) as f:
            for line in f.readlines():
                fields = line.split()
                lines.append(fields)
    db_callback(None, None)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main(sys.argv)
    
                