# app/config.py
class Config:
    MYSQL_HOST= 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'root'
    MYSQL_DB = 'chatapplication'
    SECRET_KEY = 'your_secret_key_here'  # Make sure this key is secret and secure
    SESSION_TYPE = 'filesystem'
    SESSION_COOKIE_SECURE = True

    # Elasticsearch configuration
    ELASTICSEARCH_HOST = 'localhost'  # Your Elasticsearch host
    ELASTICSEARCH_PORT = 9200  # Your Elasticsearch port
    ELASTICSEARCH_SCHEME = 'http'  # 'http' or 'https' based on your setup

    # Flask-SocketIO settings (if any)
    SOCKETIO_MESSAGE_QUEUE = 'redis://localhost:6379/0'  # Example, if you're using Redis as a message broker