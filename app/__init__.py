from flask import Flask
from .extensions import db, login_manager, socketio  # Import socketio from extensions
from .routes import add_routes

def create_app():
    # Initialize Flask app
    app = Flask(__name__)

    # Load configuration settings from a config class
    app.config.from_object('app.config.Config')

    # Initialize the extensions (MySQL, LoginManager, etc.)
    db.init_app(app)
    login_manager.init_app(app)

    # Set the login view for Flask-Login
    login_manager.login_view = 'login'  # Ensure this matches the name of your login route

    # Register routes (URLs and their associated views)
    add_routes(app)

    # Initialize SocketIO for real-time features (if used)
    socketio.init_app(app)

    return app, socketio  # Return both app and socketio
