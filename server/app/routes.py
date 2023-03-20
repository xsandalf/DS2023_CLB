#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app, PORT_NUMBER, FIRST_ID, LEADER_PORT, LEADER_NAME, IS_LEADER, register_container, get_master_container, NAME
from flask import render_template, request
import requests
import psutil
import subprocess
import threading

# Use global variables as local cache
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
# Main page for server, unused
@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"

# Routine for receiving payloads from either client or master container depending on server role
@app.route("/payload", methods=["GET", "POST"])
def payload():
    # Tell interpreter where to find variables
    global CONTAINERS
    global CONTAINER_WORKLOADS
    global WORKLOAD
    global QUEUE
    global IS_STOPPED
    global ID
    global PORT_NUMBER
    # Check if container is simulating a crash
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
    if request.method == "POST":
        # Check if container is the master container
        if IS_LEADER:
            # Get hash and payload from POST request
            hash, payload = request.data.decode("utf-8").strip().split(",")
            # Create a thread for handling a payload from client and choosing a worker container to execute it
            def long_running_task(**kwargs):
                # Log the receiving of payload from client
                LOGS.append("Received payload: {hash}".format(hash=hash))
                send_request(name="database", port="3003", data="{id},Received payload: {hash}"
                            .format(id=ID, hash=hash), route="logs")
                # Get workload from worker containers
                loads = get_container_loads()
                # Choose the worker container with lowest workload
                idx = loads.index(min(loads))
                # Get chosen containers name and port
                name = CONTAINERS[idx*2]
                port = CONTAINERS[idx*2+1]
                container = "{}, {}".format(name, port)
                # Store the payload to chosen container's workload
                CONTAINER_WORKLOADS[idx].append(hash)
                # Log the sending of payload to worker container for execution
                LOGS.append("Sent payload: {hash} for execution to port: {port}".format(hash=hash, port=port))
                send_request(name="database", port="3003", data="{id},Sent payload: {hash} for execution to port: {port}"
                            .format(id=ID, hash=hash, port=port), route="logs")
                # Send the payload to worker container for execution
                response = send_request(name=name, port=port, data=",".join([str(hash), payload]), route="payload")
                # If response was not OK, then worker container has crashed. Report it to database
                if response.text != "OK":
                    # Log worker container crash
                    LOGS.append("Worker has crashed")
                    send_request(name="database", port="3003", data="{id},Worker has crashed".format(id=ID), route="logs")
                    # Put the created payload to queue
                    QUEUE.append(",".join([str(hash), payload]))
                    # Remove crashed container information from container list
                    CONTAINERS.remove(name)
                    CONTAINERS.remove(port)
                    # Tell database worker container has crashed
                    send_request(name="database", port="3003", data="{},{}".format(PORT_NUMBER, port), route="down")

                    # Repeat the process for choosing the worker container with the lowest workload
                    loads = get_container_loads()
                    idx = loads.index(min(loads))
                    name = CONTAINERS[idx*2]
                    port = CONTAINERS[idx*2+1]
                    container = "{}, {}".format(name, port)
                    CONTAINER_WORKLOADS[idx].append(hash)
                    # Log the resending of payload to different worker container
                    LOGS.append("Sent payload: {hash} for execution to port: {port}".format(hash=hash, port=port))
                    send_request(name="database", port="3003", data="{id},Sent payload: {hash} for execution to port: {port}"
                                .format(id=ID, hash=hash, port=port), route="logs")
                    # Send the payload to worker container for execution
                    response = send_request(name=name, port=port, data=",".join([str(hash), payload]), route="payload")
            thread = threading.Thread(target=long_running_task, kwargs={})
            thread.start()
            return ("OK", 202)
        else:
            # Get hash and payload from POST request
            hash, payload = request.data.decode("utf-8").strip().split(",")
            # Create a thread for handling a payload from master container and executing it
            def long_running_task(**kwargs):
                # Log the receiving of payload from master container
                LOGS.append("Received payload: {hash}".format(hash=hash))
                send_request(name="database", port="3003", data="{id},Received payload: {hash}"
                            .format(id=ID, hash=hash), route="logs")
                # Put the payload to workload list
                WORKLOAD.append({"hash" : hash, "payload": payload})
                # Mutate the payload so it can executed in terminal
                code = payload.split("\n")
                runnable = ""
                for c in code:
                    if not (len(c) == 0 or c.isspace()):
                        runnable += c[4:]
                        runnable += ";"
                runnable = runnable[:-1]
                # Execute the payload in terminal with subprocess
                stdout = subprocess.check_output(["python", "-c", runnable]).decode("utf-8").strip()
                # Log the sending of results back to master container
                LOGS.append("Sent result: {hash} for leader to port: {port}".format(hash=hash, port=LEADER_PORT))
                send_request(name="database", port="3003", data="{id},Sent result: {hash} for leader to port: {port}"
                            .format(id=ID, hash=hash, port=LEADER_PORT), route="logs")
                # Send the result back to master container
                response = send_request(name=LEADER_NAME, port=LEADER_PORT, data=",".join([PORT_NUMBER, str(hash), stdout]), route="result")
                # If response was not OK, then master container has crashed. Report it to database
                if response.text != "OK":
                    # Log the crashing of master container
                    LOGS.append("Leader has crashed")
                    send_request(name="database", port="3003", data="{id},Leader has crashed".format(id=ID), route="logs")
                    # Put the created payload to queue,
                    # until information about new master container has been received
                    QUEUE.append(",".join([PORT_NUMBER, str(hash), stdout]))
                    # Tell database master container has crashed
                    send_request(name="database", port="3003", data="{},{}".format(PORT_NUMBER, LEADER_PORT), route="down")
                else:
                    # Remove the executed payload from the workload
                    WORKLOAD.remove({"hash" : hash, "payload": payload})
            thread = threading.Thread(target=long_running_task, kwargs={})
            thread.start()
            return ("OK", 202)

