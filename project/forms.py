from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField,IntegerField
from wtforms.validators import DataRequired,Length,Email,NumberRange

class RegistrationForm(FlaskForm):
    username = StringField("Benutzername min. 4 max. 20 Zeichen",validators=[DataRequired(),Length(4,20)])
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
        if self.wert < 70:
            return "danger"   # Rot für Hypo
        elif 70 <= self.wert <= 140:
            return "success"  # Grün für Normal (nüchtern/leicht nach Essen)
        elif 141 <= self.wert <= 180:
            return "warning"  # Gelb für leicht erhöht
        else:
            return "danger"   # Rot für Hyper (>180)

