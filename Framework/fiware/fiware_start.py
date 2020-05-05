import os
import subprocess
#Check if context-broker image exist
if "context-broker" not in os.popen("docker images").read():
    subprocess.Popen('docker build -t context-broker .',shell=True).wait()

#Check if mongo-db container exist
if "mongodb" in os.popen("docker ps -a").read():
    db_output=os.popen("docker start mongodb").read()
else:
    db_output=os.popen("docker run -d --name=mongodb mongo:3.6").read()
print(db_output)
#Check if fiware context broker exist
if "context-broker" in os.popen("docker ps -a").read():
    fiware_output=os.popen("docker start context-broker").read()
else:
    fiware_output=os.popen("docker run -d --name context-broker --link mongodb:mongodb -p 1026:1026 context-broker -dbhost mongodb").read()
print(fiware_output)
print(os.popen("docker ps -a").read())
