#!/bin/bash

# Stopping existing Flask servers
echo "Stopping any existing Flask servers"
pkill gunicorn
