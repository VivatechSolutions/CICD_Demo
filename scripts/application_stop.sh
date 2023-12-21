

# Stopping existing Flask servers
#echo "Stopping any existing Flask servers"
#pkill gunicorn

#!/bin/bash

sudo yum erase codedeploy-agent
cd /opt
sudo rm -r codedeploy-agent/
sudo rm -r Flask-App/
sudo ./install auto

# Stop the Flask application

echo "Stopping any existing Flask servers"

# Find the Flask server process and kill it
pkill -f "python -m flask run"

# Optionally, you may want to add a delay before checking if the process is still running
sleep 2

# Check if the process is still running and force kill if necessary
pkill -9 -f "python -m flask run"

#########################################################


