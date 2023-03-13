#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app

# Register callbacks with URLs
@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"
