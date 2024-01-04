#!/bin/bash

# Give permission for everything in the flask-app directory
sudo chmod -R 777 /home/ec2-user/Flask-App

# Navigate into our working directory where we have all our GitHub files
cd /home/ec2-user/Flask-App

# Activate virtual environment
#source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start our Flask app in the background
# gunicorn -b 0.0.0.0:5000 app:app > app.out.log 2> app.err.log < /dev/null &

python -m flask run --host=0.0.0.0 --port=5000 > app.out.log 2> app.err.log < /dev/null &


#### try with this 
#python3 app.py
