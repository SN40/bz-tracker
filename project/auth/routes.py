from flask import Blueprint,render_template,flash,url_for,redirect
from project.forms import RegistrationForm,LoginForm
from project.models import User
from project import db
from flask_login import current_user, login_user,logout_user,login_required

auth_bp = Blueprint('auth', __name__, template_folder="templates")

# Route für Registrierung
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        # Füge neuen Benutzer zur Session hinzu
        db.session.add(user)
        # Den neuen Benutzer in der Datenbank speichern.
        db.session.commit()
        flash("Ihr Konto wurde erstellt", "success")
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