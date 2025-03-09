"""
LLM Shell Sandbox - Main entry point for the application.
"""
import os
from app.core.app import create_app

# Create the application
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ['true', '1', 't']
    
    # Run the application with proper host/port binding
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG) 