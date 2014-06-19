#!/bin/bash

nohup beanstalkd -l 127.0.0.1 -p 11300 -b ../data/beanstalkd -f0 > ../log/beanstalkd.out 2> ../log/beanstalkd.err &

#echo $! > beanstalkd.pid