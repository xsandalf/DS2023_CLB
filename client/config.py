#!/usr/bin/env python3
import os

# Class for Flask configs
class Config(object):
    # Secret key for encryption and stuff, looks for the environment variable first,
    # if that is not available, uses the hard coded values
    SECRET_KEY = os.environ.get("SECRET_KEY") or "crypto_duck_security"
