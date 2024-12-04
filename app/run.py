from flask_socketio import SocketIO

from app import create_app, socketio  # Import the create_app function and socketio instance


app, socketio = create_app()  # Create the app and get the socketio instance

if __name__ == '__main__':
    socketio.run(app, debug=False, allow_unsafe_werkzeug=True)  # Run the app with socketio
