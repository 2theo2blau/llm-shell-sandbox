import os
import pathlib
import logging
from flask import Flask, send_from_directory
from dotenv import load_dotenv

from app.core.database import init_db
from app.controllers.api_controller import api

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    # Load environment variables
    load_dotenv()
    
    # Determine the correct static folder path
    current_dir = pathlib.Path(__file__).parent.absolute()
    static_folder = os.path.join(current_dir, '..', 'static')
    
    # Log static folder path for debugging
    logger.info(f"Static folder path: {static_folder}")
    logger.info(f"Static folder exists: {os.path.exists(static_folder)}")
    if os.path.exists(static_folder):
        logger.info(f"Static folder contents: {os.listdir(static_folder)}")
    
    # Create Flask app with explicit static URL path
    app = Flask(__name__, 
                static_url_path='', 
                static_folder=static_folder)
    
    # Log Flask configuration
    logger.info(f"Flask app static_url_path: {app.static_url_path}")
    logger.info(f"Flask app static_folder: {app.static_folder}")
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    # Register routes
    @app.route('/')
    def index():
        """Serve the main index.html page."""
        logger.info(f"Serving index.html from {app.static_folder}")
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/ls')
    def list_directory():
        """List the directory contents for the frontend."""
        try:
            # Import inside the function to avoid circular imports
            import subprocess
            
            # Use tree command if available, otherwise fallback to ls
            try:
                result = subprocess.check_output(['tree', '/app'], text=True)
            except FileNotFoundError:
                result = subprocess.check_output(['ls', '-R', '/app'], text=True)
            
            return {"success": True, "output": result}
        
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e), "output": e.output}, 500
    
    # Add route for static files explicitly
    @app.route('/<path:filename>')
    def serve_static(filename):
        logger.info(f"Serving static file: {filename}")
        return send_from_directory(app.static_folder, filename)
    
    # Initialize the database
    with app.app_context():
        init_db()
    
    return app


if __name__ == '__main__':
    # Get configuration from environment
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ['true', '1', 't']
    
    # Create and run the app
    app = create_app()
    
    # Log the port and host for debugging
    logger.info(f"Starting Flask app on {FLASK_HOST}:{FLASK_PORT}")
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG) 