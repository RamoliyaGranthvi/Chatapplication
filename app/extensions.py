from flask_mysqldb import MySQL
from flask_login import LoginManager
from flask_socketio import SocketIO  # Import SocketIO

# Initialize MySQL, LoginManager, and SocketIO
db = MySQL()
login_manager = LoginManager()
socketio = SocketIO()  # Initialize SocketIO here