# Routine for telling the asking container current CPU and RAM usage
@app.route("/load" , methods=["GET", "POST"])
def load():
    # Tell interpreter where to find variables
    global IS_STOPPED
    global ID
    # Check if container is simulating a crash
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
    if request.method == "POST":
        # Get CPU and RAM usage
        cpu = psutil.cpu_percent(4)
        ram = psutil.virtual_memory()[2]
        # Log the CPU and RAM usage
        LOGS.append("The CPU usage is: {}".format(cpu))
        send_request(name="database", port="3003", data="{id},CPU usage: {cpu}".format(id=ID, cpu=cpu), route="logs")
        LOGS.append("RAM memory /%/ used: {}".format(ram))
        send_request(name="database", port="3003", data="{id},RAM usage: {ram}".format(id=ID, ram=ram), route="logs")
    return ("{},{}".format(cpu,ram), 200)

# Routine for receiving results from executed payload
@app.route("/result", methods=["GET", "POST"])
def result():
    # Tell interpreter where to find variables
    global IS_STOPPED
    global CONTAINER_WORKLOADS
    global CLIENT
    global CLIENT_PORT
    global ID
    global MISSING
    global PORT_NUMBER
    # Check if container is simulating a crash
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
    if request.method == "POST":
        # Get port number, hash, and result from POST request
        port, hash, result = request.data.decode("utf-8").strip().split(",")
        # Log the receiving of results
        LOGS.append("Received result: {hash}".format(hash=hash))
        send_request(name="database", port="3003", data="{id},Received result: {hash}".format(id=ID, hash=hash), route="logs")
        # In case there was a crash, check if the executed payload was flagged as missing
        # If not, remove it from worker container workload
        # Unless there was a crash and 
        # the new master container and the container which executed the payload are the same
        try:
            if MISSING.index(hash):
                MISSING.remove(hash)
        except ValueError:
            print(port, flush=True)
            print(PORT_NUMBER, flush=True)
            if port != PORT_NUMBER:
                CONTAINER_WORKLOADS[int(CONTAINERS.index(port.strip())/2)].remove(hash)
        # Log the sending of results to client container
        LOGS.append("Sent result: {hash} for client to port: {port}".format(hash=hash, port=CLIENT_PORT))
        send_request(name="database", port="3003", data="{id},Sent result: {hash} for client to port: {port}"
                    .format(id=ID, hash=hash, port=CLIENT_PORT), route="logs")
        # Send the result to client container
        send_request(name=CLIENT, port=CLIENT_PORT, data=",".join([str(hash), result]), route="result")
    return ("OK", 200)

# Routine for mimicking a crash
@app.route("/stop", methods=["GET"])
def stop():
    # Tell interpreter where to find variables
    global IS_STOPPED
    global PORT_NUMBER
    global NAME
    global ID
    # Flip the boolean flag
    IS_STOPPED = not IS_STOPPED
    if IS_STOPPED:
        # Log the simulated crash
        LOGS.append("CRASH :(")
        send_request(name="database", port="3003", data="{id},has crashed".format(id=ID), route="logs")
    else:
        # Log the simulated recovery
        LOGS.append("RECOVERED :)")
        send_request(name="database", port="3003", data="{id},has recovered".format(id=ID), route="logs")
        # Register the container again
        ID = register_container(PORT_NUMBER)
        # Get the master container information
        get_master_container()
        # Register with the master container
        send_request(name=LEADER_NAME, port=LEADER_PORT, data="{},{}".format(NAME, PORT_NUMBER), route="register")
    return "{}".format(IS_STOPPED)

