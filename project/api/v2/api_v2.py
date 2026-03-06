from flask import jsonify, request
from . import v2_blueprint
from project.models import Mess
from project import db
# Die Klassiker für die Statistik:
from sqlalchemy import cast, Date
from sqlalchemy.sql import func # Wir nutzen wieder 'func', aber laden es GANZ SAUBER

@v2_blueprint.route('/werte/', methods=['GET', 'POST'])
def add_messwert_v2():
    # 1. Daten vom "Boten" (Request) entgegennehmen
    data = request.get_json() or {}

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
    user_id=1,  # Wir weisen die ID 1 fest zu (Zuweisung, daher ein '=')
    notiz=data.get('notiz')
    )
    
    # Falls das Model ein manuelles Datum erlaubt:
    if 'date_mess' in data:
        # Hier müsste man noch ein datetime-Objekt parsen (optional)
        pass

    # 4. In die Datenbank schreiben
    try:
        db.session.add(neuer_eintrag)
        db.session.commit()

         # 5. Erfolgsmeldung mit dem neuen Objekt (dank to_dict!)
        return jsonify({
            "status": "Erfolg",
            "nachricht": "Wert wurde vom Hofmarschall protokolliert.",
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
    ).group_by(func.date(Mess.date_mess)).all()

        # HIER FEHLTE DER BEFEHL:
    bericht = [] # <--- Diese Zeile MUSS vor dem 'for' stehen!
        
    for s in stats:
        bericht.append({
            "tag": s.tag,
            "messungen_gesamt": s.anzahl,
            "durchschnittswert": round(s.durchschnitt, 2)
        })

    return jsonify({
        "version": "v2-statistik",
        "bericht": bericht
    }), 200
    return jsonify({"version": "v2-statistik", "bericht": bericht}), 200    

   
