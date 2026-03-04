from flask_wtf import FlaskForm
from flask import current_app
from wtforms import StringField,PasswordField,SubmitField,BooleanField,IntegerField
from wtforms.validators import DataRequired,Length,Email,NumberRange,ValidationError,EqualTo
from .models import User
from flask_login import current_user
import hashlib

# Automatische Validierung für das Feld 'svnr'
def validate_svnr(self, field):
    s = field.data
    
    # 1. Format- und Längenprüfung
    if not s or len(s) != 10 or not s.isdigit():
        raise ValidationError("Die SVNr muss genau 10 Ziffern enthalten - ohne Leerzeichen!")
    
    # 2. Mathematische Prüfziffer (Österreichische Logik)
    weights = [3, 7, 9, 0, 5, 8, 4, 2, 1, 6]
    checksum = sum(int(s[i]) * weights[i] for i in range(10))
    p_ziffer = checksum % 11

     # 2. Datenbank-Check (muss jetzt entschlüsseln!)
    all_users = User.query.all()
    encryptor = current_app.cipher_suite
    
    if p_ziffer == 10 or p_ziffer != int(s[3]):
        raise ValidationError("Die SVNr ist ungültig (Prüfziffer falsch).")

    # 3. Einzigartigkeits-Check (Verhindert den IntegrityError)
    # Wir suchen in der DB, ob diese Nummer schon vergeben ist
    for user in all_users:
        if user.svnr: # Falls eine SVNR gesetzt ist
            try:
                # Entschlüsseln für den Vergleich
                decrypted_svnr = encryptor.decrypt(user.svnr.encode()).decode()
                if decrypted_svnr == field.data:
                    raise ValidationError("Diese SVNR ist bereits registriert.")
            except Exception:
                # Falls alte Klartext-Daten (wie bei Heidi) den Decrypt stören
                if user.svnr == field.data:
                    raise ValidationError("Diese SVNR ist bereits registriert.")

class RegistrationForm(FlaskForm):
    title= StringField("Titel ")
    firstname = StringField("Vorname min. 4 max. 20 Zeichen",validators=[DataRequired(),Length(4,20)])
    lastname = StringField("Nachname min. 4 max. 30 Zeichen",validators=[DataRequired(),Length(4,30)])
    svnr = StringField('SVNr', validators=[DataRequired(), validate_svnr])
    email = StringField("E-Mail",validators=[DataRequired(), Email()])
    password= PasswordField("Passwort min. 6 Zeichen",validators=[DataRequired(),Length(min=6)])
    submit=SubmitField("Registrieren")

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    remember_me = BooleanField('Eingeloggt bleiben')
    submit = SubmitField('Login')

class MessungForm(FlaskForm):
    # Wir validieren, dass es eine Zahl ist und im realistischen Bereich liegt
    wert = IntegerField('Blutzuckerwert (mg/dL)', validators=[
        DataRequired(message="Bitte einen Wert eingeben"),
        NumberRange(min=20, max=600, message="Wert unplausibel")
    ])
    notiz = StringField() # Neu hinzufügen
    submit = SubmitField('Speichern')

    def get_status_color(self):
        """Gibt die passende Bootstrap-Farbe zurück."""
        if self.wert.data is None:
            return "secondary"
    
        wert = self.wert.data
        if wert < 70:
            return "danger"
        elif 70 <= wert <= 140:
            return "success"  # Grün für Normal (nüchtern/leicht nach Essen)
        elif 141 <= wert <= 180:
            return "warning"  # Gelb für leicht erhöht
        else:
            return "danger"   # Rot für Hyper (>180)
        
class DeleteUserForm(FlaskForm):
    password = PasswordField('Passwort zur Bestättigung', validators=[DataRequired()])
    submit = SubmitField('Konto endgültig löschen')

class EditProfileForm(FlaskForm):
    title = StringField('Titel')
    firstname = StringField('Vorname', validators=[DataRequired()])
    lastname = StringField('Nachname', validators=[DataRequired()])
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    svnr = StringField('Sozialversicherungsnummer', validators=[DataRequired(), validate_svnr])
    new_password = PasswordField('Neues Passwort')
   

    # Hier muss exakt 'new_password' in Hochkommas stehen
    confirm_password = PasswordField('Wiederholen', 
        validators=[EqualTo('new_password', message='Passwörter stimmen nicht überein!')])
    submit = SubmitField('Änderungen speichern')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Diese E-Mail-Adresse wird bereits verwendet.')
    

        



