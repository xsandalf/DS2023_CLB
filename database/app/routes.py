#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app, db
from app.models import Container, Logs
from flask import render_template, request

# Register callbacks with URLs
@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"

@app.route("/client_logs", methods=["GET", "POST"])
def client_logs():
    if request.method == "POST":
        print(request.data, flush=True)
        print("TOIMII VITTU JEE", flush=True)
    return "Hello, World!"

@app.route("/register", methods=["GET", "POST"])
def register_container():
    if request.method == "POST":
        if request.data != "":
            print(request.data, flush=True)
            print("läpimätä", flush=True)
            port_number = request.data
            with app.app_context():
                container = Container.query.filter_by(port=port_number).first()
                print(container, flush=True)
    return "Hello, World!"
