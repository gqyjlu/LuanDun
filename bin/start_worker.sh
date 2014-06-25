#!/bin/bash

. env.sh

cd ../src/luandun/tools/ && python worker.py -t magicformula
