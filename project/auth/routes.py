from flask import Blueprint,render_template,flash,url_for,redirect,current_app,request
from project.forms import RegistrationForm,LoginForm,DeleteUserForm,EditProfileForm
from project.models import User,Mess
from project import db
from flask_login import current_user, login_user,logout_user,login_required
from werkzeug.security import check_password_hash
import os
from cryptography.fernet import Fernet
from sqlalchemy.ext.hybrid import hybrid_property
import hashlib



auth_bp = Blueprint('auth', __name__, template_folder="templates")

# Route für Registrierung
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # 1. E-Mail Check (wie bisher)
        if User.query.filter_by(email=form.email.data).first():
            flash("Diese E-Mail-Adresse wird bereits verwendet.", "danger")
            return render_template("auth/register.html", form=form)

        # 2. SVNR-Hash Check (DER TURBO!)
        # Wir hashen die Eingabe sofort, um in der DB danach zu suchen
        input_hash = hashlib.sha256(form.svnr.data.encode()).hexdigest()
        
        if User.query.filter_by(svnr_hash=input_hash).first():
            flash("Diese SVNR ist bereits registriert.", "danger")
            return render_template("auth/register.html", form=form)

        # 3. Wenn beide Checks okay sind -> Verschlüsseln & Speichern
        encryptor = current_app.cipher_suite
        encrypted_svnr = encryptor.encrypt(form.svnr.data.encode()).decode()
        
        user = User(
            title=form.title.data,
            firstname=form.firstname.data, 
            lastname=form.lastname.data,
            email=form.email.data, 
            svnr=encrypted_svnr,      # Für die Anzeige (Safe)
            svnr_hash=input_hash     # Für die Suche (Fingerabdruck)
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash("Registrierung erfolgreich! Bitte melde dich an.", "success")
        return redirect(url_for('auth.login'))

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
    encryptor = current_app.cipher_suite

    if form.validate_on_submit():
        # --- POST-LOGIK (Speichern) ---
        input_hash = hashlib.sha256(form.svnr.data.encode()).hexdigest()

        # Check: Nutzt jemand ANDERES (id != current_user.id) diese E-Mail oder SVNR?
        if User.query.filter(User.email == form.email.data, User.id != current_user.id).first():
            flash("E-Mail bereits vergeben!", "danger")
            return render_template("auth/edit_profile.html", form=form)

        if User.query.filter(User.svnr_hash == input_hash, User.id != current_user.id).first():
            flash("SVNR bereits registriert!", "danger")
            return render_template("auth/edit_profile.html", form=form)

        # Daten in das User-Objekt schreiben
        current_user.title = form.title.data
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        current_user.email = form.email.data
        current_user.svnr = encryptor.encrypt(form.svnr.data.encode()).decode()
        current_user.svnr_hash = input_hash
        
        db.session.commit()
        flash("Profil aktualisiert!", "success")
        return redirect(url_for('auth.edit_profile')) # Oder wo dein Profil liegt

    # --- GET-LOGIK (Laden der Seite) ---
    elif request.method == 'GET':
        # Bestehende Daten ins Formular füllen
        form.title.data = current_user.title
        form.firstname.data = current_user.firstname
        form.lastname.data = current_user.lastname
        form.email.data = current_user.email
        
        # SVNR ENTSCHLÜSSELN für die Anzeige im Formular
        if current_user.svnr:
            try:
                decrypted_svnr = encryptor.decrypt(current_user.svnr.encode()).decode()
                form.svnr.data = decrypted_svnr
            except Exception:
                form.svnr.data = "Fehler beim Entschlüsseln"

    return render_template("auth/edit_profile.html", title="Profil bearbeiten", form=form)



