#!/bin/bash

. env.sh

cd $LUANDUN_HOME/src/luandun/tools/ && python worker.py -t magicformula
