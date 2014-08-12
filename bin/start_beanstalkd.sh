#!/bin/bash

. env.sh

if [ "x$BEANSTALKD_POST" = "x" ]; then
	BEANSTALKD_POST = 11300
fi

mkdir -p $LUANDUN_HOME/data/beanstalkd
mkdir -p $LUANDUN_HOME/log/beanstalkd

nohup beanstalkd -l 127.0.0.1 -p $BEANSTALKD_POST -b $LUANDUN_HOME/data/beanstalkd -f0 2>&1 | cronolog $LUANDUN_HOME/log/beanstalkd/beanstalkd.%Y%m%d.log &
