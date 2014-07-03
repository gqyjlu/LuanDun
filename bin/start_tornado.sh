#!/bin/bash

. env.sh

mkdir -p $LUANDUN_HOME/log/tornado

cd $LUANDUN_HOME/src/luandun/business/magicformula/ && python main.py > $LUANDUN_HOME/log/tornado/stdout.log 2> $LUANDUN_HOME/log/tornado/stderr.log &
