import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import socket
import SystemManager
from SystemManager import initFiware, initIotagent
from SensorManager import sensorRegister, sensorManager
from DataManager import dataQuerier, dataAccessor
import requests
import time
import signal


PORT = 9250
TIMEZONE = +8
MODEL_PORT = 5000


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # /entities -> Create Entity (House,Floor,Room,Entity)
        # /service-groups -> Setup Service Group
        # /devices -> Create Sensor Node Entity
        # /devices/<service_group>/<deviceID>/controls -> Send Command to <service_group>'s <deviceID>
        # /subscriptions -> Create Subscription
        try:
            content_length = int(self.headers['Content-Length'])
        except:
            return self._set_response(400, "{'Status':'No Data Input'}")
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            post_data_dict = json.loads(post_data)
        except:
            return self._set_response(400, "{'Status':'Wrong Data Format'}")

        if str(self.path) == "/init":
            ret = SystemManager.writeSetback(post_data_dict)

            if ret == -1:
                return self._set_response(422, "{'Status':'Already Exists'}")
            elif ret == -2:
                return self._set_response(400, "{'Status':'Wrong Format'}")
            elif ret == 0:
                return self._set_response(201, "{'Status':'Create'}")
        elif str(self.path) == "/notify":

            try:
                entity_id = post_data_dict["data"][0]["id"]
                dataType = post_data_dict["data"][0]["count"]["type"]
                fiware_service = self.headers["Fiware-Service"]
                count = post_data_dict["data"][0]["count"]["value"]
                timestamp = post_data_dict["data"][0]["timestamp"]["value"]
            except:
                return self._set_response(404, "")

            if count == " " and timestamp == "1970-01-01T00:00:00.00Z":
                return self._set_response(200, "")

            Data = {"entity_id": entity_id, "fiware_service": fiware_service,
                    "count": count, "timestamp": timestamp, "dataType": dataType}

            result = dataQuerier.dataStore(Data, MODEL_PORT)

            if result == []:
                return self._set_response(200, "")

            else:

                # TODO: Anomaly Raise
                # TODO
                # TODO
                # TODO
                # TODO
                # TODO
                # Signal Apache
                msg = "{'Status':'Error occured.','ErrorCode':"+str(result)+"}"
                return self._set_response(409, msg)
        elif str(self.path).find("/devices") == 0:
            if self.path.split("/")[-1] == "controls":
                logging.info("Command")

                resourceSplit = self.path.split("/")
                try:
                    fiware_service = resourceSplit[2]
                    deviceID = resourceSplit[3]
                except:
                    return self._set_response(400, "{'Status':'Wrong Format'}")

                rts = dataQuerier.commandIssue(fiware_service, deviceID,
                                               post_data_dict, MODEL_PORT)

                if rts == 0:
                    return self._set_response(200, "{'Status':'Command Issue'}")
                elif rts == -1:
                    return self._set_response(400, "{'Status':'Target Sensor Not Found'}")
                elif rts == -2:
                    return self._set_response(400, "{'Status':'Error Command Type'}")
                elif rts == -3:
                    return self._set_response(400, "{'Status':'Target Service Group Not Found'}")
                elif rts == -4:
                    return self._set_response(400, "{'Status':'Wrong Format'}")

            elif self.path.split("/")[-1] == "devices":
                logging.info("Creating new sensor entity")

                device = sensorRegister.Device()

                ret, check = device.sensorRegister(post_data_dict)

                if ret == 201:
                    self._set_response(201, "{'Status':'Create'}")
                elif ret == 409:
                    return self._set_response(409, '{"name":"DUPLICATE_DEVICE_ID","message":"A device with the same pair (Service, DeviceId) was found')
                elif ret == -1:
                    return self._set_response(404, "{'Status':'Initial FIWARE First'}")
                elif ret == 400:
                    message = "{'Status':'Missing Sensor Information '" + \
                        str(check)+"}"
                    return self._set_response(400, message)
                elif ret == -2:
                    message = "{'Status':'Initial Iotagent Named '" + \
                        post_data_dict["agent_info"]["Service-Group"] + \
                        "' First'}"
                    return self._set_response(404, message)
                else:
                    return self._set_response(400, "{'Status':'Fail'}")
            else:
                return self._set_response(400, "{'Status':'Error Usage at Endpoint'}")
        elif str(self.path).find("/entities") == 0:

            logging.info("Create Entities")

            ret = initFiware.createEntity(post_data_dict)

            if ret == -1:
                return self._set_response(422, "{'Status':'Already Exists'}")
            elif ret == -2:
                return self._set_response(400, "{'Status':'Wrong Format'}")
            elif ret == -3:
                return self._set_response(404, "{'Status':'Can't Find Context Broker'}")
            elif ret == 0:
                return self._set_response(201, "{'Status':'Create'}")
        elif str(self.path) == "/service-groups":
            logging.info("Initializing Service Group")

            IotAgent = initIotagent.IotAgent()

            ret = IotAgent.createIotagent(post_data_dict)

            if ret == 0:
                return self._set_response(201, "{'Status':'Create'}")
            elif ret == -1:
                return self._set_response(404, "{'Status':'Initial FIWARE First'}")
            elif ret == -2:
                return self._set_response(400, "{'Status':'Wrong Format, Must Be List'}")
            elif ret == 422:
                return self._set_response(ret, "{'Status':'Already Exist'}")
            elif ret == 400:
                return self._set_response(ret, "{'Status':'Wrong Format'}")
            else:
                return self._set_response(ret, "{'Status':'Fail'}")
        elif self.path.find("/subscriptions/") == 0:
            logging.info("Create New Subscription")
            try:
                creator = dataAccessor.Creator(MODEL_PORT)
            except IOError:
                return self._set_response(400, "{'Status':'Enpty'}")
            try:
                creator.createSubscription(self.path, post_data_dict)
                return self._set_response(201, "{'Status':'Create Subscription Success'}")
            except:
                return self._set_response(400, "{'Status':'Wrong Format'}")

        else:
            logging.error("Error usage at endpoint.")
            return self._set_response(400, "{'Status':'Fail'}")

        logging.info("End of POST")

    def do_GET(self):

        # /entities -> List house information

        # /entities/<entityID> -> Show <entitiyID>'s detail
        # /attrs
        # /attrs/<attributes>
        # /attrs/<attributes>/value
        # ?options=keyValues
        # ?type=House,Floor,Room

        # /devices/<service_group> -> List Device under <service_group>
        # /devices/<service_group>/<deviceID> -> Show <deviceID>'s detail
        # /devices/<service_group>/<deviceID>/model -> Show <deviceID>'s Model State
        # /devices/<service_group>/<deviceID>/controls -> Show <deviceID>'s supported actionType and action
        # /devices/<service_group>/<deviceID>/data -> List Sensor Data
        # ?limit=<limit_count>
        # ?attrs=a,b

        # /subscriptions/<service_group> -> List Subscription under <service_group>
        # /subscriptions/<service_group>/<subscriptionID> -> Show <subscriptionID>'s detail

        # /service-groups -> List service-group
        # ?<key>=<value>&
        # /service-groups/<service_group> -> show <service_group>'s detail
        # /service-groups/<service_group>/devices -> List Device under <service_group>
        # /service-groups/<service_group>/subscriptions -> List Subscription under <service_group>

        try:
            viewer = dataAccessor.Viewer(MODEL_PORT)
        except IOError:
            return self._set_response(400, "{'Status':'Nothing To Read'}")
        try:
            endpoint, query = self._url_resource_parser(self.path)
            resourceSplit = endpoint.split("/")
            baseEndpoint = resourceSplit.pop(1)
            additionalURL = "/".join(resourceSplit)
        except:
            return self._set_response(400, "{'Status':'Wrong Format'}")
        r = -1
        if baseEndpoint == "entities":
            logging.info("Show entities detail")
            r = viewer.listEntities(additionalURL, query)

        elif baseEndpoint == "devices":
            logging.info("Show devices' information")
            r = viewer.listDevices(additionalURL, query)

        elif baseEndpoint == "subscriptions":
            logging.info("Show subscriptions' information")
            r = viewer.listSubscriptions(additionalURL, query)

        elif baseEndpoint == "service-groups":
            logging.info("List service-group")
            r = viewer.listServiceGroups(additionalURL, query)
        if r == -1:
            return self._set_response(400, "{'Status':'Wrong Use of Endpoint'}")
        elif r == -2:
            return self._set_response(404, "{'Status':'Service Not Found'}")
        else:
            return self._set_response(200, r)

    def do_DELETE(self):
        # /reset -> Reset
        # /entities/<entityID>
        # /service-groups/<Service-Group> -> Remove <Service-Group> and <Service-Group>'s <Device>
        # /devices/<service_group>/<deviceID> -> Remove <deviceID>
        # /subscriptions/<service_group>/<subscriptionID> -> Remove <subscriptionID>
        try:
            Cleaner = dataAccessor.Cleaner(MODEL_PORT)
        except IOError:
            return self._set_response(400, "{'Status':'Nothing To Clean'}")

        endpoint, query = self._url_resource_parser(self.path)

        if endpoint == None:
            return self._set_response(400, "{'Status':'Wrong Format'}")

        elif endpoint == "/reset":
            logging.info("Reset")
            Cleaner.reset()
            return self._set_response(201, "{'Status':'Remove Done'}")
        elif endpoint.find("/entities/") == 0:
            try:
                if endpoint.split("/")[3] == "attrs":
                    try:
                        logging.info("Remove Entity's attributes")
                        entityID = endpoint.split("/")[2]
                        attrName = endpoint.split("/")[4]
                        retcode, rettext = Cleaner.removeEntityAttr(
                            entityID, attrName)
                        return self._set_response(retcode, rettext)
                    except:
                        return self._set_response(400, "{'Status':'Wrong Format'}")
                else:
                    return self._set_response(400, "{'Status':'Error usage at endpoint.'}")
            except:
                logging.info("Remove Entity")
                try:
                    entityID = endpoint.split("/")[2]
                except:
                    return self._set_response(400, "{'Status':'Wrong Format'}")
                ret, msg = Cleaner.removeEntity(entityID)
                return self._set_response(ret, msg)
        elif endpoint.find("/devices/") == 0:

            logging.info("Remove IoT Sensor")
            try:
                Cleaner.removeIoTSensor(endpoint.split(
                    "/")[2], endpoint.split("/")[3])
                return self._set_response(201, "{'Status':'Remove Done'}")
            except:
                return self._set_response(400, "{'Status':'Wrong Format'}")

        elif endpoint.find("/service-groups/") == 0:
            logging.info("Remove Service Group")
            try:
                Cleaner.removeServiceGroup(endpoint.split(
                    "/")[2])
                return self._set_response(201, "{'Status':'Remove Done'}")
            except:
                return self._set_response(400, "{'Status':'Wrong Format'}")

        elif endpoint.find("/subscriptions/") == 0:
            logging.info("Remove Subscription")
            try:
                Cleaner.removeSubscription(
                    endpoint.split("/")[2], endpoint.split("/")[3])
                return self._set_response(201, "{'Status':'Remove Done'}")
            except:
                return self._set_response(400, "{'Status':'Wrong Format'}")
        else:
            return self._set_response(400, "{'Status':'Error usage at endpoint.'}")

    def do_PATCH(self):
        # /entities/<entityID>/
        try:
            content_length = int(self.headers['Content-Length'])
        except:
            return self._set_response(400, "{'Status':'No Data Input'}")
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            post_data_dict = json.loads(post_data)
        except:
            return self._set_response(400, "{'Status':'Wrong Data Format'}")
        try:
            updater = dataAccessor.Updater(MODEL_PORT)
        except IOError:
            return self._set_response(400, "{'Status':'Nothing To Update'}")

        endpoint, query = self._url_resource_parser(self.path)
        if endpoint.find("/entities/") == 0:
            logging.info("Update entity attributes")
            try:
                retcode, rettext = updater.updateEntity(
                    endpoint.split("/")[2], post_data_dict)
                return self._set_response(retcode, rettext)
            except:
                return self._set_response(400, "{'Status':'Wrong Format'}")
        else:
            return self._set_response(400, "{'Status':'Error usage at endpoint.'}")

    def _url_resource_parser(self, url: str):
        url = url.split("?")
        if len(url) > 2:
            return None, None
        endpoint = url[0]
        query = {}
        if len(url) == 2:
            try:
                q = url[1].split("&")
                for i in q:
                    kv = i.split("=")
                    query[kv[0]] = kv[1]
            except:
                return None, None
        return endpoint, query

    def _set_response(self, status_code, msg):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(str(msg).encode('utf-8'))
        return status_code


