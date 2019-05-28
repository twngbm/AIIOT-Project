import os
import subprocess
#Check if context-broker image exist
if "context-broker" not in os.popen("docker images").read():
    subprocess.Popen('sudo docker build -t context-broker .',shell=True).wait()
#Check if network exist
if "fiware_default" not in os.popen("docker network ls").read():
    print(os.popen("docker network create fiware_default").read())
    print(os.popen("docker network ls").read())

#Check if mongo-db container exist
if "mongo-db" in os.popen("docker ps -a").read():
    db_output=os.popen("docker start mongo-db").read()
else:
    db_output=os.popen("docker run -d --name=mongo-db --network=fiware_default --expose=27017 mongo:3.6 --bind_ip_all --smallfiles").read()
print(db_output)
#Check if fiware context broker exist
if "context-broker" in os.popen("docker ps -a").read():
    fiware_output=os.popen("docker start context-broker").read()
else:
    fiware_output=os.popen("docker run -d --name context-broker -h -orion --network=fiware_default -p 1026:1026 context-broker -dbhost mongo-db").read()
print(fiware_output)
print(os.popen("docker ps -a").read())
