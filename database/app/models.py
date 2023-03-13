#!/usr/bin/env python3
# Import variable db from __init__.py
from app import db
from datetime import datetime

# Class for containers
class Container(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    port = db.Column(db.Integer, index=True, unique=True)
    # Either "client" or "server"
    role = db.Column(db.String(255), index=True)
    # Name of the container as typed in docker-compose.yml
    name = db.Column(db.String(255), index=True)

    def __repr__(self):
        return "<Container {}, port {}>".format(self.id, self.port)

# Class for container logs
class Logs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, db.ForeignKey("container.id"))
    message = db.Column(db.String(255), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return "<Log {}, Container {}: {}>".format(self.id, self.container_id, self.message)
