#!/usr/bin/env python3
from flask import Flask
# config = file /server/config.py, Config = class Config in /server/config.py
from config import Config

# Initialise Flask class
app = Flask(__name__)
# Apply config file
app.config.from_object(Config)

# Import at the bottom to prevent circular imports
from app import routes
