#!/bin/bash

# Stop Gunicorn
echo "Stopping Gunicorn server..."
sudo pkill -f gunicorn

# Wait for Gunicorn to stop (adjust the sleep duration as needed)
sleep 5

# Verify that Gunicorn has stopped
if pgrep -f gunicorn > /dev/null
then
  echo "Failed to stop Gunicorn."
  exit 1
else
  echo "Gunicorn stopped successfully."
fi

exit 0
