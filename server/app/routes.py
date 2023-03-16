#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app, PORT_NUMBER, ID, LEADER_PORT, LEADER_NAME, IS_LEADER
from flask import render_template, request
import requests
import psutil
import subprocess
import threading

# Bad coding practice, "dirty hack" :D
PAYLOAD = ""
PAYLOADS = []
LOGS = []
CONTAINERS = []
CONTAINER_WORKLOADS = []
WORKLOAD = []
CLIENT = ""
CLIENT_PORT = -1
IS_STOPPED = False

# Register callbacks with URLs
@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"

@app.route("/payload", methods=["GET", "POST"])
def payload():
    global CONTAINERS
    global CONTAINER_WORKLOADS
    global WORKLOAD
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 1337)
    if request.method == "POST":
        if IS_LEADER:
            hash, payload = request.data.decode("utf-8").strip().split(",")
            def long_running_task(**kwargs):
                LOGS.append("Received payload: {hash}".format(hash=hash))
                #send_logging_post_req("{id},Received payload: {hash}".format(id=ID, hash=hash))
                send_request(name="database", port="3003", data="{id},Received payload: {hash}"
                            .format(id=ID, hash=hash), route="logs")
                loads = get_container_loads()
                idx = loads.index(min(loads))
                name = CONTAINERS[idx*2]
                port = CONTAINERS[idx*2+1]
                container = "{}, {}".format(name, port)
                #CONTAINER_WORKLOADS[int(idx / 2].append(hash)
                CONTAINER_WORKLOADS[idx].append(hash)
                LOGS.append("Sent payload: {hash} for execution to port: {port}".format(hash=hash, port=port))
                #send_logging_post_req("{id},Sent payload: {hash} for execution to port: {port}"
                #                      .format(id=ID, hash=hash, port=port))
                send_request(name="database", port="3003", data="{id},Sent payload: {hash} for execution to port: {port}"
                            .format(id=ID, hash=hash, port=port), route="logs")
                # LOG THE RETURN
                response = send_request(name=name, port=port, data=",".join([str(hash), payload]), route="payload")
                if response.text != "OK":
                    print("OH OH", flush=True)
            thread = threading.Thread(target=long_running_task, kwargs={})
            thread.start()
            return ("OK", 202)
        else:
            hash, payload = request.data.decode("utf-8").strip().split(",")
            def long_running_task(**kwargs):
                LOGS.append("Received payload: {hash}".format(hash=hash))
                #send_logging_post_req("{id},Received payload: {hash}".format(id=ID, hash=hash))
                send_request(name="database", port="3003", data="{id},Received payload: {hash}"
                            .format(id=ID, hash=hash), route="logs")
                WORKLOAD.append({"hash" : hash, "payload": payload})
                # THIS IS BORKED
                code = payload.split("\n")
                runnable = ""
                for c in code:
                    if not (len(c) == 0 or c.isspace()):
                        #print(c[4:], flush=True)
                        runnable += c[4:]
                        runnable += ";"
                runnable = runnable[:-1]
                stdout = subprocess.check_output(["python", "-c", runnable]).decode("utf-8").strip()
                print(stdout, flush=True)
                LOGS.append("Sent result: {hash} for leader to port: {port}".format(hash=hash, port=LEADER_PORT))
                #send_logging_post_req("{id},Sent result: {hash} for leader to port: {port}"
                #                      .format(id=ID, hash=hash, port=LEADER_PORT))
                send_request(name="database", port="3003", data="{id},Sent result: {hash} for leader to port: {port}"
                            .format(id=ID, hash=hash, port=LEADER_PORT), route="logs")
                send_request(name=LEADER_NAME, port=LEADER_PORT, data=",".join([PORT_NUMBER, str(hash), stdout]), route="result")
            thread = threading.Thread(target=long_running_task, kwargs={})
            thread.start()
            return ("OK", 202)

@app.route("/load" , methods=["GET", "POST"])
def load():
    if request.method == "POST":
        cpu = psutil.cpu_percent(4)
        ram = psutil.virtual_memory()[2]
        LOGS.append("The CPU usage is: {}".format(cpu))
        #send_logging_post_req("{id},CPU usage: {cpu}".format(id=ID, cpu=cpu))
        send_request(name="database", port="3003", data="{id},CPU usage: {cpu}".format(id=ID, cpu=cpu), route="logs")
        LOGS.append("RAM memory /%/ used: {}".format(ram))
        #send_logging_post_req("{id},RAM usage: {ram}".format(id=ID, ram=ram))
        send_request(name="database", port="3003", data="{id},RAM usage: {ram}".format(id=ID, ram=ram), route="logs")
    return ("{},{}".format(cpu,ram), 200)

