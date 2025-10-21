# app/__init__.py
import os
from flask import Flask
from config import Config
from flask_migrate import Migrate
from .models import db  # Import the 'db' object from your models.py

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ✅ --- Configuration pour l'upload de photos ---
    # Nous utilisons app.instance_path, qui est un dossier créé par Flask
    # en dehors du package de l'application, idéal pour les données utilisateur.
    upload_folder = os.path.join(app.instance_path, 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # S'assurer que le dossier d'upload existe
    try:
        os.makedirs(upload_folder, exist_ok=True)
    except OSError as e:
        app.logger.error(f"Erreur lors de la création du dossier d'uploads: {e}")
    # ✅ --- Fin de la configuration ---

    # Connect the database and migration tool
    db.init_app(app)
    migrate.init_app(app, db)

    # Register your routes
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app