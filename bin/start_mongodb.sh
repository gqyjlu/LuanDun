#!/bin/bash

. env.sh

mongod --dbpath $LUANDUN_HOME/data/mongodb 2>&1 | cronolog $LUANDUN_HOME/log/mongodb/mongodb.%Y%m%d.log &
