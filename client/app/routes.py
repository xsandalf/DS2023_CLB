#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app, ID, PORT_NUMBER
from flask import render_template, request
from random import randint
import requests

# Bad coding practice, "dirty hack" :D
PAYLOAD = ""
PAYLOADS = []
LOGS = []
LEADER_NAME = ""
LEADER_PORT = -1
QUEUE = []

# Register callbacks with URLs
@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    # Payload template to simulate workload (read: python files) that client would input
    # time.sleep emulates a computing heavy file that requires random_int seconds to execute
    # returns a sum of two integers to signify execution has ended
    payload_template = """
    import time\n
    \n
    time.sleep(20)\n
    print(2 + 2)
    """#.format(random_int=randint(10,60), random_int2=randint(1,10), random_int3=randint(1,10))
    #payload_template = """
    #import time\n
    #\n
    #time.sleep({random_int})\n
    #print({random_int2} + {random_int3})
    #""".format(random_int=randint(10,60), random_int2=randint(1,10), random_int3=randint(1,10))

    # Tell interpreter where to find variables
    global PAYLOAD
    global PAYLOADS
    global LOGS
    global QUEUE

    # POST-request means a button was pressed, figure out which one and either generate a payload or
    # send the payload forward to be executed in another container
    if request.method == "POST":
        if request.form.get("generate_payload") == "Generate Payload":
            # Get new payload
            PAYLOAD = payload_template
            # Re-render page and show the payload
            return render_template("index.html", generated_payload=PAYLOAD, payloads=PAYLOADS)
        elif request.form.get("send_payload") == "Send Payload":
            # Ignore clicks if payload isn't created
            if len(PAYLOAD) > 0:
                payload_hash = hash(PAYLOAD)
                # Store payload, its hash, and current state to a dictionary
                PAYLOADS.append({"hash" : str(payload_hash), "payload" : PAYLOAD, "result" : "executing"})
                # Log payload creation and sending
                LOGS.append("Created payload: {hash}".format(hash=payload_hash))
                #send_logging_post_req("{id},Created payload: {hash}".format(id=ID, hash=payload_hash))
                send_request(name="database", port="3003", data="{id},Created payload: {hash}"
                            .format(id=ID, hash=payload_hash), route="logs")
                LOGS.append("Sent payload: {hash} for execution to port: {port}".format(hash=payload_hash, port=LEADER_PORT))
                #send_logging_post_req("{id},Sent payload: {hash} for execution to port: {port}"
                #                      .format(id=ID, hash=payload_hash, port=LEADER_PORT))
                send_request(name="database", port="3003", data="{id},Sent payload: {hash} for execution to port: {port}"
                            .format(id=ID, hash=payload_hash, port=LEADER_PORT), route="logs")
                # Send payload to master container
                # LOG THE RETURN
                response = send_request(name=LEADER_NAME, port=LEADER_PORT,
                                        data=",".join([str(payload_hash), PAYLOAD]), route="payload")
                if response.text != "OK":
                    LOGS.append("Leader has crashed")
                    send_request(name="database", port="3003", data="{id},Leader has crashed".format(id=ID), route="logs")
                    QUEUE.append(",".join([str(payload_hash), PAYLOAD]))
                    send_request(name="database", port="3003", data="{},{}".format(PORT_NUMBER, LEADER_PORT), route="down")
                # Empty payload so user cannot flood the system with the same payload
                PAYLOAD = ""
                # Re-render page and show the payload in the execution table
                return render_template("index.html", generated_payload=PAYLOAD, payloads=PAYLOADS)
    # Reset variables on GET-requests
    else:
        PAYLOAD = ""
        PAYLOADS = []
        LOGS = []

    # Return index.html with additional parameters
    return render_template("index.html", generated_payload=PAYLOAD, payloads=PAYLOADS)

# Register callbacks with URLs
@app.route("/logging", methods=["GET", "POST"])
def logging():
    # Tell interpreter where to find logs
    global LOGS
    # Return logs.html with additional paremeter
    return render_template("logs.html", logs=LOGS)

@app.route("/result", methods=["GET", "POST"])
def result():
    global ID
    global PAYLOADS
    if request.method == "POST":
        hash, result = request.data.decode("utf-8").strip().split(",")
        LOGS.append("Received result: {hash}".format(hash=hash))
        #send_logging_post_req("{id},Received result: {hash}".format(id=ID, hash=hash))
        send_request(name="database", port="3003", data="{id},Received result: {hash}".format(id=ID, hash=hash), route="logs")
        print(result, flush=True)
        for payload in PAYLOADS:
            if payload["hash"] == hash:
                payload["result"] = result
    return ("OK", 200)

@app.route("/leader", methods=["POST"])
def leader():
    global LEADER_NAME
    global LEADER_PORT
    if request.method == "POST":
        LEADER_NAME, LEADER_PORT = request.data.decode("utf-8").strip().split(",")
        for data in QUEUE:
            hash = data.split(",")[0]
            LOGS.append("Sent payload: {hash} for execution to port: {port}".format(hash=hash, port=LEADER_PORT))
            send_request(name="database", port="3003", data="{id},Sent payload: {hash} for execution to port: {port}"
                        .format(id=ID, hash=hash, port=LEADER_PORT), route="logs")
            response = send_request(name=LEADER_NAME, port=LEADER_PORT, data=data, route="payload")
    return ("OK", 200)

@app.route("/pending", methods=["POST"])
def pending():
    global PAYLOADS
    if request.method == "POST":
        response = ""
        for payload in PAYLOADS:
            if payload["result"] == "executing":
                response += "{},".format(payload["hash"])
        if response != "":
            response = response[:-1]
    return (response, 200)

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

# Ask database for master containers information
@app.before_first_request
def get_master_container():
    global LEADER_NAME
    global LEADER_PORT
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://database:3003/leader"
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with container information to database container
    LEADER_NAME, LEADER_PORT = requests.post(url, data="", headers=headers).text.split(",")
