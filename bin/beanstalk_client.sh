#!/bin/bash

. env.sh

cd $LUANDUN_HOME/src/luandun/tools/ && python beanstalk_client.py
