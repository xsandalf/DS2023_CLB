#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app, PORT_NUMBER, FIRST_ID, LEADER_PORT, LEADER_NAME, IS_LEADER, register_container, get_master_container, NAME
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
QUEUE = []
ID = FIRST_ID
MISSING = []

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
    global QUEUE
    global IS_STOPPED
    global ID
    global PORT_NUMBER
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
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
                    LOGS.append("Worker has crashed")
                    send_request(name="database", port="3003", data="{id},Worker has crashed".format(id=ID), route="logs")
                    QUEUE.append(",".join([str(hash), payload]))
                    #workload = CONTAINER_WORKLOADS.pop(int(CONTAINERS.index(port.strip())/2))
                    CONTAINERS.remove(name)
                    CONTAINERS.remove(port)
                    send_request(name="database", port="3003", data="{},{}".format(PORT_NUMBER, port), route="down")

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
                response = send_request(name=LEADER_NAME, port=LEADER_PORT, data=",".join([PORT_NUMBER, str(hash), stdout]), route="result")
                if response.text != "OK":
                    LOGS.append("Leader has crashed")
                    send_request(name="database", port="3003", data="{id},Leader has crashed".format(id=ID), route="logs")
                    QUEUE.append(",".join([PORT_NUMBER, str(hash), stdout]))
                    send_request(name="database", port="3003", data="{},{}".format(PORT_NUMBER, LEADER_PORT), route="down")
                else:
                    WORKLOAD.remove({"hash" : hash, "payload": payload})
            thread = threading.Thread(target=long_running_task, kwargs={})
            thread.start()
            return ("OK", 202)

@app.route("/load" , methods=["GET", "POST"])
def load():
    global IS_STOPPED
    global ID
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
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
    global IS_STOPPED
    global CONTAINER_WORKLOADS
    global CLIENT
    global CLIENT_PORT
    global ID
    global MISSING
    global PORT_NUMBER
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
    if request.method == "POST":
        port, hash, result = request.data.decode("utf-8").strip().split(",")
        LOGS.append("Received result: {hash}".format(hash=hash))
        #send_logging_post_req("{id},Received result: {hash}".format(id=ID, hash=hash))
        send_request(name="database", port="3003", data="{id},Received result: {hash}".format(id=ID, hash=hash), route="logs")
        try:
            if MISSING.index(hash):
                MISSING.remove(hash)
        except ValueError:
            print(port, flush=True)
            print(PORT_NUMBER, flush=True)
            if port != PORT_NUMBER:
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
    global PORT_NUMBER
    global NAME
    global ID
    IS_STOPPED = not IS_STOPPED
    if IS_STOPPED:
        LOGS.append("CRASH :(")
        send_request(name="database", port="3003", data="{id},has crashed".format(id=ID), route="logs")
    else:
        LOGS.append("RECOVERED :)")
        send_request(name="database", port="3003", data="{id},has recovered".format(id=ID), route="logs")
        ID = register_container(PORT_NUMBER)
        get_master_container()
        send_request(name=LEADER_NAME, port=LEADER_PORT, data="{},{}".format(NAME, PORT_NUMBER), route="register")
    return "{}".format(IS_STOPPED)

@app.route("/leader", methods=["POST"])
def leader():
    global IS_STOPPED
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
    global LEADER_NAME
    global LEADER_PORT
    global IS_LEADER
    global PORT_NUMBER
    global ID
    global CLIENT_PORT
    global WORKLOAD
    global MISSING
    if request.method == "POST":
        name, port = request.data.decode("utf-8").strip().split(",")
        if int(PORT_NUMBER) == int(port):
            IS_LEADER = True
            get_client()
            get_pending()
            get_containers()
            for data in QUEUE:
                _, hash, result = data.split(",")
                try:
                    print("HUPPENED", flush=True)
                    if MISSING.index(str(hash)):
                        print("HUPPENED2", flush=True)
                        MISSING.remove(str(hash))
                except ValueError:
                    pass
                LOGS.append("Sent result: {hash} for client to port: {port}".format(hash=hash, port=CLIENT_PORT)
                            .format(id=ID, hash=hash, port=CLIENT_PORT))
                send_request(name="database", port="3003", data="{id},Sent result: {hash} for client to port: {port}"
                            .format(id=ID, hash=hash, port=CLIENT_PORT), route="logs")
                send_request(name=CLIENT, port=CLIENT_PORT, data="{},{}".format(hash,result), route="result")
            if len(MISSING) > 0:
                find_missing()
            if len(MISSING) > 0:
                get_missing()
        LEADER_NAME = name
        LEADER_PORT = port
        for data in QUEUE:
            print(data, flush=True)
            _, hash, result = data.split(",")
            LOGS.append("Sent result: {hash} for leader to port: {port}".format(hash=hash, port=LEADER_PORT))
            send_request(name="database", port="3003", data="{id},Sent result: {hash} for leader to port: {port}"
                        .format(id=ID, hash=hash, port=LEADER_PORT), route="logs")
            send_request(name=LEADER_NAME, port=LEADER_PORT, data=",".join([PORT_NUMBER, str(hash), result]), route="result")
            for work in WORKLOAD:
                if work["hash"] == hash:
                    WORKLOAD.remove(work)
    return ("OK", 200)

