#!/bin/bash
# Color Schema
RED='\033[0;31m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'
# Color Schema
LOG_LEVEL="INFO"
NETWORK="aiot-network"

AIOT_CORE_IMAGE="aiot-core"
AIOT_CORE="aiot-core"
AIOT_CORE_PORT=9250

MONGODB="aiot-mongodb"
MONGODB_PORT=27017
CRADEDB="aiot-cratedb"

CB="aiot-cb"
CB_PORT=1026

HM="aiot-hm"
HM_PORT=8668

IOTA_UL="aiot-iotagent"
IOTA_UL_NPORT=4041
IOTA_UL_SPORT=7896

IOTA_JSON="aiot-iotagent-json"
IOTA_JSON_NPORT=4042
IOTA_JSON_SPORT=7897

echo -e "\n${RED}Install Docker Engine.\n${NC}"

sudo apt install -y docker docker.io
sudo sysctl -w vm.max_map_count=262144

echo -e "\n${RED}Create Docker Network and Volume.\n${NC}"

sudo docker network create $NETWORK
sudo docker volume create mongodb_volume
sudo docker volume create cratedb_volume

echo -e "\n${RED}Start Data-backend DB.\n${NC}"

sudo docker run --name=$MONGODB --volume=mongodb_volume:/data --expose=$MONGODB_PORT --network=$NETWORK --env="TZ=Asia/Taipei" --detach mongo:3.6 --bind_ip_all --smallfiles
sudo docker run --name=$CRADEDB --network=$NETWORK --volume=cratedb_volume:/data --expose=4200 --expose=4300 --env="TZ=Asia/Taipei" --detach crate:3.1.2 crate -Clicense.enterprise=false -Cauth.host_based.enabled=false -Ccluster.name=fiware -Chttp.cors.enabled=true -Chttp.cors.allow-origin="*"

echo -e "\n${RED}Start Data-backend Context-Broker and History Manager.\n${NC}"

sudo docker run --name=$CB --network=$NETWORK --expose=$CB_PORT --env="TZ=Asia/Taipei" --detach fiware/orion:2.4.0 -dbhost $MONGODB -logLevel $LOG_LEVEL
sudo docker run --name=$HM --network=$NETWORK --expose=$HM_PORT --env="CRATE_HOST=aiot-cratedb" --env="TZ=Asia/Taipei" --detach smartsdk/quantumleap:0.7.5

echo -e "\n${RED}Start IoT-Agent.\n${NC}"

sudo docker run --name=$IOTA_UL --network=$NETWORK --expose=$IOTA_UL_NPORT --expose=$IOTA_UL_SPORT -p $IOTA_UL_SPORT:$IOTA_UL_SPORT --env="IOTA_CB_HOST=$CB" --env="IOTA_CB_PORT=$CB_PORT" --env="IOTA_NORTH_PORT=$IOTA_UL_NPORT" --env="IOTA_REGISTRY_TYPE=mongodb" --env="IOTA_LOG_LEVEL=$LOG_LEVEL" --env="IOTA_TIMESTAMP=false" --env="IOTA_CB_NGSI_VERSION=v2" --env="IOTA_AUTOCAST=true" --env="IOTA_MONGO_HOST=$MONGODB" --env="IOTA_MONGO_PORT=$MONGODB_PORT" --env="IOTA_MONGO_DB=iotagentul" --env="IOTA_HTTP_PORT=$IOTA_UL_SPORT" --env="IOTA_PROVIDER_URL=$IOTA_UL:$IOTA_UL_NPORT" --env="TZ=Asia/Taipei" --detach fiware/iotagent-ul:1.11.0
sudo docker run --name=$IOTA_JSON --network=$NETWORK --expose=$IOTA_JSON_NPORT --expose=$IOTA_JSON_SPORT -p $IOTA_JSON_SPORT:$IOTA_JSON_SPORT --env="IOTA_CB_HOST=$CB" --env="IOTA_CB_PORT=$CB_PORT" --env="IOTA_NORTH_PORT=$IOTA_JSON_NPORT" --env="IOTA_REGISTRY_TYPE=mongodb" --env="IOTA_LOG_LEVEL=$LOG_LEVEL" --env="IOTA_TIMESTAMP=false" --env="IOTA_CB_NGSI_VERSION=v2" --env="IOTA_AUTOCAST=true" --env="IOTA_MONGO_HOST=$MONGODB" --env="IOTA_MONGO_PORT=$MONGODB_PORT" --env="IOTA_MONGO_DB=iotagentjson" --env="IOTA_HTTP_PORT=$IOTA_JSON_SPORT" --env="IOTA_PROVIDER_URL=$IOTA_JSON:$IOTA_JSON_NPORT" --env="TZ=Asia/Taipei" --detach fiware/iotagent-json

echo -e "\n${RED}Write IoT-Agent Setting to iotagent_config.cfg .\n${NC}"

echo "{\"iotagent_setting\":[{\"Iot-Agent-Url\":\"http://${IOTA_UL}:${IOTA_UL_NPORT}\",\"Device-Port\":${IOTA_UL_SPORT},\"Resource\":\"/iot/d\"},{\"Iot-Agent-Url\":\"http://${IOTA_JSON}:${IOTA_JSON_NPORT}\",\"Device-Port\":${IOTA_JSON_SPORT},\"Resource\":\"/iot/json\"}]}" >../../Source/iotagent_config.cfg

echo -e "\n${BLUE}Show running container.\n${NC}"

sudo docker ps -a

echo -e "\n${RED}Build AIOT-CORE image.\n${NC}"

sudo docker build -t $AIOT_CORE_IMAGE -f ../../Support/Dockerfile ../../.

echo -e "\n${RED}Start AIOT-CORE.\n${NC}"

sudo docker run --name $AIOT_CORE --network=$NETWORK -p $AIOT_CORE_PORT:9250 --env "LOG=$LOG_LEVEL" --detach aiot-core

echo -e "\n${BLUE}Attach to AIOT-CORE log output, press ctrl-C to detach.\n${NC}"
sudo docker logs -f $AIOT_CORE
