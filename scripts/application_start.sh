#source venv/bin/activate

# Set environment variables
export FLASK_APP=Flask-App
export FLASK_ENV=production  # Change to "development" for development mode

# Install dependencies (if needed)
pip install -r requirements.txt

# Start the Flask application
flask run --host=0.0.0.0 --port=5000
