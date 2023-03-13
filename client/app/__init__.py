#!/usr/bin/env python3
from flask import Flask
# config = file /client/config.py, Config = class Config in /client/config.py
from config import Config
import requests

# Initialise Flask class
app = Flask(__name__)
# Apply config file
app.config.from_object(Config)

port_number = -1
name = ""
# Read port number and name from text file, created in Dockerfile
with open("port.txt") as f:
    #print(f.readline(), flush=True)
    name, port_number = f.readline().split(",")

# Registers the client container with the database containers
def register_container(port_number):
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://database:3003/register"
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with container information to database container
    requests.post(url, data="{},{}".format(name, port_number), headers=headers)

# Register container to database
response = register_container(port_number=port_number)

# Import at the bottom to prevent circular imports
from app import routes
