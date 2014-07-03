#!/bin/bash

. env.sh

cassandra > $LUANDUN_HOME/log/cassandra/stdout.log 2> $LUANDUN_HOME/log/cassandra/stderr.log
