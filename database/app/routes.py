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
            #print(request.data, flush=True)
            print("läpimätä", flush=True)
            # Extract container name and port number from POST-request
            name, port_number = request.data.decode("utf-8").strip().split(",")
            print(name)
            print(port_number)
            role = "client" if name == "client" else "server"
            print(role)
            with app.app_context():
                #container = Container.query.filter_by(port=port_number).first()
                container = Container(name=name, port=port_number, role=role)
                db.session.add(container)
                db.session.commit()
    return "OK"
