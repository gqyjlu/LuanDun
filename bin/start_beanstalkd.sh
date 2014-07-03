#!/bin/bash

. env.sh

mkdir -p $LUANDUN_HOME/data/beanstalkd
mkdir -p $LUANDUN_HOME/log/beanstalkd

nohup beanstalkd -l 127.0.0.1 -p 11300 -b $LUANDUN_HOME/data/beanstalkd -f0 > $LUANDUN_HOME/log/beanstalkd/beanstalkd.out 2> $LUANDUN_HOME/log/beanstalkd/beanstalkd.err &
