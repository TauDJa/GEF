# config.py
import os
from dotenv import load_dotenv

# Find the .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Get the secret key from the .env file
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Get the database URL from the .env file
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Turn off a feature we don't need
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database connection settings for better encoding support
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'client_encoding': 'latin1',  # Use latin1 to read existing data
            'options': '-c client_encoding=latin1'
        }
    }