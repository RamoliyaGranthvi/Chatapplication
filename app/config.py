# app/config.py
class Config:
    MYSQL_HOST= 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'root'
    MYSQL_DB = 'chatapplication'
    SECRET_KEY = 'your_secret_key_here'  # Make sure this key is secret and secure
    SESSION_TYPE = 'filesystem'
    SESSION_COOKIE_SECURE = True
    ELASTICSEARCH_URL = 'http://192.168.1.21:9200/'  # Your Elasticsearch URL
