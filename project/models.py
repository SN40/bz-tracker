from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from datetime import datetime, timezone
import pytz
from flask import current_app


#from project import db    # Importiere das db-Objekt aus der __init__.py
from datetime import datetime, timezone

# Definiere das User-Modell
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable = False)
    firstname = db.Column(db.String(80),nullable=False)
    lastname = db.Column(db.String(80), nullable =False)
    svnr = db.Column(db.String(255), unique=True, nullable=True)
    svnr_hash = db.Column(db.String(64), unique=True, index=True, nullable=True) # NEU darunter
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    messungen = db.relationship('Mess', back_populates='user', lazy="dynamic",cascade="all, delete-orphan")

    @property
    def mess_stats(self):
        """Berechnet alle Statistiken basierend auf den aktuellen Messwerten."""
        # Holen aller Werte als Liste von Integern
        werte = [m.wert for m in self.messungen.all()]
        anzahl = len(werte)
        
        if anzahl == 0:
            return {
                'anzahl': 0, 
                'summe': 0, 
                'schnitt': 0, 
                'hba1c': 0
            }

        summe_werte = sum(werte)
        durchschnitt = summe_werte / anzahl
        # Die korrigierte Formel mit Klammern
        hba1c_wert = (durchschnitt + 46.7) / 28.7

        return {
            'anzahl': anzahl,
            'summe': summe_werte,
            'schnitt': round(durchschnitt, 1),
            'hba1c': round(hba1c_wert, 2)
        }
    @property
    def real_svnr(self):
        """Entschlüsselt die SVNR live für die Anzeige."""
        if not self.svnr:
            return "Nicht angegeben"
        
        try:
            # Greift auf die cipher_suite aus deiner __init__.py zu
            encryptor = current_app.cipher_suite
            # Von String zu Bytes -> Entschlüsseln -> Zurück zu String
            return encryptor.decrypt(self.svnr.encode()).decode()
        except Exception:
            # Falls in der DB noch Klartext steht, gib diesen zurück
            return self.svnr


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"
    
# Definiere das Mess-Modell
class Mess(db.Model):
    def get_berlin_time():
        return datetime.now(pytz.timezone('Europe/Berlin'))
    
    mess_id = db.Column(db.Integer, primary_key=True)
    #date_mess = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False) # Aktuelles Datum mit Zeitzone
    date_mess = db.Column(db.DateTime, default=get_berlin_time, nullable=False) # Aktuelles Datum mit Zeitzone
    
    wert = db.Column(db.Integer,nullable=False)
    notiz = db.Column(db.String(200),nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    user = db.relationship('User', back_populates='messungen')

    def __repr__(self):
        return f"<Mess {self.wert}>"
    
    def get_status_color(self):
        """Gibt die passende Bootstrap-Farbe zurück."""
        if self.wert < 70:
            return "danger"   # Rot für Hypo
        elif 70 <= self.wert <= 140:
            return "success"  # Grün für Normal (nüchtern/leicht nach Essen)
        elif 141 <= self.wert <= 180:
            return "warning"  # Gelb für leicht erhöht
        else:
            return "danger"   # Rot für Hyper (>180)
        
    