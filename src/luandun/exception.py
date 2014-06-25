# -*- coding: utf-8 -*-


'''
Created on 2014年6月25日

@author: prstcsnpr
'''


class LuanDunException(Exception):pass
class NoAvailableTaskQueueException(LuanDunException):pass
class TaskQueueConnectionException(LuanDunException):pass