#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app, db
from app.models import Container, Logs
from flask import render_template, request

LEADER = ""

# Register callbacks with URLs
@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"

@app.route("/logs", methods=["GET", "POST"])
def client_logs():
    if request.method == "POST":
        print(request.data, flush=True)
        id, log = request.data.decode("utf-8").strip().split(",")
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
            role = "client" if name == "client" else "server"
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
        global LEADER
        if LEADER == "":
            container = ""
            with app.app_context():
                container = db.session.query(Container).filter_by(role="server").first()
            LEADER = ",".join((str(container.name), str(container.port)))
        return (LEADER, 200)

# Tell requesting container who are the worker containers
@app.route("/workers", methods=["GET", "POST"])
def workers():
    if request.method == "POST":
        global LEADER
        container = ""
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
        with app.app_context():
            client = db.session.query(Container).filter(Container.role == "client").first()
        return ("{},{}".format(client.name, str(client.port)), 200)

# Empties the database on every build
@app.before_first_request
def clear_database():
    with app.app_context():
        db.session.query(Container).delete()
        db.session.query(Logs).delete()
        db.session.commit()
