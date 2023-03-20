#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app, db
from app.models import Container, Logs
from flask import render_template, request
import requests
import threading

# Use global variables as local cache
LEADER = ""

# Register callbacks with URLs
# Main page for database, unused
@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"

# Routine for receiving logs from containers
@app.route("/logs", methods=["GET", "POST"])
def client_logs():
    if request.method == "POST":
        print(request.data, flush=True)
        # Get sending id and log from the POST request
        id, log = request.data.decode("utf-8").strip().split(",")
        # Store the log to database
        with app.app_context():
            logs = Logs(container_id=id, message=log)
            db.session.add(logs)
            db.session.commit()
    return ("OK", 200)

# Receive information data from containers wishing to register
@app.route("/register", methods=["GET", "POST"])
def register_container():
    if request.method == "POST":
        if request.data != "":
            # Extract container name and port number from POST-request
            name, port_number = request.data.decode("utf-8").strip().split(",")
            # See if the container is client or server
            role = "client" if name == "client" else "server"
            # Store the container to database
            with app.app_context():
                container = Container(name=name, port=int(port_number), role=role)
                db.session.add(container)
                db.session.commit()
                container = db.session.query(Container).filter_by(port=int(port_number)).first()
    return (str(container.id), 200)

# Tell requesting container who is the master container
@app.route("/leader", methods=["GET", "POST"])
def leader():
    if request.method == "POST":
        # Tell interpreter where to find variables
        global LEADER
        if LEADER == "":
            container = ""
            # Get leader from database
            with app.app_context():
                container = db.session.query(Container).filter_by(role="server").first()
            LEADER = ",".join((str(container.name), str(container.port)))
        return (LEADER, 200)

# Tell requesting container who are the worker containers
@app.route("/workers", methods=["GET", "POST"])
def workers():
    if request.method == "POST":
        # Tell interpreter where to find variables
        global LEADER
        container = ""
        # Get worker containers from database
        with app.app_context():
            port = LEADER.split(",")[1]
            container = db.session.query(Container).filter((Container.role == "server") & (Container.port != port)).all()
            containers = ""
            for c in container:
                containers += "{},{},".format(c.name, str(c.port))
        return (containers, 200)

# Tell requesting container who is the client container
@app.route("/client", methods=["GET", "POST"])
def client():
    if request.method == "POST":
        # Get client container from database
        with app.app_context():
            client = db.session.query(Container).filter(Container.role == "client").first()
        return ("{},{}".format(client.name, str(client.port)), 200)

# Routine for receiving information about a crashed container and choosing a new master container if needed
@app.route("/down", methods=["GET", "POST"])
def down():
    if request.method == "POST":
        # Get the port numbers of sending container and crashed container from POST request
        port_number, down_port = request.data.decode("utf-8").strip().split(",")
        # Containers might get port numbers wrong due to race condition, ignore false alarms
        if port_number != down_port:
            # Create a thread for handling crashed container and possible master container change
            def long_running_task(**kwargs):
                with app.app_context():
                    # Tell interpreter where to find variables
                    global LEADER
                    # Delete the crashed container from database
                    db.session.query(Container).filter(Container.port == down_port).delete()
                    db.session.commit()
                    # Check if the crashed container was the master container
                    # if so, choose new master container by choosing a server container with lowest id
                    if down_port == LEADER.split(",")[1]:
                        # Get new master container from database
                        new_leader = db.session.query(Container).filter_by(role="server").first()
                        LEADER = ",".join((str(new_leader.name), str(new_leader.port)))
                        servers = db.session.query(Container).filter_by(role="server").all()
                        # Inform all the server containers who is the new master container
                        for c in servers:
                            send_request(name=c.name, port=c.port, data=LEADER, route="leader")
                        # Inform client who is the new master container
                        client = db.session.query(Container).filter_by(role="client").first()
                        send_request(name=client.name, port=client.port, data=LEADER, route="leader")
            thread = threading.Thread(target=long_running_task, kwargs={})
            thread.start()
        return ("OK", 202)

# Register callbacks with URLs
# Page for viewing database logs
@app.route("/logging", methods=["GET", "POST"])
def logging():
    # Get all the logs from database
    with app.app_context():
        logs = db.session.query(Logs).all()
    # Return logs.html with additional paremeter
    return render_template("logs.html", logs=logs)

# Empties the database on every build
@app.before_first_request
def clear_database():
    with app.app_context():
        db.session.query(Container).delete()
        db.session.query(Logs).delete()
        db.session.commit()

# General method for sending POST requests
def send_request(name, port, data, route):
    # URL needs include protocol
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://{}:{}/{}".format(name, port, route)
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with log data to database container
    return requests.post(url, data=data, headers=headers)
