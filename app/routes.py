# app/routes.py
from flask_restful import Api
from .resource import Home,Register, Login, Logout,Dashboard,Chatpage


def add_routes(app):
    api = Api(app)

    # Register the resources with their respective URL paths
    api.add_resource(Home,'/')
    api.add_resource(Register, '/register')  # Register endpoint
    api.add_resource(Login, '/login')        # Login endpoint
    api.add_resource(Logout, '/logout')      # Logout endpoint
    api.add_resource ( Dashboard, '/dashboard' )  # Protected route
    api.add_resource(Chatpage, '/chatpage/<int:user_id>')