import json
import os 
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import logging
import subprocess
import multiprocessing
import socket
from SystemManager import initFiware,initIotagent
from SensorManager import sensorRegister,sensorManager,sensorCheck
from DataManager import dataQuerier
import requests
import time
from DebugManager import cleanEverything
#from ModelManager import modelEntrance

#Activity Portal
PORT=9250
TIMEZONE=+8
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        #logging.info("POST request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        try:
            content_length = int(self.headers['Content-Length'])
        except:
            self._set_response(400)
            self.wfile.write("{'Status':'No Data Input'}".encode('utf-8'))
            return 400
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            post_data_dict = json.loads(post_data)
        except:
            return 400
        
        
        
        # /notify
        # Endpoint for fiware subscription
        # Stage 1:
        # Data Collecting
        # New Data come from /notify and call DataQuier to store data at local.
        # 
        # Stage 2:
        # Swarm
        # When data amount reach threadhold
        # DataQuier call swarm to make OPF's discription.
        # After finish swarm, deleted local file.
        # 
        # Stage 3:(fork 1)
        # Process all data in CrateDB
        # Queue data where prediction value == NULL in CrateDB and process than all
        # Stage 3:(fork 2)
        # Process new come data from /notify
        
        # Server Restart
        # If OPF's discription exist
        #     Start Stage 3
        # Else
        #     Start count current data in CrateDB and local data
        #         If local data < CrateDB
        #             Que Data from crateDB and store in local data
        #         Start Stage 1
        
        if str(self.path)=="/notify":
            #logging.info("New notification come from orion.")

            try:
                entity_id=post_data_dict["data"][0]["id"]
                dataType=post_data_dict["data"][0]["count"]["type"]
                fiware_service=self.headers["Fiware-Service"]
                count=post_data_dict["data"][0]["count"]["value"]
                timestamp=post_data_dict["data"][0]["timestamp"]["value"]
            except:
                self._set_response(404)
                self.wfile.write("{'Status':'Wrong Formate.'}".encode('utf-8'))
                return 404
            __PATH__=os.path.dirname(os.path.abspath(__file__))
            if not os.path.isfile(__PATH__+"/Data/global-setting.json"):
                logging.warning("Initial FIWARE First")
                self._set_response(404)
                self.wfile.write("{'Status':'Initial FIWARE First'}".encode('utf-8'))
                return 404
            if not os.path.isfile(__PATH__+"/Data/IoT/"+fiware_service+"/iotagent-setting.json"):
                logging.warning("Initial Iotagent Named '"+fiware_service+"' First")
                self._set_response(404)
                meaasge="{'Status':'Initial Iotagent Named '"+fiware_service+"' First'}"
                self.wfile.write(meaasge.encode('utf-8'))
                return 404
            if count==" " and timestamp=="1970-01-01T00:00:00.00Z":
                self._set_response(200)
                return 200

            Data={"entity_id":entity_id,"fiware_service":fiware_service,"count":count,"timestamp":timestamp,"dataType":dataType}

            result=dataQuerier.dataStore(Data)

            if result==[]:
                self._set_response(200)
                return 200
            else:
                self._set_response(409)
                msg="{'Status':'Error occured.','ErrorCode':"+str(result)+"}"
                self.wfile.write(msg.encode('utf-8'))
                #TODO: Anomaly Raise
                #TODO
                #TODO
                #TODO
                #TODO
                #TODO
                #Signal Apache
                return 409
            

        
        
        
        # /sensor
        # Create a new sensor entity by calling SensorTool/sensorManager.py.
        # It will create a new folder named {sensorType}+"-"+{device_id} and a new endpoint sensorID
        # Contain some metadata like sensor static_attribute and counter for HTM swarm
        # After swarm, it will contain HTM model parmeter file and HTM saved model.
        
        elif str(self.path)=="/sensor":
            IOTAGENT=str(self.headers["Iot-Agent"])
            if not os.path.isfile("./Data/global-setting.json"):
                self._set_response(404)
                self.wfile.write("{'Status':'Initial FIWARE First'}".encode('utf-8'))
                return 404
            if not os.path.isfile("./Data/IoT/"+IOTAGENT+"/iotagent-setting.json"):
                self._set_response(404)
                meaasge="{'Status':'Initial Iotagent Named '"+IOTAGENT+"' First'}"
                self.wfile.write(meaasge.encode('utf-8'))
                return 404
            logging.info("Checking new sensor entity")
            
            ret=sensorCheck.sensorCheck(post_data_dict)
            
            if type(ret)==list:
                self._set_response(400)
                meaasge="{'Status':'Missing Sensor Information '"+str(ret)+"' First'}"
                self.wfile.write(meaasge.encode('utf-8'))
                return 400
            elif ret==0:
                pass
            else:
                return 404
                
            logging.info("Creating new sensor entity")

            with open("./Data/global-setting.json") as f:
                setting=json.load(f)
            with open("./Data/IoT/"+IOTAGENT+"/iotagent-setting.json") as f:
                setting.update(json.load(f))
            setting.update(post_data_dict)
            setting["iotagent_setting"]["fiware-service"]=IOTAGENT
            
            ret=sensorRegister.sensorRegister(setting)
            
            if ret!=201:
                if ret==409:
                    self._set_response(409)
                    self.wfile.write('{"name":"DUPLICATE_DEVICE_ID","message":"A device with the same pair (Service, DeviceId) was found:Sensor01"}'.encode('utf-8')) 
                else:
                    self._set_response(400)
                    self.wfile.write("{'Status':'Fail'}".encode('utf-8'))
                return ret
                
            self._set_response(201)
            self.wfile.write("{'Status':'Create'}".encode('utf-8'))

            
            
        
        # /fiware-init
        # Initial fiware with "global-setting.json"
        # Check if there are only one "House" type entity already exist.

        elif str(self.path)=="/fiware-init":
            
            logging.info("Initializing FIWARE")
            
            ret=initFiware.initFiware(post_data_dict)
            if ret==-1:
                self._set_response(422)
                self.wfile.write("{'Status':'Already Exists'}".encode('utf-8'))
            elif ret==0:    
                self._set_response(201)
                os.mkdir("Data/IoT/")
                self.wfile.write("{'Status':'Create'}".encode('utf-8'))
        
                
            
        
        # /iotagent-init
        # Initial iotagent with "global-setting.json"
        
        elif str(self.path)=="/iotagent-init":
            logging.info("Initializing Iot-Agent")
            try:
                with open("./Data/global-setting.json","r" ) as f:
                    setting=json.load(f)
            except:
                self._set_response(404)
                self.wfile.write("{'Status':'Initial FIWARE First'}".encode('utf-8'))
                return 404
            setting.update(post_data_dict)
            
            
            ret=initIotagent.initIotagent(setting)
            
            if ret==0:
                self._set_response(201)
                self.wfile.write("{'Status':'Create'}".encode('utf-8'))
            else:
                self._set_response(ret)
                if ret==409:
                    self.wfile.write("{'Status':'Already Exist'}".encode('utf-8'))
                else:
                    self.wfile.write("{'Status':'Fail'}".encode('utf-8'))
        
        else:
            logging.error("Error usage at endpoint.")
            self._set_response(400)
            self.wfile.write("{'Status':'Fail'}".encode('utf-8'))
            return 400
        logging.info("End of POST")

    def do_GET(self):
                
        # /sensors:
        # List all sensor currently prepairing/ready to run HTM
        
        # /sensors/<sensorID>
        # /sensors/<sensorID>/Info
        # List sensor {sensorID}'s info
        
        # /sensors/<sensorID>/LearningState
        # Show sensor {sensorID}'s learning state
        # if before swarm, return current count , ETA time or count
        # if after swarm, return model parameter
        
        
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        #TODO
        #TODO
        #TODO
        #TODO
        #TODO

    def do_DELETE(self):
        # /sensors/<sensorID>
        # Clean all sensor {sensorID} setting, include entity on fiware orion context broker and iotagent and HTM model

        logging.info("DELETE request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        
        if str(self.path)=="/sensors":
            logging.info("Creating new sensor entity")
            self._set_response(201)
            self.wfile.write("{'Status':'Create'}".encode('utf-8'))
            #TODO
            #TODO
            #TODO
            #TODO
            #TODO
        if str(self.path)=="/all":
            logging.info("Clean All")
            cleanEverything.cleanAll()
            self._set_response(201)
            self.wfile.write("{'Status':'Clean All'}".encode('utf-8'))
            

        
        else:
            logging.error("Error usage at endpoint.")
            self._set_response(400)
            self.wfile.write("{'Status':'Fail'}".encode('utf-8'))
            return 400
        
    def do_PATCH(self):
        # /sensors/<snesorID>/attrs/<attribute>/value
        # update a sensor static_attribute with new value
        
        # /sensors/<snesorID>/HTM_Model/<attribute>/value
        # update a sensor HTM model with new value
        logging.info("PATCH request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        #TODO
        #TODO
        #TODO
        #TODO
        #TODO

        
    def _set_response(self,status_code):
        self.send_response(status_code)
        self.send_header("Content-type","application/json")
        self.end_headers()

    
def run(server_class=ThreadingHTTPServer,handler_class=Handler,port=PORT):
    ip_address=socket.gethostbyname(socket.gethostname())
    server_address=(ip_address,port)
    
    httpd=server_class(server_address,handler_class)
    logging.info("Starting httpd...\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.critical("Catch KeyboardInterrupt")
    httpd.server_close()
    logging.info("Stopping httpd...\n")

def init(): 
    __PATH__=os.path.dirname(os.path.abspath(__file__))
    
    logging.info("Starting Module Entrance...\n")
    from ModelManager import modelEntrance
    pid=os.fork()
    if pid==0:
        
        MEprocess=multiprocessing.Process(None,target=modelEntrance.modelEntrance, args=(logging.INFO,))
        MEprocess.start()
        MEprocess.join()
        #p=subprocess.Popen(["python3.7",__PATH__+"/ModelManager/modelEntrance.py"])
        #p.wait()
    else: 
        return 0
    
    
if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    init()
    logging.info("init done")
    run()

        
    
