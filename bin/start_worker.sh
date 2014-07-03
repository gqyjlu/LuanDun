#!/bin/bash

. env.sh

mkdir -p $LUANDUN_HOME/log/worker

cd $LUANDUN_HOME/src/luandun/tools/ && python worker.py -t magicformula > $LUANDUN_HOME/log/worker/stdout.log 2> $LUANDUN_HOME/log/worker/stderr.log &
