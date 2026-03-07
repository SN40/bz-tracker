from flask import jsonify, request
from . import v2_blueprint
from project import db
# Die Klassiker für die Statistik:
from sqlalchemy import cast, Date
from sqlalchemy.sql import func # Wir nutzen wieder 'func', aber laden es GANZ SAUBER
from flask_login import current_user,login_required
from project.models import Mess 

@v2_blueprint.route('/werte/', methods=['GET', 'POST'])
def add_messwert_v2():
    # 1. Daten vom "Boten" (Request) entgegennehmen
    data = request.get_json() or {}
    wert = data.get('wert')
    # 2. Die Einlasskontrolle (Validation)
    if 'wert' not in data:
        return jsonify({"fehler": "Befehl ungültig: 'wert' fehlt!"}), 400
    
    try:
        neuer_wert = float(data['wert'])
    except (ValueError, TypeError):
        return jsonify({"fehler": "Ungültiger Datentyp: 'wert' muss eine Zahl sein!"}), 400

    # 3. Den neuen Messwert erstellen
    neuer_eintrag = Mess(
    wert=data.get('wert'),
    user_id=current_user.id,  # Wir weisen die ID 1 fest zu (Zuweisung, daher ein '=')
    notiz=data.get('notiz')
    )
    # Falls das Model ein manuelles Datum erlaubt:
    if 'date_mess' in data:
        # Hier müsste man noch ein datetime-Objekt parsen (optional)
        pass
     # API-Plausibilitäts-Check (analog zum Formular)
    if not wert or not (20 <= int(wert) <= 600):
        return jsonify({"fehler": "Wert unplausibel (20-600 mg/dL erlaubt)"}), 400
    # Duplikatscheck nutzt jetzt auch den echten User
    if Mess.ist_duplikat(current_user.id, data.get('wert')):
        return jsonify({"error": "Duplikat erkannt"}), 409
    
    # 4. In die Datenbank schreiben
    try:
        db.session.add(neuer_eintrag)
        db.session.commit()

         # 5. Erfolgsmeldung mit dem neuen Objekt (dank to_dict!)
        return jsonify({
            "status": "Erfolg",
            
            "daten": neuer_eintrag.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"Fehler": f"Datenbank-Fehler: {str(e)}"}), 500
    
# 2. NEU: Dein Statistik-Endpunkt (wird unten angehängt)
@v2_blueprint.route('/stats/tag', methods=['GET'])
def get_tages_stats_v2():
    # ... der neue Code für Gruppierung & Durchschnitt ...
    stats = db.session.query(
        func.date(Mess.date_mess).label('tag'),
        # pylint: disable=not-callable
        func.count(Mess.mess_id).label('anzahl'),
        func.avg(Mess.wert).label('durchschnitt')
    ).filter(Mess.user_id == current_user.id) \
     .group_by(func.date(Mess.date_mess)).all()

       
    bericht = [] 
        
    for s in stats:
        bericht.append({
            "tag": s.tag,
            "messungen_gesamt": s.anzahl,
            "durchschnittswert": round(s.durchschnitt, 1)  if s.durchschnitt else 0
        })

    return jsonify({
        "version": "v2-statistik",
        "bericht": bericht
    }), 200
    return jsonify({"version": "v2-statistik", "bericht": bericht}), 200    

# --- API UPDATE ---
@v2_blueprint.route('/werte/<int:mess_id>', methods=['PUT'])
@login_required
def update_messwert_v2(mess_id):
    messung = Mess.query.get_or_404(mess_id)
    
    # Ownership-Check
    if messung.user_id != current_user.id:
        return jsonify({"error": "Nicht autorisiert"}), 403

    data = request.get_json() or {}
    
    # Werte aktualisieren (falls im JSON vorhanden)
    if 'wert' in data:
        messung.wert = data['wert']
    if 'notiz' in data:
        messung.notiz = data['notiz']
        
    db.session.commit()
    return jsonify({"message": "Aktualisiert", "daten": messung.to_dict()}), 200

# --- API DELETE ---
@v2_blueprint.route('/werte/<int:mess_id>', methods=['DELETE'])
@login_required
def delete_messwert_v2(mess_id):
    messung = Mess.query.get_or_404(mess_id)
    
    if messung.user_id != current_user.id:
        return jsonify({"error": "Nicht autorisiert"}), 403
        
    db.session.delete(messung)
    db.session.commit()
    return jsonify({"message": f"Messung {mess_id} gelöscht"}), 200  

# --- NEU: Dashboard-Endpunkt für Live-Updates ---
@v2_blueprint.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard_v2():
    # Wir nutzen das Property 'mess_stats' aus deinem User-Model
    return jsonify({
        "status": "success",
        "statistik": current_user.mess_stats
    }), 200

@v2_blueprint.route('/werte/<int:mess_id>/notiz', methods=['PUT'])
@login_required
def update_notiz_v2(mess_id):
    messung = Mess.query.get_or_404(mess_id)
    
    if messung.user_id != current_user.id:
        return jsonify({"error": "Nicht autorisiert"}), 403

    data = request.get_json() or {}
    messung.notiz = data.get('notiz', "")
    db.session.commit()
    
    return jsonify({"status": "erfolg", "notiz": messung.notiz}), 200
