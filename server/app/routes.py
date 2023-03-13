#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app, PORT_NUMBER, ID, LEADER_PORT, LEADER_NAME, IS_LEADER
import requests

# Bad coding practice, "dirty hack" :D
PAYLOAD = ""
PAYLOADS = []
LOGS = []

# Register callbacks with URLs
@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"

@app.route("/payload")
def payload():
    if IS_LEADER:
        pass

# Ask database for worker containers
@app.before_first_request
def get_containers():
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
        print(containers, flush=True)#.text.split(",")
    print(LEADER_NAME, flush=True)
    print(LEADER_PORT, flush=True)

def send_logging_post_req(data):
    # URL for database, check port number from /DS2023_CLB/docker-compose.yml for changes
    # URL needs include protocol
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://database:3003/logs"
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with log data to database container
    requests.post(url, data=data, headers=headers)
