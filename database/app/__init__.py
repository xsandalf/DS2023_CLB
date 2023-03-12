#!/usr/bin/env python3
from flask import Flask
# config = file /database/config.py, Config = class Config in /database/config.py
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialise Flask class
app = Flask(__name__)
# Apply config file
app.config.from_object(Config)
# Database instance
db = SQLAlchemy(app)
# Database migration instances
migrate = Migrate(app, db, render_as_batch=True)

# Import at the bottom to prevent circular imports
from app import routes, models