#!/bin/bash

. env.sh

mkdir -p $LUANDUN_HOME/log/tornado

cd $LUANDUN_HOME/src/luandun/business/magicformula/ && python main.py 2>&1 | cronolog $LUANDUN_HOME/log/tornado/tornado.%Y%m%d.log &