@app.route("/register", methods=["POST"])
def register():
    global IS_STOPPED
    global CONTAINERS
    global CONTAINER_WORKLOADS
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
    if request.method == "POST":
        name, port = request.data.decode("utf-8").strip().split(",")
        CONTAINERS.append(name)
        CONTAINERS.append(port)
        CONTAINER_WORKLOADS.append([])
    return ("OK", 200)

@app.route("/pending", methods=["POST"])
def pending():
    global WORKLOAD
    if request.method == "POST":
        response = ""
        for work in WORKLOAD:
            response += "{},".format(work["hash"])
        if response != "":
            response = response[:-1]
    return (response, 200)

# Ask database for worker containers
@app.before_first_request
def get_containers():
    global CONTAINERS
    global CONTAINER_WORKLOADS
    global ID
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
    global ID
    container_load = []
    loads = []
    delete = -1
    for i in range(0, len(CONTAINERS), 2):
        #cpu, ram = get_container_load(name=CONTAINERS[i], port=CONTAINERS[i+1]).text.split(",")
        response = send_request(name=CONTAINERS[i], port=CONTAINERS[i+1], data="", route="load")
        if response.text == "I am simulating a crash, please do not bother me":
            delete = i
            LOGS.append("Worker has crashed")
            send_request(name="database", port="3003", data="{id},Worker has crashed".format(id=ID), route="logs")
            send_request(name="database", port="3003", data="{},{}".format(PORT_NUMBER, CONTAINERS[i+1]), route="down")
        else:
            cpu, ram = response.text.split(",")
            loads.append(float(cpu) + float(ram) + 5 * len(CONTAINER_WORKLOADS[int(i / 2)]))
    if delete != -1:
        del CONTAINER_WORKLOADS[(int(CONTAINERS.index(CONTAINERS[i+1])/2))]
        del CONTAINERS[i]
        # index moves down dummie
        del CONTAINERS[i]
    return loads
"""
def get_container_load(name, port):
    # URL for database, check port number from /DS2023_CLB/docker-compose.yml for changes
    # URL needs include protocol
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://{}:{}/load".format(name, port)
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with log data to database container
    return requests.post(url, data="", headers=headers)
"""
"""
def send_logging_post_req(data):
    # URL for database, check port number from /DS2023_CLB/docker-compose.yml for changes
    # URL needs include protocol
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://database:3003/logs"
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with log data to database container
    requests.post(url, data=data, headers=headers)
"""
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

def get_pending():
    global CLIENT
    global CLIENT_PORT
    global MISSING
    response = send_request(name=CLIENT, port=CLIENT_PORT, data="", route="pending")
    pending_hashes = response.text.split(",")
    print(pending_hashes, flush=True)
    LOGS.append("Got pending hashes from client")
    send_request(name="database", port="3003", data="{id},Got pending hashes from client"
                .format(id=ID), route="logs")
    MISSING.extend(pending_hashes)
    print(MISSING, flush=True)

def find_missing():
    global MISSING
    global CONTAINERS
    global CONTAINER_WORKLOADS
    for i in range(0, len(CONTAINERS), 2):
        response = send_request(name=CONTAINERS[i], port=CONTAINERS[i+1], data="", route="pending")
        pending_hashes = response.text.split(",")
        print(pending_hashes, flush=True)
        LOGS.append("Ask for pending hashes from workers")
        send_request(name="database", port="3003", data="{id},Ask for pending hashes from workers"
                    .format(id=ID), route="logs")
        for hash in pending_hashes:
            print("HAPPENED1", flush=True)
            try:
                print("HAPPENED2", flush=True)
                if MISSING.index(str(hash)):
                    MISSING.remove(str(hash))
                    CONTAINER_WORKLOADS[int(i / 2)].append(hash)
                    print("HAPPENED", flush=True)
            except ValueError:
                pass

def get_missing():
    global CLIENT
    global CLIENT_PORT
    global QUEUE
    global NAME
    global PORT_NUMBER
    response = send_request(name=CLIENT, port=CLIENT_PORT, data="", route="missing")
    pending_payloads = response.text.split(",")
    print(pending_payloads, flush=True)
    LOGS.append("Ask for missing payloads from client")
    send_request(name="database", port="3003", data="{id},Ask for missing payloads from client"
                .format(id=ID), route="logs")
    if len(pending_payloads) > 1:
        for i in range(0, len(pending_payloads), 2):
            #QUEUE.append(",".join([str(pending_payloads[i]), pending_payloads[i+1]]))
            data = ",".join([str(pending_payloads[i]), pending_payloads[i+1]])
            response = send_request(name=NAME, port=PORT_NUMBER, data=data, route="payload")
