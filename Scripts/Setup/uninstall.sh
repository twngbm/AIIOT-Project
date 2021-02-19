#!/bin/bash
# Color Schema
RED='\033[0;31m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'
# Color Schema

echo -e "\n${RED}Stop and Remove Container.\n${NC}"

sudo docker rm $(docker kill $(docker ps -a -q --filter='name=aiot-' --format="{{.ID}}"))

echo -e "\n${RED}Remove Docker Network and Volume.\n${NC}"
sudo docker network rm aiot-network
sudo docker volume rm cratedb_volume mongodb_volume
#

echo -e "\n${RED}Do You want to Remove Created Docker Images?[y/n]?${NC}"
read confirm
if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    echo -e "\n${RED}Remove Docker Images.\n${NC}"
    sudo docker rmi aiot-core fiware/iotagent-json mongo:3.6 fiware/orion:2.4.0 fiware/iotagent-ul:1.11.0 smartsdk/quantumleap:0.7.5 crate:3.1.2
fi
echo -e "\n${BLUE}Remove Done.\n${NC}"
