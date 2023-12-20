echo "Stopping script started at $(date)"

# Stopping existing Flask servers
echo "Stopping any existing Flask servers"
pkill -f "gunicorn -b 0.0.0.0:5000"

# Log finish
echo "Stopping script completed at $(date)"