# Routine for receiving information on new master container and 
# executing a master container routine if this container was chosen
@app.route("/leader", methods=["POST"])
def leader():
    # Tell interpreter where to find variables
    global IS_STOPPED
    # Check if container is simulating a crash
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
        # Get new master container name and port number from POST request
        name, port = request.data.decode("utf-8").strip().split(",")
        # If the port number matches container's own, it was chosen as the new master container
        if int(PORT_NUMBER) == int(port):
            # Store master container status
            IS_LEADER = True
            # Get client information
            get_client()
            # Get payloads waiting for results from client
            get_pending()
            # Get running worker containers
            get_containers()
            # Clear the possible results waiting from the queue and send them straight to client
            # Check if they are flagged as missing
            for data in QUEUE:
                _, hash, result = data.split(",")
                try:
                    if MISSING.index(str(hash)):
                        MISSING.remove(str(hash))
                except ValueError:
                    pass
                # Log the sending of results to client
                LOGS.append("Sent result: {hash} for client to port: {port}".format(hash=hash, port=CLIENT_PORT)
                            .format(id=ID, hash=hash, port=CLIENT_PORT))
                send_request(name="database", port="3003", data="{id},Sent result: {hash} for client to port: {port}"
                            .format(id=ID, hash=hash, port=CLIENT_PORT), route="logs")
                # Send the result to client
                send_request(name=CLIENT, port=CLIENT_PORT, data="{},{}".format(hash,result), route="result")
            # If there are still missing payloads, ask worker containers if they have them in workload
            if len(MISSING) > 0:
                find_missing()
            # If there are still missing payloads, ask client container to send them again
            if len(MISSING) > 0:
                get_missing()
        # Store master container information
        LEADER_NAME = name
        LEADER_PORT = port
        # Clear the possible results waiting from the queue and send them to new master container
        for data in QUEUE:
            _, hash, result = data.split(",")
            # Log the sending of results to master container
            LOGS.append("Sent result: {hash} for leader to port: {port}".format(hash=hash, port=LEADER_PORT))
            send_request(name="database", port="3003", data="{id},Sent result: {hash} for leader to port: {port}"
                        .format(id=ID, hash=hash, port=LEADER_PORT), route="logs")
            # Send the result to master container
            send_request(name=LEADER_NAME, port=LEADER_PORT, data=",".join([PORT_NUMBER, str(hash), result]), route="result")
            # Remove the payload from workload
            for work in WORKLOAD:
                if work["hash"] == hash:
                    WORKLOAD.remove(work)
    return ("OK", 200)

# Routine for registering the requesting container
@app.route("/register", methods=["POST"])
def register():
    # Tell interpreter where to find variables
    global IS_STOPPED
    global CONTAINERS
    global CONTAINER_WORKLOADS
    # Check if container is simulating a crash
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
    if request.method == "POST":
        # Get the name and port number from POST request
        name, port = request.data.decode("utf-8").strip().split(",")
        # Store the registered container to container list
        CONTAINERS.append(name)
        CONTAINERS.append(port)
        # Establish a workload for the registered container
        CONTAINER_WORKLOADS.append([])
    return ("OK", 200)

# Routine for telling the asking container what payloads are in workload
@app.route("/pending", methods=["POST"])
def pending():
    # Tell interpreter where to find variables
    global WORKLOAD
    # Check if container is simulating a crash
    if IS_STOPPED:
        return ("I am simulating a crash, please do not bother me", 418)
    if request.method == "POST":
        response = ""
        # Get hash from payloads in execution
        for work in WORKLOAD:
            response += "{},".format(work["hash"])
        # Remove the last comma
        if response != "":
            response = response[:-1]
    return (response, 200)

# Ask database for worker containers
@app.before_first_request
def get_containers():
    # Tell interpreter where to find variables
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
        containers = requests.post(url, data="", headers=headers).text.split(",")
        containers.pop()
        # Store the container informations
        CONTAINERS = containers
        CONTAINER_WORKLOADS = []
        # Establish a workload list for containers
        for i in range(0, len(CONTAINERS), 2):
            CONTAINER_WORKLOADS.append([])

