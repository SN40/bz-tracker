from flask import Blueprint,render_template,flash,url_for,redirect,current_app,request
from project.forms import RegistrationForm,LoginForm,DeleteUserForm,EditProfileForm
from project.models import User,Mess
from project import db
from flask_login import current_user, login_user,logout_user,login_required
from werkzeug.security import check_password_hash
import os
from cryptography.fernet import Fernet
from sqlalchemy.ext.hybrid import hybrid_property


auth_bp = Blueprint('auth', __name__, template_folder="templates")

# Route für Registrierung
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
         # Hole den Encryptor aus der aktuellen App-Instanz
        encryptor = current_app.cipher_suite
        
        # Verschlüsseln und als String dekodieren für die DB
        encrypted_svnr = encryptor.encrypt(form.svnr.data.encode()).decode()
        
        user = User(
            title=form.title.data,
            firstname=form.firstname.data, 
            lastname=form.lastname.data,
            email=form.email.data, 
            svnr=encrypted_svnr
        )
        user.set_password(form.password.data)
        # Füge neuen Benutzer zur Session hinzu
        db.session.add(user)
        # Den neuen Benutzer in der Datenbank speichern.
        db.session.commit()
        flash("IhrDein Konto wurde erstellt. - Klicke auf 'Anmelden' um dich einzuloggen.", "success")
        # Umleiten zur Startseite
        return redirect(url_for("main.index"))
    # DEBUG: Wenn du hier landest bei POST, ist das Formular ungültig
    if form.errors:
        print(form.errors) 

    return render_template("auth/register.html", title="Registrieren", form=form)

# Route für Login'
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
     
    form = LoginForm()
    if form.validate_on_submit():
        # Benutzer per email nachschlagen
        user = db.session.scalar(db.select(User).where(User.email == form.email.data))

        # Überprüfen ob der Benutzer existiert und das Passwort korrekt ist.
        if user is None or not user.check_password(form.password.data):
            flash("Ungültige E-Mail oder Passwort", "error")
            return redirect(url_for("auth.login"))
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        # Die Remember-me-Funktionalität könnte hier implementiert werden, z.B. mit Flask-Login.
        login_user(user, remember=form.remember_me.data)
        # Wenn die Anmeldeinformationen korrekt sind, können Sie den Benutzer anmelden.
        flash("Erfolgreich eingeloggt", "success")
        return redirect(url_for("main.werte_liste"))
    # DEBUG: Wenn du hier landest bei POST, ist das Formular ungültig
    if form.errors:
        print(form.errors) 

    return render_template("auth/login.html", title="Login",form=form)

# Route zum Abmelden eines Benutzers
@auth_bp.route("/logout")
def logout():    # Hier können Sie die Logout-Funktionalität implementieren, z.B. mit Flask-Login.
    logout_user()
    flash("Erfolgreich ausgeloggt", "success")
    return redirect(url_for("main.index"))

@auth_bp.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    form = DeleteUserForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.password.data):
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash("Dein Konto wurde gelöscht.", "success")
            return redirect(url_for("main.index"))
        flash("Passwort falsch.", "danger")
    
    # Hier muss das Template gerendert werden, KEIN redirect auf sich selbst!
    return render_template("auth/delete_account.html", form=form)

# API-Route User-profil bearbeiten

@auth_bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    
    if form.validate_on_submit():
        # POST: Wir holen den TEXT aus dem Formular (.data) 
        # und speichern ihn in die Datenbank (current_user)
        current_user.title = form.title.data
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        current_user.email = form.email.data
        
        db.session.commit()
        flash("Profil aktualisiert!", "success")
        return redirect(url_for('auth.edit_profile'))
    
    elif request.method == 'GET':
        # GET: Wir holen den TEXT aus der Datenbank (current_user)
        # und schreiben ihn in das Formular-Feld (.data)
        # HIER DARF KEIN .data hinter current_user stehen!
        form.title.data = current_user.title
        form.firstname.data = current_user.firstname
        form.lastname.data = current_user.lastname
        form.email.data = current_user.email
        
    return render_template("auth/edit_profile.html", form=form)

