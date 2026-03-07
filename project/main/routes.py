import io
import pandas as pd
from datetime import datetime,timedelta
from flask import Blueprint,render_template,url_for,redirect,flash,request,Response,make_response,jsonify,current_app
from io import StringIO
import csv
from project.forms import RegistrationForm,LoginForm,MessungForm,DeleteUserForm
from flask_login import login_required,current_user,logout_user
from project.models import Mess,User
from project import db
import json
from itertools import groupby   
from werkzeug.exceptions import RequestEntityTooLarge









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
    page = request.args.get('page', 1, type=int)
    days = request.args.get('days', default=0, type=int)
    
    # 1. SPEICHERN (POST) - Zuerst abhandeln
    if form.validate_on_submit():
        if Mess.ist_duplikat(current_user.id, form.wert.data):
            flash("Wert wurde bereits vor kurzem gespeichert!", "warning")
            return redirect(url_for('main.werte_liste'))
            
        neuer_wert = Mess(wert=form.wert.data, notiz=form.notiz.data, user_id=current_user.id)
        db.session.add(neuer_wert)
        db.session.commit()
        flash("Wert erfolgreich gespeichert!", "success")
        return redirect(url_for('main.werte_liste'))

    # 2. BASIS-QUERY
    query = Mess.query.filter_by(user_id=current_user.id)
    if days > 0:
        stichtag = datetime.now() - timedelta(days=days)
        query = query.filter(Mess.date_mess >= stichtag)

    # 3. DATEN FÜR GRAFIK (Chronologisch AUFSTEIGEND)
    messungen_grafik = query.order_by(Mess.date_mess.asc()).all()
    bzLabels = [m.date_mess.strftime('%d.%m. %H:%M') for m in messungen_grafik]
    bzWerte = [int(m.wert) for m in messungen_grafik]

    # Schnittlinie berechnen
    if bzWerte:
        avg = round(sum(bzWerte) / len(bzWerte), 1)
        schnitt_linie_json = json.dumps([avg] * len(bzWerte))
    else:
        schnitt_linie_json = json.dumps([])

    # 4. DATEN FÜR TABELLE (Pagination & Gruppierung)
    pagination = query.order_by(Mess.date_mess.desc()).paginate(page=page, per_page=10, error_out=False)

    gruppierte_fuer_tabelle = []
    # Gruppierung nach Datum (Wichtig: groupby braucht sortierte Daten, was pagination.items ist)
    from itertools import groupby
    for datum, gruppe in groupby(pagination.items, key=lambda x: x.date_mess.date()):
        tages_werte = list(gruppe)
        durchschnitt = round(sum(m.wert for m in tages_werte) / len(tages_werte), 1)
        gruppierte_fuer_tabelle.append({
            'datum': datum,
            'durchschnitt': durchschnitt,
            'werte': tages_werte
        })

    # 5. ÜBERGABE ANS TEMPLATE
    # Alle im HTML verwendeten Variablen (bzLabels, bzWerte, schnitt_linie) müssen hier rein!
    return render_template("main/werte.html", 
                            title="Blutzucker Verlauf", 
                            gruppierte_messungen=gruppierte_fuer_tabelle,
                            pagination=pagination,
                            bzLabels=bzLabels, 
                            bzWerte=bzWerte,
                            schnitt_linie=schnitt_linie_json,
                            selected_days=days,
                            form=form)

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


