#!/bin/bash

. env.sh

if [ "x$MONGO_PORT" = "x" ]; then
	MONGO_PORT=27017
fi
mongod --port $MONGO_PORT --dbpath $LUANDUN_HOME/data/mongodb 2>&1 | cronolog $LUANDUN_HOME/log/mongodb/mongodb.%Y%m%d.log &
