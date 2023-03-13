#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app, PORT_NUMBER, ID, LEADER_PORT, LEADER_NAME, IS_LEADER

# Register callbacks with URLs
@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"

def send_logging_post_req(data):
    # URL for database, check port number from /DS2023_CLB/docker-compose.yml for changes
    # URL needs include protocol
    # docker-compose provides a DNS so we can use database, instead of 127.0.0.1
    url = "http://database:3003/logs"
    # Basic headers
    headers = {"Content-type": "text/html; charset=UTF-8"}
    # Send the POST-request with log data to database container
    requests.post(url, data=data, headers=headers)