@main_bp.route("/werte/drucken")
@login_required
def werte_drucken():
    # Zeitraum aus der URL holen, Standard sind 30 Tage (4 Wochen)
    tage = request.args.get('zeitraum', default=30, type=int)
    start_datum = datetime.now() - timedelta(days=tage)
     # 1. SVNR für den Druck entschlüsseln
    # Wir greifen auf den Encryptor zu, den wir in __init__.py an app gebunden haben
    encryptor = current_app.cipher_suite
    svnr_anzeige = ""
    
    if current_user.svnr:
        try:
            # Versuch die SVNR zu entschlüsseln
            svnr_anzeige = encryptor.decrypt(current_user.svnr.encode()).decode()
        except Exception:
            # Fallback, falls in der DB noch Klartext von alten Tests steht
            svnr_anzeige = current_user.svnr
    # 2. Deine bestehende Logik für die Messwerte
    # Nur Messwerte ab dem Startdatum für den aktuellen User laden
    alle_messungen = Mess.query.filter(
        Mess.user_id == current_user.id,
        Mess.date_mess >= start_datum
    ).order_by(Mess.date_mess.desc()).all()

    gruppiert = []
    # Gruppierung nach Kalendertag
    for datum, gruppe in groupby(alle_messungen, key=lambda x: x.date_mess.date()):
        werte = list(gruppe)
        # Hier wichtig: 'durchschnitt' (nicht 'schnitt') passend zum Template
        durchschnitt = round(sum(m.wert for m in werte) / len(werte), 1)
        gruppiert.append({
            'datum': datum, 
            'durchschnitt': durchschnitt, 
            'werte': werte
            
        })

        # --- NEU: Berechnung für die Grafik ---
    total = len(alle_messungen)
    stats_prozent = None
    
    # --- KORREKTUR: Berechnung für die Grafik ---
    total = len(alle_messungen)
    stats_prozent = None

    if total > 0:
        # WICHTIG: Nutze 'alle_messungen' statt 'werte'
        tief = len([m for m in alle_messungen if m.wert < 70])
        ziel = len([m for m in alle_messungen if 70 <= m.wert <= 139])
        erhoeht = len([m for m in alle_messungen if 140 <= m.wert <= 179])
        hoch = len([m for m in alle_messungen if m.wert >= 180])
        
        stats_prozent = {
            'hoch': round((hoch / total) * 100),
            'erhoeht': round((erhoeht / total) * 100),
            'ziel': round((ziel / total) * 100),
            'tief': round((tief / total) * 100),
            'gesamt_anzahl': total
        }
    else:
        # Fallback für leere Listen
        stats_prozent = {'tief': 0, 'ziel': 0, 'erhoeht': 0, 'hoch': 0, 'gesamt_anzahl': 0}
            # Aufruf der Property OHNE Klammern (), da @property im Model steht
    entschluesselte_nummer = current_user.real_svnr     
    return render_template("main/druckansicht.html", 
                            gruppierte_messungen=gruppiert, 
                            heute=datetime.now(),
                            svnr=entschluesselte_nummer,
                            zeitraum=tage,
                            stats=stats_prozent) 

@main_bp.route('/download_csv')
@login_required
def download_csv():
    # 1. Zeitraum aus der URL holen (Standard: Alle Werte, falls kein Parameter)
    tage = request.args.get('zeitraum', type=int)
    
    query = Mess.query.filter_by(user_id=current_user.id)
    
    if tage:
        start_datum = datetime.now() - timedelta(days=tage)
        query = query.filter(Mess.date_mess >= start_datum)
        date_info = f"_{tage}tage"
    else:
        date_info = "_gesamt"

    messungen = query.order_by(Mess.date_mess.desc()).all()
    
    # 2. In-Memory Datei erstellen
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Datum', 'Wert', 'Notiz'])
    
    for m in messungen:
        zeit_string = m.date_mess.strftime('%d.%m.%Y %H:%M:%S')
        cw.writerow([zeit_string, m.wert, m.notiz])

    # 3. Response mit dynamischem Dateinamen
    output = make_response(si.getvalue())
    filename = f"blutzucker_backup{date_info}_{datetime.now().strftime('%Y%m%d')}.csv"
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    
    return output

