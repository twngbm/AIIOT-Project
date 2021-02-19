import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import socket
import SystemManager
from SystemManager import initFiware, initIotagent, serviceGroup
from SystemManager.SysConfig import PORT, TIMEZONE, MODEL_PORT
from SensorManager import sensorRegister, sensorManager
from DataManager import dataQuerier, dataAccessor
import requests
import time
import signal


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # /entities -> Create Entity (House,Floor,Room,Entity)
        # /service-groups -> Setup Service Group
        # /devices -> Create Sensor Node Entity
        # /devices/<service_group>/<deviceName>/controls -> Send Command to <service_group>'s <deviceName>
        # /subscriptions -> Create Subscription
        try:
            content_length = int(self.headers['Content-Length'])
        except:
            return self._set_response(422, "{'Status':'No Data Input'}")

        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            post_data_dict = json.loads(post_data)
        except:
            return self._set_response(422, "{'Status':'Wrong Data Format'}")

        if str(self.path) == "/init":
            retCode, retText = SystemManager.writeSetback(post_data_dict)
            if retCode != 201:
                return self._set_response(retCode, retText)

            else:
                IotAgent = initIotagent.IotAgent()
                retCode, retText = IotAgent.initIotagent()
                if retCode == 201:
                    return self._set_response(201, "System Initinal Success.")

                else:
                    return self._set_response(retCode, retText)

        elif str(self.path) == "/notify":
            try:
                entity_id = post_data_dict["data"][0]["id"]
                service_group = entity_id.split(":")[2]
                dataType = post_data_dict["data"][0]["count"]["type"]
                count = post_data_dict["data"][0]["count"]["value"]
                timestamp = post_data_dict["data"][0]["timestamp"]["value"]
            except:
                return self._set_response(404, "")

            if timestamp == "1970-01-01T00:00:00.00Z":
                return self._set_response(200, "")
            logging.debug(f"Notify:{post_data_dict}")
            Data = {"entity_id": entity_id, "service_group": service_group,
                    "count": count, "timestamp": timestamp, "dataType": dataType}

            result = dataQuerier.dataStore(Data, MODEL_PORT)

            if result == []:
                return self._set_response(200, "")

            else:
                msg = "{'Status':'Error occured.','ErrorCode':"+str(result)+"}"
                return self._set_response(409, msg)

        elif str(self.path).find("/devices") == 0:
            if self.path.split("/")[-1] == "controls":
                resourceSplit = self.path.split("/")
                try:
                    service_group = resourceSplit[2]
                    deviceName = resourceSplit[3]
                    retCode, retText = dataQuerier.commandIssue(service_group, deviceName,
                                                                post_data_dict, MODEL_PORT)
                except:
                    retCode = 422
                    retText = "{'Status':'Wrong Format'}"
                return self._set_response(retCode, retText)

            elif self.path.split("/")[-1] == "devices":
                device = sensorRegister.Device(TIMEZONE)
                ret, check = device.sensorRegister(post_data_dict)
                self._set_response(ret, check)
            else:
                return self._set_response(400, "{'Status':'Error Usage at Endpoint'}")

        elif str(self.path).find("/entities") == 0:
            ret, retText = initFiware.createEntity(post_data_dict)
            return self._set_response(ret, str(retText))

        elif str(self.path) == "/service-groups":
            retCode, retText = serviceGroup.createServiceGroup(post_data_dict)
            return self._set_response(retCode, retText)

        elif self.path.find("/subscriptions/") == 0:
            try:
                creator = dataAccessor.Creator(MODEL_PORT)
            except IOError:
                return self._set_response(400, "{'Status':'Enpty'}")

            rtc, rtt = creator.createSubscription(self.path, post_data_dict)
            try:
                return self._set_response(rtc, rtt)

            except KeyError:
                return self._set_response(400, "{'Status':'Service Group Missing'}")

            except:
                return self._set_response(400, "{'Status':'Wrong Format'}")

        elif self.path == "/test":
            logging.critical(
                f"{self.address_string()}:POST on /test with message:\n {post_data_dict}")
            return self._set_response(200, "{''}")

        else:
            return self._set_response(404, "{'Status':'Endpoint Not Supported'}")

    def do_GET(self):
        # /entities -> List house information

        # /entities/<entityID> -> Show <entitiyID>'s detail
        # /attrs
        # /attrs/<attributes>
        # /attrs/<attributes>/value
        # ?options=keyValues
        # ?type=House,Floor,Room

        # /devices/<service_group> -> List Device under <service_group>
        # /devices/<service_group>/<deviceName> -> Show <deviceName>'s detail
        # /devices/<service_group>/<deviceName>/model -> Show <deviceName>'s Model State
        # /devices/<service_group>/<deviceName>/controls -> Show <deviceName>'s supported actionType and action
        # /devices/<service_group>/<deviceName>/data -> List Sensor Data
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
            r = viewer.listEntities(additionalURL, query)
        elif baseEndpoint == "devices":
            r = viewer.listDevices(additionalURL, query)
        elif baseEndpoint == "subscriptions":
            r = viewer.listSubscriptions(additionalURL, query)
        elif baseEndpoint == "service-groups":
            r = viewer.listServiceGroups(additionalURL, query)
        if r == -1:
            return self._set_response(400, '{"Status":"Wrong Use of Endpoint"}')

        elif r == -2:
            return self._set_response(404, '{"Status":"Service Not Found"}')

        elif r == -3:
            return self._set_response(400, '{"Status":"Missing Necessary Information"}')

        else:
            return self._set_response(200, r)

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
            try:
                retcode, rettext = updater.updateEntity(
                    endpoint.split("/")[2], post_data_dict)
                return self._set_response(retcode, rettext)

            except:
                return self._set_response(400, "{'Status':'Wrong Format'}")

        else:
            return self._set_response(400, "{'Status':'Error usage at endpoint.'}")

    def do_DELETE(self):
        # /reset -> Reset
        # /entities/<entityID>
        # /service-groups/<Service-Group> -> Remove <Service-Group> and <Service-Group>'s <Device>
        # /devices/<service_group>/<deviceName> -> Remove <deviceName>
        # /subscriptions/<service_group>/<subscriptionID> -> Remove <subscriptionID>
        try:
            Cleaner = dataAccessor.Cleaner(MODEL_PORT)
        except IOError:
            return self._set_response(400, "{'Status':'Nothing To Clean'}")

        endpoint, query = self._url_resource_parser(self.path)
        if endpoint == None:
            return self._set_response(400, "{'Status':'Wrong Format'}")

        elif endpoint == "/reset":
            Cleaner.reset()
            return self._set_response(201, "{'Status':'Remove Done'}")

        elif endpoint.find("/entities/") == 0:
            try:
                if endpoint.split("/")[3] == "attrs":
                    try:
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
                try:
                    entityID = endpoint.split("/")[2]
                except:
                    return self._set_response(400, "{'Status':'Wrong Format'}")

                ret, msg = Cleaner.removeEntity(entityID)
                return self._set_response(ret, msg)

        elif endpoint.find("/devices/") == 0:
            try:
                Cleaner.removeIoTSensor(endpoint.split(
                    "/")[2], endpoint.split("/")[3])
                return self._set_response(201, "{'Status':'Remove Done'}")

            except:
                return self._set_response(400, "{'Status':'Wrong Format'}")

        elif endpoint.find("/service-groups/") == 0:
            try:
                Cleaner.removeServiceGroup(endpoint.split(
                    "/")[2])
                return self._set_response(201, "{'Status':'Remove Done'}")

            except:
                return self._set_response(400, "{'Status':'Wrong Format'}")

        elif endpoint.find("/subscriptions/") == 0:
            try:
                Cleaner.removeSubscription(
                    endpoint.split("/")[2], endpoint.split("/")[3])
                return self._set_response(201, "{'Status':'Remove Done'}")

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

    def log_message(self, format, *args):
        infolist = args[0].split(" ")
        logging.info(self.address_string()+" " +
                     infolist[0]+" On {"+infolist[1]+"}")
        return


def run(server_class=HTTPServer, handler_class=Handler, port=PORT):
    ip_address = socket.gethostbyname(socket.gethostname())
    server_address = (ip_address, port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        logging.critical("AIOT CORE STOP")


def init():
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

    formatter = '| %(levelname)s | %(asctime)s | %(process)d | %(message)s |'
    PATH = os.path.dirname(os.path.abspath(__file__))
    lf = logging.FileHandler(f"{PATH}/aiot.log")
    ch = logging.StreamHandler()
    logging.basicConfig(level=LOG_LEVEL, format=formatter,
                        datefmt="%Y-%m-%d %H:%M:%S", handlers=[lf, ch])

    logging.critical("AIOT CORE START")


def handle_sigchld(signum, frame):
    try:
        while True:
            cpid, status = os.waitpid(-1, os.WNOHANG)
            if cpid == 0:
                break
            exitcode = status >> 8
            logging.info('\n|-------'+str(cpid) +
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
