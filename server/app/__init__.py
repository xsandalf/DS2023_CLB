#!/usr/bin/env python3
from flask import Flask
# config = file /server/config.py, Config = class Config in /server/config.py
from config import Config
import requests

# Initialise Flask class
app = Flask(__name__)
# Apply config file
app.config.from_object(Config)

PORT_NUMBER = -1
NAME = ""
ID = -1
LEADER_NAME = ""
LEADER_PORT = -1
IS_LEADER = False

# Read port number and name from text file, created in Dockerfile
with open("port.txt") as f:
    #print(f.readline(), flush=True)
    NAME, PORT_NUMBER = f.readline().split(",")

# Registers the client container with the database container
def register_container(port_number):
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://database:3003/register"
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with container information to database container
    ID = int(requests.post(url, data="{},{}".format(NAME, PORT_NUMBER), headers=headers).text)
    print(ID, flush=True)

def get_master_container():
    global IS_LEADER
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://database:3003/leader"
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with container information to database container
    LEADER_NAME, LEADER_PORT = requests.post(url, data="", headers=headers).text.split(",")
    print(LEADER_NAME, flush=True)
    print(LEADER_PORT, flush=True)
    if NAME == LEADER_NAME and PORT_NUMBER == LEADER_PORT:
        IS_LEADER = True
    print(IS_LEADER, flush=True)

# Register container to database
register_container(port_number=PORT_NUMBER)

# Ask database for master containers information
get_master_container()

# Import at the bottom to prevent circular imports
from app import routes
