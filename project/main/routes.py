from flask import Blueprint,render_template,url_for,redirect,flash,request
from project.forms import RegistrationForm,LoginForm,MessungForm
from flask_login import login_required,current_user
from project.models import User,Mess
from project import db


#Erstelle ein Blueprint-Objekt
# Das erste Argument ist der name des Bluprints.
# Das zweite Argument ist der Name des Moduls, in dem sich der Blueprint befindet0 Normalerweise __name__.

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    return render_template("main/index.html", title="Startseite")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("main/dashboard.html", title="Dashboard", user=current_user)

# Route für Blutzucker Werte
@main_bp.route("/werte", methods=["GET", "POST"])
@login_required
def werte_liste():
    form = MessungForm()
    
    if form.validate_on_submit():
        # Daten aus dem Formular nehmen
        neuer_wert = Mess(wert=form.wert.data,notiz=form.notiz.data, user=current_user)
        db.session.add(neuer_wert)
        db.session.commit()
        
        flash('Messwert erfolgreich gespeichert!', 'success')
        return redirect(url_for('main.werte_liste'))

    
    # Alle Messungen des aktuellen Nutzers für die Tabelle holen
    meine_messungen = current_user.messungen.order_by(Mess.date_mess.desc()).all()
    
    # return render_template(
    #     "main/werte.html", 
    #     form=form, 
    #     messungen=meine_messungen
    # )
    page = request.args.get('page', 1, type=int)
    
    # .paginate() statt .all() verwenden (z.B. 10 Einträge pro Seite)
    pagination = Mess.query.filter_by(user_id=current_user.id)\
    .order_by(Mess.date_mess.desc())\
    .paginate(page=page, per_page=10, error_out=False)

    
    messungen = pagination.items  # Nur die Messungen der aktuellen Seite
    return render_template('main/werte.html',form=form, messungen=messungen, pagination=pagination
    )

# Delete Route zum löschen von Messungen
@main_bp.route("/werte/delete/<int:mess_id>", methods=["GET", "POST"]) 
def delete_messung(mess_id):
    messung = Mess.query.get_or_404(mess_id)
    
    # Sicherstellen, dass die Messung zum aktuellen Nutzer gehört
    if messung.user_id != current_user.id:
        flash("Du kannst nur deine eigenen Messungen löschen.", "danger")
        return redirect(url_for('main.werte_liste'))
    
    db.session.delete(messung)
    db.session.commit()
    flash("Messung erfolgreich gelöscht!", "success")
    return redirect(url_for('main.werte_liste'))

    # Update Route  zum Aktualisieren einer Messung
@main_bp.route("/werte/update/<int:mess_id>", methods=["GET", "POST"])
def update_messung(mess_id):
    messung = Mess.query.get_or_404(mess_id)
    form = MessungForm(obj=messung)  # Formular mit bestehenden Daten füllen
    if form.validate_on_submit():
        messung.wert = form.wert.data  # Wert aktualisieren
        messung.notiz = form.notiz.data  # Notiz aktualisieren
        db.session.commit()
        flash("Messung erfolgreich aktualisiert!", "success")
        return redirect(url_for('main.werte_liste'))
    # Sicherstellen, dass die Messung zum aktuellen Nutzer gehört
    if messung.user_id != current_user.id:
        flash("Du kannst nur deine eigenen Messungen bearbeiten.", "danger")
        return redirect(url_for('main.werte_liste'))
    
    form = MessungForm(obj=messung)  # Formular mit bestehenden Daten füllen
    
    if form.validate_on_submit():
        messung.wert = form.wert.data  # Wert aktualisieren
        db.session.commit()
        flash("Messung erfolgreich aktualisiert!", "success")
        return redirect(url_for('main.werte_liste'))
    
    return render_template("main/update_messung.html", form=form, messung=messung)


# @main_bp.route("/test-setup")
# def test_setup():
#     u1 = User(username="Max", email="Max@example.com")
#     u1.set_password("geheim")
#     u2 = User(username="Erika", email="erika@example.com")
#     u2.set_password("geheim")  

#     db.session.add_all([u1, u2])
#     db.session.commit()  # Damit die IDs zugewiesen werden   

#     # 2. Messwerte zuweisen (über die Beziehung 'messungen')
#     m1 = Mess(wert=120, user=u1) # Max hat 120
#     m2 = Mess(wert=95, user=u2)  # Erika hat 95
#     m3 = Mess(wert=140, user=u1) # Max hat noch einen Wert
    
#     db.session.add_all([m1, m2, m3])
#     db.session.commit()

#     # 3. Kontrolle im Log
#     ausgabe = ""
#     for user in [u1, u2]:
#         ausgabe += f"User {user.username} hat {user.messungen.count()} Messung(en): "
#         ausgabe += ", ".join([str(m.wert) for m in user.messungen]) + "<br>"
    
#     return ausgabe