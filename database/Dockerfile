# Official Docker image running Debian with minimal packages needed for Python 3.11
FROM python:3.11-slim-buster

# Set work directory
WORKDIR /app

# Create python venv
ENV VIRTUAL_ENV=/opt/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements
# Use common requirements.txt file for all containers, separate files if problems arise
# Problems counter: 2
# First problem: Cannot find requirements.txt because it's in parent directory
# Solution: Add context to /DS2023_CLB/docker-compose.yml, see that file for possible issues.
COPY requirements.txt requirements.txt

# Install pip dependencies
RUN pip3 install -r requirements.txt

# Copy all from current directory (client/)
# Second problem: Due to context flag in /DS2023_CLB/docker-compose.yml,
# this copies everything in /DS2023_CLB directory
# Solution: Change ./ to ./database/ to specify the correct directory
COPY ./database/ ./

# Set Flask env
ENV FLASK_APP=database.py

# TODO: combine all the commands into a entrypoint.sh script and run that instead
# Store port number in a file, so it can be accessed programmatically
RUN echo "database,3003" > port.txt

# Run flask
# THIS HAS TO BE LAST CMD IN THE FILE
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=3003"]
