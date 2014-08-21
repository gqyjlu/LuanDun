#!/bin/bash

. env.sh

if [ "x$BEANSTALKD_PORT" = "x" ]; then
	BEANSTALKD_PORT=11300
fi

mkdir -p $LUANDUN_HOME/data/beanstalkd
mkdir -p $LUANDUN_HOME/log/beanstalkd

nohup beanstalkd -l 127.0.0.1 -p $BEANSTALKD_PORT -b $LUANDUN_HOME/data/beanstalkd -f0 2>&1 | cronolog $LUANDUN_HOME/log/beanstalkd/beanstalkd.%Y%m%d.log &
