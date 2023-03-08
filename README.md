# Container Load Balancing (CLB)
## _DS2023 project_

Joku lyhyt selitys projektista vois olla vaikka tässä :D.
Ehkä tekijätkin :D.

## Requirements
* Python 3.7+
* pip
* Docker
* Docker Compose

## First Start Guide for \*nix

We strongly recommend using a Python virtual environment. So after pulling the repository and changing into the main directory, create a new virtual environment with: (if you don't have venv-module installed, please install it with pip)
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
docker-compose up
```

## Quick Start Guide for \*nix (for every use after First Start Guide)

In the main directory:
Activate the virtual environment:
```
source venv/bin/activate
```

Make sure your packages are up to date:
```
pip3 install -r requirements.txt
```

Start CLB:
```
docker-compose up
```

## Dev Guide for \*nix

Great tutorial for [Flask](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)


Initialize migration repository, if app.db does not exist (inside /database/ directory):
```
flask init db
```

Migrate database, if made changes to /app/models.py (inside /database/ directory):
```
flask db migrate -m "your message here"
```
```
flask db upgrade
```

If your changes to /app/models.py fucked everything up (inside /database/ directory):
Revert your changes in /app/models.py
```
flask db downgrade
```
Remove migration script from /migrations/versions/, you should be able to recognize the correct script by filename which contains your message.