# Ask databse for client container
@app.before_first_request
def get_client():
    # Tell interpreter where to find variables
    global CLIENT
    global CLIENT_PORT
    if IS_LEADER:
        # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
        url = "http://database:3003/client"
        # Basic headers
        headers = {"Content-type": "text/html; charset=UTF-8"}
        # Store client container information
        CLIENT, CLIENT_PORT = requests.post(url, data="", headers=headers).text.split(",")

# Ask containers for their available CPU and memory
def get_container_loads():
    # Tell interpreter where to find variables
    global CONTAINERS
    global CONTAINER_WORKLOADS
    global ID
    container_load = []
    loads = []
    delete = -1
    # Loop through containers asking for CPU and RAM usage
    for i in range(0, len(CONTAINERS), 2):
        response = send_request(name=CONTAINERS[i], port=CONTAINERS[i+1], data="", route="load")
        # Check if worker has crashed, if so, tell the database and mark it for removal
        if response.text == "I am simulating a crash, please do not bother me":
            delete = i
            # Log the worker container crash
            LOGS.append("Worker has crashed")
            send_request(name="database", port="3003", data="{id},Worker has crashed".format(id=ID), route="logs")
            # Inform database worker container has crashed
            send_request(name="database", port="3003", data="{},{}".format(PORT_NUMBER, CONTAINERS[i+1]), route="down")
        else:
            cpu, ram = response.text.split(",")
            # Count the workload by summing CPU and RAM usage with current payload queue (multiplied by 5)
            loads.append(float(cpu) + float(ram) + 5 * len(CONTAINER_WORKLOADS[int(i / 2)]))
    # Delete the containers marked for deletion
    if delete != -1:
        del CONTAINER_WORKLOADS[(int(CONTAINERS.index(CONTAINERS[i+1])/2))]
        del CONTAINERS[i]
        # index moves down dummie
        del CONTAINERS[i]
    return loads

# General method for sending POST requests
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

# Method for asking client container for payloads waiting for results
def get_pending():
    # Tell interpreter where to find variables
    global CLIENT
    global CLIENT_PORT
    global MISSING
    # Ask client for payloads waiting for results
    response = send_request(name=CLIENT, port=CLIENT_PORT, data="", route="pending")
    # Get hashes from the response
    pending_hashes = response.text.split(",")
    # Log the received payload hashes
    LOGS.append("Got pending hashes from client")
    send_request(name="database", port="3003", data="{id},Got pending hashes from client"
                .format(id=ID), route="logs")
    # Mark the payload hashes as missing
    MISSING.extend(pending_hashes)

# Method for asking worker containers for missing payloads
def find_missing():
    # Tell interpreter where to find variables
    global MISSING
    global CONTAINERS
    global CONTAINER_WORKLOADS
    # Loop through worker containers and ask what payloads they have in execution
    for i in range(0, len(CONTAINERS), 2):
        # Ask worker for payloads in execution
        response = send_request(name=CONTAINERS[i], port=CONTAINERS[i+1], data="", route="pending")
        # Get hashes from the response
        pending_hashes = response.text.split(",")
        # Log the received payload hashes
        LOGS.append("Ask for pending hashes from workers")
        send_request(name="database", port="3003", data="{id},Ask for pending hashes from workers"
                    .format(id=ID), route="logs")
        # Check if the payload hashes were flagged as missing and remove the flag and add the has to workload
        for hash in pending_hashes:
            try:
                if MISSING.index(str(hash)):
                    MISSING.remove(str(hash))
                    CONTAINER_WORKLOADS[int(i / 2)].append(hash)
            except ValueError:
                pass

# Method for asking client to resend payloads that are waiting for results
def get_missing():
    # Tell interpreter where to find variables
    global MISSING
    global CLIENT
    global CLIENT_PORT
    global QUEUE
    global NAME
    global PORT_NUMBER
    # Ask client for payloads waiting for results
    response = send_request(name=CLIENT, port=CLIENT_PORT, data="", route="missing")
    # Get hashes and payloads from the response
    pending_payloads = response.text.split(",")
    # Log the receiving of payloads
    LOGS.append("Ask for missing payloads from client")
    send_request(name="database", port="3003", data="{id},Ask for missing payloads from client"
                .format(id=ID), route="logs")
    # Send the payloads to itself so they get executed
    if len(pending_payloads) > 1:
        for i in range(0, len(pending_payloads), 2):
            data = ",".join([str(pending_payloads[i]), pending_payloads[i+1]])
            response = send_request(name=NAME, port=PORT_NUMBER, data=data, route="payload")
