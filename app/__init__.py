# app/__init__.py
from flask import Flask
from config import Config
from flask_migrate import Migrate
from .models import db  # Import the 'db' object from your models.py

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Connect the database and migration tool
    db.init_app(app)
    migrate.init_app(app, db)

    # Register your routes
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app