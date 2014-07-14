#!/bin/bash

. env.sh

mkdir -p $LUANDUN_HOME/log/worker

cd $LUANDUN_HOME/src/luandun/tools/ && python worker.py -t magicformula 2>&1 | cronolog $LUANDUN_HOME/log/worker/worker.%Y%m%d.log &
