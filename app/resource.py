from flask import request , make_response , render_template , flash , redirect , url_for , session , \
    current_app
from flask_restful import Resource
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.current_app.extensions import db, login_manager, socketio
from flask_socketio import join_room, leave_room, send
from datetime import datetime
from app.current_app import es_client
rooms = {}


# User Model (Session Handling)
class User:
        query = None

        def __init__(self, id, username, email, password):
            self.id = id
            self.username = username
            self.email = email  # Include email as a parameter
            self.password = password

        def is_authenticated(self):
            return True

        def is_active(self):
            return True
        def get_id(self):
            return str(self.id)

    # User loader function (loads the user object by user_id)
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
            return make_response(render_template('Login.html'))  # Login page for User 1

        # Check if the Elasticsearch connection is successful

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
            return make_response(render_template("Login.html"))  # Login page for User 1

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


class Chatpage ( Resource ):
        # Method to store chat data for both users under one key in Elasticsearch
        @login_required
        def get(self , user_id):
            # Ensure the logged-in user isn't trying to chat with themselves
            if user_id == current_user.id:
                flash ( 'You cannot chat with yourself.' , 'danger' )
                return redirect ( url_for ( 'dashboard' ) )


            # Fetch the other user details by user_id from the database
            cur = db.connection.cursor ()
            cur.execute ( "SELECT id, username FROM user WHERE id = %s" , (user_id ,) )
            other_user = cur.fetchone ()  # Returns a tuple (id, username) or None if not found

            # Close the cursor after querying
            cur.close ()

            # Check if the user exists
            if not other_user:
                flash ( 'User not found' , 'danger' )
                return redirect ( url_for ( 'dashboard' ) )

            # Ensure the room exists or create one
            room = "-".join ( sorted ( [str ( current_user.id ) , str ( user_id )] ) )

            # Initialize the room in the rooms dictionary if it doesn't exist
            if room not in rooms:
                rooms[room] = {"members": 0 , "messages": []}

            room_messages = rooms[room]["messages"]

            # Store the room in the session so we can access it from the frontend
            session['room'] = room
            session['name'] = current_user.username

            # Render the chat page template
            return make_response (
                render_template ( 'chatpage.html' , other_user=other_user , room=room , room_messages=room_messages )
            )

        @staticmethod
        def store_message_in_es(room_key , name , email ,   message_content):
            doc = {
                'email': email ,
                'name': name ,
                'message':   message_content ,
                'timestamp': datetime.utcnow () ,
            }

            room_exists = es_client.exists ( index='chat_messages' , id=room_key )
            print ( f"Checking if room exists: {room_exists}" )

            if room_exists:
                try:
                    es_client.update ( index='chat_messages' , id=room_key , body={
                        'script': {
                            'source': 'ctx._source.messages.add(params.message)' ,
                            'params': {'message': doc}
                        }
                    } )
                    print ( "Message appended successfully." )
                except Exception as e:
                    print ( f"Error appending message: {e}" )
            else:
                try:
                    es_client.index ( index='chat_messages' , id=room_key , document={
                        'room_key': room_key ,
                        'messages': [doc]
                    } )
                    print ( "Room created and message stored." )
                except Exception as e:
                    print ( f"Error storing new room and message: {e}" )


        def get_chat_data_from_es(room_key ):
                response = es_client.get ( index="chat_messages" , id=room_key )
                if response['found']:
                    return response['_source']['messages']
                else:
                    return None  # No chat history found for this room



@socketio.on ( 'message' )
def handle_message(data):
    print ( f"Received message: {data}" )  # Log received message
    room = session.get ( 'room' )

    if room:
        name = session.get ( 'name' )
        email = current_user.email
        message_content = data.get ( 'message' )

        # Ensure message content is not empty
        if not message_content or not message_content.strip ():
            print ( "Empty message, ignoring." )
            return

        # Store message in Elasticsearch
        es = current_app.config['ELASTICSEARCH_CLIENT']
        try:
            # Pass `es` instance explicitly
            Chatpage.store_message_in_es ( es , room , name , email , message_content )
            print ( f"Message stored in Elasticsearch: {message_content}" )
        except Exception as e:
            print ( f"Error storing message in Elasticsearch: {e}" )

        # Broadcast message to the room
        send ( {"name": name , "message": message_content} , to=room )
@socketio.on('join')
def on_join(data):
    room = data['room']
    if room not in rooms:
        rooms[room] = {"members": 0, "messages": []}
    join_room(room)
    rooms[room]["members"] += 1
    send({"name": "Chat", "message": f"{session.get('name')} : Online."}, to=room)


@socketio.on ( 'disconnect' )
def disconnect():
        room = session.get ( 'room' )
        name = session.get ( 'name' )

        if room:
                leave_room ( room )  # User leaves the room
                rooms[room]["members"] -= 1
        if rooms[room]["members"] == 0:
            del rooms[room]
            send ( {"name": "System" , "message": f"{name} Offline."} , to=room )


