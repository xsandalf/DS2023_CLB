#!/usr/bin/env python3
from flask import Flask
# config = file /server/config.py, Config = class Config in /server/config.py
from config import Config

# Initialise Flask class
app = Flask(__name__)
# Apply config file
app.config.from_object(Config)

port_number = -1
# Read port number from text file, created in Dockerfile
with open("port.txt") as f:
    #print(f.readline(), flush=True)
    port_number = int(f.readline())

# Import at the bottom to prevent circular imports
from app import routes