@app.route("/result", methods=["GET", "POST"])
def result():
    global CONTAINER_WORKLOADS
    global CLIENT
    global CLIENT_PORT
    if request.method == "POST":
        port, hash, result = request.data.decode("utf-8").strip().split(",")
        LOGS.append("Received result: {hash}".format(hash=hash))
        #send_logging_post_req("{id},Received result: {hash}".format(id=ID, hash=hash))
        send_request(name="database", port="3003", data="{id},Received result: {hash}".format(id=ID, hash=hash), route="logs")
        CONTAINER_WORKLOADS[int(CONTAINERS.index(port.strip())/2)].remove(hash)
        LOGS.append("Sent result: {hash} for client to port: {port}".format(hash=hash, port=CLIENT_PORT))
        #send_logging_post_req("{id},Sent result: {hash} for client to port: {port}"
        #                      .format(id=ID, hash=hash, port=CLIENT_PORT))
        send_request(name="database", port="3003", data="{id},Sent result: {hash} for client to port: {port}"
                    .format(id=ID, hash=hash, port=CLIENT_PORT), route="logs")
        send_request(name=CLIENT, port=CLIENT_PORT, data=",".join([str(hash), result]), route="result")
    return ("OK", 200)

@app.route("/stop", methods=["GET"])
def stop():
    global IS_STOPPED
    IS_STOPPED = not IS_STOPPED
    return "{}".format(IS_STOPPED)

# Ask database for worker containers
@app.before_first_request
def get_containers():
    global CONTAINERS
    global CONTAINER_WORKLOADS
    if IS_LEADER:
        # Log leader status
        LOGS.append("Is master container")
        #send_logging_post_req("{id},Is master container".format(id=ID))
        send_request(name="database", port="3003", data="{id},Is master container".format(id=ID), route="logs")
        # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
        url = "http://database:3003/workers"
        # Basic headers
        headers = {"Content-type": "text/html; charset=UTF-8"}
        # Send the POST-request with container information to database container
        #LEADER_NAME, LEADER_PORT = requests.post(url, data="", headers=headers).text.split(",")
        containers = requests.post(url, data="", headers=headers).text.split(",")
        containers.pop()
        CONTAINERS = containers
        CONTAINER_WORKLOADS = []
        for i in range(0, len(CONTAINERS), 2):
            CONTAINER_WORKLOADS.append([])

@app.before_first_request
def get_client():
    global CLIENT
    global CLIENT_PORT
    if IS_LEADER:
        # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
        url = "http://database:3003/client"
        # Basic headers
        headers = {"Content-type": "text/html; charset=UTF-8"}
        CLIENT, CLIENT_PORT = requests.post(url, data="", headers=headers).text.split(",")

# Ask containers for their available CPU and memory
def get_container_loads():
    global CONTAINERS
    global CONTAINER_WORKLOADS
    container_load = []
    loads = []
    for i in range(0, len(CONTAINERS), 2):
        cpu, ram = get_container_load(name=CONTAINERS[i], port=CONTAINERS[i+1]).text.split(",")
        loads.append(float(cpu) + float(ram) + len(CONTAINER_WORKLOADS[int(i / 2)]))
    return loads

def get_container_load(name, port):
    # URL for database, check port number from /DS2023_CLB/docker-compose.yml for changes
    # URL needs include protocol
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://{}:{}/load".format(name, port)
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with log data to database container
    return requests.post(url, data="", headers=headers)

def send_logging_post_req(data):
    # URL for database, check port number from /DS2023_CLB/docker-compose.yml for changes
    # URL needs include protocol
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://database:3003/logs"
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with log data to database container
    requests.post(url, data=data, headers=headers)

def send_request(name, port, data, route):
    # URL needs include protocol
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://{}:{}/{}".format(name, port, route)
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with log data to database container
    return requests.post(url, data=data, headers=headers)
    #hash, sum = requests.post(url, data=data, headers=headers).text.split(",")
    #print("{},{}".format(hash,sum), flush=True)
    #return ("{},{}".format(hash,sum))
