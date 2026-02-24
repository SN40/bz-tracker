import os
from dotenv import load_dotenv      
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail

load_dotenv()
mail = Mail()


db = SQLAlchemy()
login_manager = LoginManager()

login_manager.login_view = "auth.login"

def create_app():

    from itsdangerous import URLSafeTimedSerializer
    from werkzeug.security import generate_password_hash


    app = Flask(__name__)
    # 1. Sicherheitsschlüssel
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
     # 2. Datenbank (bleibt genau so, nur der Pfad kommt idealerweise aus der .env)
    # Falls du SQLite nutzt, kannst du den Pfad direkt lassen oder auch auslagern:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
     # Gmail Konfiguration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
# Wichtig: App-Passwort!
    
    mail.init_app(app)
      
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)
    login_manager.login_view = 'auth.login' # 'auth' ist hier der Name deines Blueprints

    # Importiere und registriere Blueprints
    from .main.routes import main_bp
    from project.auth.routes import auth_bp
    from .api.routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    with app.app_context():
        from . import models
        db.create_all()
        
    return app