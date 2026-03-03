import os
from dotenv import load_dotenv

# Sucht die .env Datei im aktuellen Verzeichnis und lädt sie
load_dotenv()

class Config:
    # Holt den Key aus der .env. Falls er fehlt (None), wird der 'dev-key' genutzt.
    # WICHTIG: Im Live-Betrieb DARF der Notfall-Key niemals genutzt werden!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'du-solltest-einen-echten-key-nutzen-12345'
    
    # Datenbank-Pfad
    # Nutzt die DATABASE_URL aus .env oder standardmäßig SQLite im instance-Ordner
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/site.db'
    
    # Verhindert unnötigen Overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Falls du später E-Mails versendest (Passwort-Reset):
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