def run(server_class=HTTPServer, handler_class=Handler, port=PORT):
    ip_address = socket.gethostbyname(socket.gethostname())
    server_address = (ip_address, port)

    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        logging.info("Stopping httpd...\n")


def init():
    pass
    loglevel = os.getenv('LOG', "ERROR")
    if loglevel == "DEBUG":
        LOG_LEVEL = logging.DEBUG
    elif loglevel == "INFO":
        LOG_LEVEL = logging.INFO
    elif loglevel == "WARNING":
        LOG_LEVEL = logging.WARNING
    elif loglevel == "ERROR":
        LOG_LEVEL = logging.ERROR
    elif loglevel == "CRITICAL":
        LOG_LEVEL = logging.CRITICAL
    else:
        LOG_LEVEL = logging.ERROR
    logging.basicConfig(level=LOG_LEVEL)
    logging.info("MAIN:START {pid}".format(pid=os.getpid()))


def handle_sigchld(signum, frame):
    try:
        while True:
            cpid, status = os.waitpid(-1, os.WNOHANG)
            if cpid == 0:
                break
            exitcode = status >> 8
            logging.info('-------MAIN:Process '+str(cpid) +
                         ' EXIT with exit code ' + str(exitcode)+'-------')
    except OSError as e:
        pass


def handle_sigterm(*args):
    raise KeyboardInterrupt()


if __name__ == "__main__":
    signal.signal(signal.SIGCHLD, handle_sigchld)
    signal.signal(signal.SIGTERM, handle_sigterm)
    init()
    run()
