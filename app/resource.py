# app/resources.py
from flask import request, jsonify,make_response,render_template,flash,redirect,url_for,session
from flask_restful import Resource
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user,UserMixin
from .extensions import db , login_manager,socketio
from flask_socketio import emit, join_room, leave_room,send
from flask_login import login_required, current_user
import json
import MySQLdb


# Initialize rooms dictionary to hold room data
rooms = {}
# User Model (Session Handling)
# User Model (Session Handling)
class User:
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email  # Include email as a parameter
        self.password = password

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
## User loader function (loads the user object by user_id)
@login_manager.user_loader
def load_user(user_id):
    cur = db.connection.cursor()
    cur.execute("SELECT * FROM user WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()

    if user:
        return User(id=user[0], username=user[1], email=user[2], password=user[3])
    return None
class Home(Resource):
    def get(self):
        return make_response(render_template('Login.html'))
# Registration API
class Register(Resource):
    def get(self):
        return make_response(render_template("Register.html"))

    def post(self):
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM user WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()
        if existing_user:
            flash('Username or email already exists')  # Flash error message
            return redirect(url_for('register'))  # Redirect to registration page

        # Hash password and insert user into database
        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO user (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_password))
        db.connection.commit()
        cur.close()

        flash('User registered successfully')
        return redirect(url_for('login'))  # Redirect to login page

class Login(Resource):
    def get(self):
        return make_response(render_template("Login.html"))

    def post(self):
        # Parse form data
        username = request.form.get('username')
        password = request.form.get('password')

        cur = db.connection.cursor()
        cur.execute("SELECT * FROM user WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user:
            # Check if the password is correct
            if check_password_hash(user[3], password):  # Assuming password is in the 4th column
                # Create the User object, passing email as well
                user_obj = User(id=user[0], username=user[1], email=user[2], password=user[3])

                # Log the user in
                login_user(user_obj)

                flash('Login successful', 'success')
                return redirect(url_for('dashboard'))  # Redirect to dashboard
            else:
                flash('Invalid password', 'danger')
        else:
            flash('Invalid username', 'danger')

        return redirect(url_for('login'))  # Redirect back to login page


# Logout API
class Logout(Resource):
    @login_required
    def post(self):
        logout_user()
        flash('Logout successful', 'success')
        return redirect(url_for('home'))  # Redirect to the home page

class Dashboard(Resource):
    @login_required
    def get(self):
        # Get the current logged-in user data
        current_user_data = {
            'id': current_user.id,
            'username': current_user.username
        }

        # Fetch other users (not the current user)
        cur = db.connection.cursor()
        cur.execute("SELECT id, username, email FROM user WHERE id != %s", (current_user.id,))
        users = cur.fetchall()
        cur.close()

        # Pass current user data and other users to the template
        return make_response(render_template('Dashboard.html', users=users, current_user_data=current_user_data))



class Chatpage(Resource):
    @login_required
    def get(self, user_id):
        room = "-".join(sorted([str(current_user.id), str(user_id)]))  # Create a unique room identifier

        # Store the room and user data in the session
        session["room"] = room
        session["user_id"] = current_user.id
        session["name"] = current_user.username

        # Check if the room exists or not, and create it if necessary
        if room not in rooms:
            rooms[room] = {"members": 0, "messages": []}

        # Get the other user details (e.g., name, username) for the chat page
        cur = db.connection.cursor()
        cur.execute("SELECT id, username FROM user WHERE id = %s", (user_id,))
        other_user = cur.fetchone()
        cur.close()

        # Ensure the room messages are passed to the template
        room_messages = rooms[room]["messages"]

        # Render the chat page with the current and other user information
        return  make_response(render_template("Chatpage.html", user_id=user_id, room=room,
                               other_user=other_user, room_messages=room_messages))

    @socketio.on("connect")
    def connect():
        room = session.get("room")
        name = session.get("name")

        if room:
            join_room(room)  # User joins the chat room
            send({"name": name, "message": f"{name} has entered the room!"}, to=room)
            rooms[room]["members"] += 1
        else:
            print("Error: No room or name in session")

    @socketio.on("message")
    def message(data):
        room = session.get("room")
        if room and room in rooms:
            message_data = {
                "name": session.get("name"),
                "message": data.get("message")
            }
            send(message_data, to=room)  # Send the message to the chat room
            rooms[room]["messages"].append(message_data)  # Store the message in the room history
        else:
            print("Error: Room not found")

    @socketio.on("disconnect")
    def disconnect():
        room = session.get("room")
        name = session.get("name")

        if room:
            leave_room(room)  # User leaves the room
            rooms[room]["members"] -= 1
            if rooms[room]["members"] == 0:
                del rooms[room]  # Delete room if no members are left
            send({"name": name, "message": f"{name} has left the room."}, to=room)
        else:
            print("Error: No room or name in session")