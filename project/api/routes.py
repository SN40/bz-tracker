#from urllib import response

from flask import Blueprint, current_app, flash,jsonify, redirect, render_template,request,url_for,Response
from project.models import User
from project import db
from werkzeug.security import generate_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_mail import Message
from project import mail # Importiere das mail-Objekt


def generate_reset_token(email):
    s = Serializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset-salt')

def confirm_reset_token(token, expiration=3600):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None
    return email


api_bp = Blueprint('api', __name__, url_prefix='/api')

#API-Route zum Erstellen eines neuen Benutzers
@api_bp.route('/users', methods=['POST'])
def create_user():
    # Die JSON-Daten aus dem Anfang-Body holen
    data = request.get_json()
    if not data or not "username" in data or not "password" in data:
        return jsonify({"error": "Fehlende Daten"}), 400
    # Prüfen ob der Benutzername bereits existiert
    if db.session.scalar(db.select(User).where(User.username == data["username"])):
        return jsonify({"error": "Benutzername bereits vergeben"}), 400

    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    # Die Antwort mit den Benutzerdaten zurückgeben
    response = jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    })
    response.status_code = 201 # 201 Created
    # Einen Location_Header hinzufügen, der auf die neue Ressource zeigt
    response.headers["Location"] = url_for("api.get_user", user_id=user.id)
    return response


# API-Route zum Abrufen aller Benutzer
@api_bp.route('/users', methods=['GET'])
def get_users():
    users = db.session.scalars(db.select(User)).all()
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })
    return jsonify(user_list)

#API-Route zum Abrufen eines Benutzers anhand seiner ID
@api_bp.route('/users/<int:user_id>', methods=['GET']) 
def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    })
    
# API-Route zum Aktualisieren eines Benutzers anhand seiner ID   
@api_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Fehlende Daten"}), 400
    
    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    db.session.commit()
        
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }) 

# API-Route zum Löschen eines Benutzers anhand seiner ID
@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return "", 204 # 204 No Content

# API - Route für Passwort Reset
@api_bp.route('/res_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            return jsonify({"error": "E-Mail-Adresse erforderlich"}), 400
        
        user = db.session.scalar(db.select(User).where(User.email == email))
        if user:
            # Hier würde normalerweise eine E-Mail mit einem Reset-Link gesendet werden
            # Zum Beispiel  könnte mant einen Token generieren und diesen in der E-Mail verwenden
            token = generate_reset_token(user.email)
            reset_url = url_for('api.reset_password', token=token, _external=True)
             # TEST-AUSGABE: Erscheint in deinem VS Code / Terminal
            print(f"\n*** RESET LINK FÜR {user.email}: {reset_url} ***\n")
            print(f"VOLLSTÄNDIGER LINK: {reset_url}")

            # Die E-Mail erstellen
            msg = Message('Passwort zurücksetzen',
                          sender='noreply@deineapp.com',
                          recipients=[user.email])
            msg.body = f'''Hallo,um dein Passwort zurückzusetzen, klicke bitte auf den folgenden Link:
{reset_url}

Falls du diese Anfrage nicht gestellt hast, kannst du diese E-Mail einfach ignorieren.
'''
        # Abschicken!
        mail.send(msg)
        
        flash('Eine E-Mail mit Anweisungen wurde gesendet.', 'info')
        return redirect(url_for('auth.login'))
        flash('Check deine E-Mails für den Reset-Link.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_request.html')
           
@api_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # 1. Token validieren
    email = confirm_reset_token(token)
    if not email:
        flash('Der Reset-Link ist ungültig oder abgelaufen.', 'danger')
        return redirect(url_for('auth.login')) # Zurück zum Login
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        # 2. User finden (SQLAlchemy 2.0 Stil - Top!)
        user = db.session.scalar(db.select(User).where(User.email == email))
        
        if user:
            # 3. Passwort hashen und speichern
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Dein Passwort wurde aktualisiert!', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Benutzer nicht gefunden.', 'danger')
            return redirect(url_for('auth.login'))
            
    # GET-Anfrage: Zeige das Formular
    return render_template('auth/reset_token.html', token=token)
# Test route für die E-Mail-Funktionalität

#from project import mail # Import aus deiner __init__.py

@api_bp.route('/test-mail')
def test_mail():
    try:
        msg = Message(
            subject="Flask Test-Mail",
            sender="noreply@deineapp.com",
            recipients=["schwarz.no@gmail.com"] # Setze hier deine eigene Adresse ein!
        )
        msg.body = "Glückwunsch! Die Verbindung zu Gmail steht und dein App-Passwort ist korrekt."
        mail.send(msg)
        return "E-Mail erfolgreich gesendet! Schau in dein Postfach."
    except Exception as e:
        return f"Fehler beim Senden: {str(e)}"



       
          
      