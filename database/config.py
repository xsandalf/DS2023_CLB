#!/usr/bin/env python3
import os
# Gets the absulute file path for current directory (/database/)
basedir = os.path.abspath(os.path.dirname(__file__))

# Class for Flask configs
class Config(object):
    # Secret key for encryption and stuff, looks for the environment variable first,
    # if that is not available, uses the hard coded values
    SECRET_KEY = os.environ.get("SECRET_KEY") or "hacker_duck_exe"
    # File path for database, looks for the the environment variable first,
    # if that is not available, uses the hard coded file path
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///"" + os.path.join(basedir, "app.db")
    # This flag would signal the application everytime a change is made
    # Not needed in our case
    SQLALCHEMY_TRACK_MODIFICATIONS = False
