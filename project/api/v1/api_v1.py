from flask import jsonify
# In api_v1.py
from . import v1_blueprint
from project.models import Mess # Beispiel-Model
from project import db

@v1_blueprint.route('/test')
def test():
    return {"msg": "V1 meldet sich zum Dienst!"}

@v1_blueprint.route('/werte', methods=['GET'])
def get_werte_v1():
    # Die alte, stabile Logik: Einfach alle Werte ausgeben
    werte = db.session.execute(db.select(Mess)).scalars().all()
    return jsonify([w.to_dict() for w in werte]), 200
