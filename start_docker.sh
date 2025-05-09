#!/bin/sh
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v `pwd`/data/mongodb:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:latest