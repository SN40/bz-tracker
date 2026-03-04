import os
from dotenv import load_dotenv      
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from cryptography.fernet import Fernet
from sqlalchemy import MetaData

# 1. Pfad und Umgebung laden
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()

# 2. Extensions definieren (noch ohne App)
mail = Mail()
login_manager = LoginManager()
migrate = Migrate(render_as_batch=True)

# 3. Naming Convention für SQLite (Wichtig für Migrationen!)
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)
db = SQLAlchemy(metadata=metadata) # Nur EINMAL definieren!

def create_app():
    app = Flask(__name__)

    # --- Konfiguration ---
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'fallback-key'
    app.config['SECRET_KEY_ENCRYPTION'] = os.environ.get('FERNET_KEY')
   
    # Pfad zur Datenbank
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

    # --- Initialisierung ---
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()

    # Fernet für Verschlüsselung bereitstellen
    if app.config['SECRET_KEY_ENCRYPTION']:
        try:
            app.cipher_suite = Fernet(app.config['SECRET_KEY_ENCRYPTION'])
        except Exception as e:
            print(f"FEHLER: Ungültiger FERNET_KEY: {e}")
    else:
        print("WARNUNG: FERNET_KEY fehlt!")

    # Login Einstellungen
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # --- Blueprints ---
    from .main.routes import main_bp
    from project.auth.routes import auth_bp
    from .api.routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # User Loader
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app
