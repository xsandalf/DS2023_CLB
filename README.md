# Container Load Balancing (CLB)
## _DS2023 project_

## Authors
* Saku Salo
* Roosa Risto
* Riina Annunen

## Introduction

This project was created for the Distributed Systems 2023 course at University of Oulu. This repository shows a container load balancer architecture, where one container is assigned as the master container which distributes tasks to worker containers based on their current workload and resource availability. Tasks are simulated with python scripts that contain a processor sleep command, this is used to mimic a CPU intensive task that will take 10 - 60 seconds to run. Architecture contains several recovery methods in case of container crashes during execution, which can be examined with methods included in the repository.

## Acknowledgements
Many thanks to Miguel Grinberg for providing an excellent tutorial for [Flask](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world).

## Requirements
* Python 3.7+
* pip
* Docker
* Docker Compose

## Start Guide for \*nix

We strongly recommend using a Python virtual environment. So after cloning the repository and changing into the main directory (DS2023_CLB), create a new virtual environment with: (if you don't have virtualenv-module installed, please install it with pip)
```
python3 -m venv venv/
```
It's important to name the virtual environment directory venv/ as that is included in the .gitignore file. Please do not push your venv to our beautiful repository :).

You can now activate the virtual environment from the main directory:
```
source venv/bin/activate
```

Now install the required packages with pip:
```
pip3 install -r requirements.txt
```

Start CLB:
```
docker-compose build && docker-compose up
```

## Start Guide for Windows

We strongly recommend using a Python virtual environment. So after pulling the repository and changing into the main directory (DS2023_CLB), create a new virtual environment with: (if you don't have virtualenv-module installed, please install it with pip)
```
python -m venv venv\
```
It's important to name the virtual environment directory venv/ as that is included in the .gitignore file. Please do not push your venv to our beautiful repository :).

You can now activate the virtual environment from the main directory:
```
venv\Scripts\activate
```

Now install the required packages with pip:
```
pip install -r requirements.txt
```

Start CLB:
```
docker-compose up
```

## Containers and Addresses

This project consists of 6 containers, 1 client, 1 database, 1 master container and 3 worker containers. Their IP addresses and ports with explanations are shown below. Note that if you simulate Master Container crash, another container will be chosen as Master Container and you will have to find the new Master Container Port Number from the logs yourself.

### Client
* 127.0.0.1:3001/ - Main page for creating and sending payloads
* 127.0.0.1:3001/logging - Client Container logs

### Database
* 127.0.0.1:3003/logging - Shows all the logs sent to Database

### Servers
* 127.0.0.1:3002/logging - Master Container logs
* 127.0.0.1:3002/stop - Simulate Master Container crash
* 127.0.0.1:3004/logging - Worker Container logs
* 127.0.0.1:3004/stop - Worker Container crash
* 127.0.0.1:3005/logging - Worker Container logs
* 127.0.0.1:3005/stop - Worker Container crash
* 127.0.0.1:3006/logging - Worker Container logs
* 127.0.0.1:3006/stop - Worker Container crash

## User Guide

### Getting Familiar
First you should get familiar with the project by navigating to Client's main page and creating and sending a couple payloads, and waiting for results. Unfortunately, there is no auto update feature, so you have to manually refresh the page to see the results once they have arrived, or you could try following the payload with /logging pages :).

### How to Read Logs 
Here are few example of logs from /logging pages with explanations.

```
Created payload: -5770691082818497906
```
Created payload tells us what has happened i.e. container has created a new payload. -5770691082818497906 is the hash created from payload. Every log that contains the same hash number is related to the same payload.


```
Sent payload: -5770691082818497906 for execution to port: 3002
```
Container has sent the payload (hash = -5770691082818497906) to be executed. Port: 3002 tells us it was sent to the container that listens to port 3002. From above we can tell that the container in question is the default master controller.


```
Received payload: -5770691082818497906
Sent payload: -5770691082818497906 for execution to port: 3004
```
These tell us that the container has received the payload (hash = -5770691082818497906) and has passed it forward to a container that listens to port 3004. From above we can tell that the container in question is one of the worker controllers.


```
The CPU usage is: 0.2
RAM memory /%/ used: 9.8
```
These two tell us the available resources (CPU and RAM) the worker container had. The lack of received payload after these, tells us that this container was not chosen to run the payload.


```
Sent result: -5770691082818497906 for leader to port: 3002
```
Container has run the payload (hash = -5770691082818497906) and has now sent the result back to master container (port number = 3002)


```
Received result: -5770691082818497906
Sent result: -5770691082818497906 for client to port: 3001
```
Master container has received the result for the payload (hash = -5770691082818497906) from a worker container and has passed it forward to client.


```
<Log 3, Container 1: Is master container>
```
Database container uses a different format for logging. Log 3 is the 3rd log database container has received from other containers. Container 1 is the id of the container that sent the log. Is master container is the log message, which is the same that can be found from the individual container's /logging page.


Once you are familiar with the project and logs, you can read them straight from the Docker Compose terminal (Terminal window you used the docker-compose up -commmand). They look like this.
```
b'1,Sent result: -5770691082818497906 for client to port: 3001'
```
Similar to database logs, 1 is the container ID and after that is the log message, which is the same that can be found from the individual container's /logging page.

### How to Simulate Container Crashes

As causing real crashes is sometimes hard (and sometimes extremely easy :D), the project has the option to simulate a container crash with /stop pages. You can soft stop the container by visiting its /stop page, the page will print the container's current status for you to see. True means container is stopped, and False means container is running.

You can start testing with these suggested crash recoveries to see how the system reacts. We don't suggest stopping more than one container at a time.
* Stop the Master Container then create and send the payload from Client
* Stop a Worker Container then create and send the payload from Client
* Create and send the payload from Client, wait until Master Container has sent it forward to a Worker Container, then stop the Master Container

No Active Recovery Implemented or Known Issues in Simulated Crashes:
* Stopping Master Container after it receives the payload from Client but before it has passed it on to a Worker Container
* Stopping a Worker Container after it has received the payload from Master Container but before it has sent the result back