# API-Route für file Upload (CSV Import)
@main_bp.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    neu = 0
    uebersprungen = 0
    should_delete = 'delete_old' in request.form
    
    file = request.files.get('file')
    if not file:
        return redirect(url_for('main.werte_liste'))

    try:
        file.seek(0)
        content = file.stream.read().decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(content))

        df.columns = df.columns.str.strip().str.capitalize()
        # Datum fixen und ungültige Zeilen (NaT) entfernen
        # df['Datum'] = pd.to_datetime(df['Datum'], errors='coerce')
        # df = df.dropna(subset=['Datum'])
        # df['Datum'] = df['Datum'].dt.floor('min')
        df['Datum'] = pd.to_datetime(df['Datum'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Datum'])
        df = df.sort_values('Datum')
        # 2. Sekunden/Mikrosekunden entfernen
        df['Datum'] = df['Datum'].dt.floor('min')
        # Duplikate in der CSV behandeln
        # df = df.sort_values('Datum')
        # while df['Datum'].duplicated().any():
        #     df.loc[df['Datum'].duplicated(), 'Datum'] += timedelta(minutes=1)
        # 3. Präzise Duplikats-Korrektur innerhalb der CSV
        # Verhindert, dass Werte durch die Schleife in falsche Monate rutschen
        df['temp_count'] = df.groupby('Datum').cumcount()
        df['Datum'] = df['Datum'] + pd.to_timedelta(df['temp_count'], unit='m')
        df = df.drop(columns=['temp_count'])

        reader = df.to_dict(orient='records')
    except Exception as e:
        flash(f"Fehler bei der CSV-Aufbereitung: {e}", "danger")
        return redirect(url_for('main.werte_liste'))

    try:
        if should_delete:
            # Lösche wirklich alle alten Einträge dieses Users
            Mess.query.filter_by(user_id=current_user.id).delete()
            db.session.flush() # Schiebt das Löschen in die DB-Pipeline vor dem Neu-Einfügen
        
            for row in reader:
                csv_date = row.get('Datum')
                # Umwandlung von Pandas Timestamp zu Python datetime
                if hasattr(csv_date, 'to_pydatetime'):
                    csv_date = csv_date.to_pydatetime()
                # Wert-Verarbeitung (Sicherstellen, dass es eine Zahl ist)
                try:
                    wert_raw = row.get('Wert')
                    # Prüfen auf NaN oder leere Werte
                    if pd.isna(wert_raw) or wert_raw == '':
                        wert = 0
                    else:
                        wert = int(float(wert_raw))
                except (ValueError, TypeError):
                    wert = 0

                 # Notiz-Verarbeitung (Verhindert das "nan" in der Anzeige)
                raw_notiz = str(row.get('Notiz', ''))
                if raw_notiz.lower() == 'nan' or not raw_notiz:
                    notiz = ""
                else:
                    notiz = raw_notiz[:200]

                # Falls NICHT gelöscht werden soll, prüfen wir auf Dubletten
                if not should_delete:
                    existiert = Mess.query.filter_by(
                        user_id=current_user.id, 
                        date_mess=csv_date
                    ).first()
                else:
                    existiert = None # Wenn gelöscht wurde, brauchen wir nicht prüfen

                if not existiert:
                    neuer_messwert = Mess(
                        date_mess=csv_date, 
                        wert=wert, 
                        notiz=notiz if notiz != 'nan' else '', # Fix für das 'nan' in deiner Anzeige
                        user_id=current_user.id
                    )
                    db.session.add(neuer_messwert)
                    neu += 1
                else:
                    uebersprungen += 1

            db.session.commit()
            flash(f"Erfolg! {neu} neu hinzugefügt, {uebersprungen} übersprungen.", "success")
    
    except Exception as e:
        db.session.rollback() # WICHTIG: Macht alle Änderungen rückgängig bei Fehler
        flash(f"Datenbank-Fehler beim Speichern: {e}", "danger")
        # Hier könntest du zusätzlich print(f"DEBUG: {e}") nutzen für das PythonAnywhere Error Log

    return redirect(url_for('main.werte_liste'))



@main_bp.route('/update_notiz/<int:mess_id>', methods=['POST'])
@login_required
def update_notiz(mess_id):
    data = request.get_json()
    messung = Mess.query.get_or_404(mess_id)
    
    # Sicherstellen, dass die Messung auch dem User gehört!
    if messung.user_id != current_user.id:
        return {"status": "error", "message": "Nicht erlaubt"}, 403
        
    messung.notiz = data.get('notiz', '')
    db.session.commit()
    return {"status": "success"}, 200

# API-Route Bestättigung zum Löschen des Benutzerkontos
main_bp.route('/account/delete', methods=['GET', 'POST'])
@login_required
def delete_account():
    form = DeleteUserForm()

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
        logout_user(user)
        # Wenn die Anmeldeinformationen korrekt sind, können Sie den Benutzer anmelden.
        flash("Erfolgreich eingeloggt", "success")
        return redirect(url_for("main.werte_liste"))
    # DEBUG: Wenn du hier landest bei POST, ist das Formular ungültig
    if form.errors:
        print(form.errors) 

    return render_template("auth/login.html", title="Login",form=form)


    if request.method == 'POST':
        # Optional: Passwort zur Sicherheit erneut abfragen
        password = request.form.get('password')
        if not current_user.check_password(password):
            flash("Passwort falsch!")
            return redirect(url_for('delete_account'))

        user = current_user
        
        # 1. User ausloggen, damit die Session ungültig wird
        logout_user()
        
        # 2. User aus der Datenbank löschen
        db.session.delete(user)
        db.session.commit()

        flash("Dein Konto wurde erfolgreich gelöscht.")
        return redirect(url_for('main.index'))

    # Zeigt bei GET die Sicherheitsabfrage (Template)
    return render_template('confirm_delete.html')

@main_bp.errorhandler(413)
@main_bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    flash("Die Datei ist zu groß! Maximal 2 MB erlaubt.", "danger")
    return redirect(url_for('main.werte_liste')), 413



