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
    if request.method == "POST":
        if IS_LEADER:
            hash, payload = request.data.decode("utf-8").strip().split(",")
            def long_running_task(**kwargs):
                LOGS.append("Received payload: {hash}".format(hash=hash))
                send_logging_post_req("{id},Received payload: {hash}".format(id=ID, hash=hash))
                loads = get_container_loads()
                idx = loads.index(min(loads))
                name = CONTAINERS[idx*2]
                port = CONTAINERS[idx*2+1]
                container = "{}, {}".format(name, port)
                CONTAINER_WORKLOADS[int(idx / 2)].append(hash)
                LOGS.append("Sent payload: {hash} for execution to port: {port}".format(hash=hash, port=port))
                send_logging_post_req("{id},Sent payload: {hash} for execution to port: {port}"
                                      .format(id=ID, hash=hash, port=port))
                # LOG THE RETURN
                response = send_payload(name=name, port=port, data=",".join([str(hash), payload]))
                if response.text != "OK":
                    print("OH OH", flush=True)
            thread = threading.Thread(target=long_running_task, kwargs={})
            thread.start()
            return ("OK", 202)
            """
            LOGS.append("Received payload: {hash}".format(hash=hash))
            send_logging_post_req("{id},Received payload: {hash}".format(id=ID, hash=hash))
            loads = get_container_loads()
            idx = loads.index(min(loads))
            name = CONTAINERS[idx*2]
            port = CONTAINERS[idx*2+1]
            container = "{}, {}".format(name, port)
            CONTAINER_WORKLOADS[int(idx / 2)].append(hash)
            LOGS.append("Sent payload: {hash} for execution to port: {port}".format(hash=hash, port=port))
            send_logging_post_req("{id},Sent payload: {hash} for execution to port: {port}"
                                  .format(id=ID, hash=hash, port=port))
            # LOG THE RETURN
            response = send_payload(name=name, port=port, data=",".join([str(hash), payload]))
            print(response, flush=True)
            return (response, 200)"""
        else:
            hash, payload = request.data.decode("utf-8").strip().split(",")
            def long_running_task(**kwargs):
                LOGS.append("Received payload: {hash}".format(hash=hash))
                send_logging_post_req("{id},Received payload: {hash}".format(id=ID, hash=hash))
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
            thread = threading.Thread(target=long_running_task, kwargs={})
            thread.start()
            return ("OK", 202)
            """
            LOGS.append("Received payload: {hash}".format(hash=hash))
            send_logging_post_req("{id},Received payload: {hash}".format(id=ID, hash=hash))
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
            return ("{},{}".format(hash,stdout), 200)"""

@app.route("/load" , methods=["GET", "POST"])
def load():
    if request.method == "POST":
        cpu = psutil.cpu_percent(4)
        ram = psutil.virtual_memory()[2]
        LOGS.append("The CPU usage is: {}".format(cpu))
        send_logging_post_req("{id},CPU usage: {cpu}".format(id=ID, cpu=cpu))
        LOGS.append("RAM memory /%/ used: {}".format(ram))
        send_logging_post_req("{id},RAM usage: {ram}".format(id=ID, ram=ram))
    return ("{},{}".format(cpu,ram), 200)

# Ask database for worker containers
@app.before_first_request
def get_containers():
    global CONTAINERS
    global CONTAINER_WORKLOADS
    if IS_LEADER:
        # Log leader status
        LOGS.append("Is master container")
        send_logging_post_req("{id},Is master container".format(id=ID))
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

def send_payload(name, port, data):
    # URL needs include protocol
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://{}:{}/payload".format(name, port)
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with log data to database container
    return requests.post(url, data=data, headers=headers)
    #hash, sum = requests.post(url, data=data, headers=headers).text.split(",")
    #print("{},{}".format(hash,sum), flush=True)
    #return ("{},{}".format(hash,sum))
