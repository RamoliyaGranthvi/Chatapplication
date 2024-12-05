from flask_socketio import SocketIO
# run.py
from app import create_app

app, socketio,es= create_app()

if __name__ == "__main__":
    socketio.run(app,allow_unsafe_werkzeug=True)

