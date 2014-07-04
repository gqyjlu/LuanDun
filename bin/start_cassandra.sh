#!/bin/bash

. env.sh

cassandra 2>&1 | cronolog $LUANDUN_HOME/log/cassandra/cassandra.%Y%m%d.log
