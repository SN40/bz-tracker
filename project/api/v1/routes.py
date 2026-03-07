from flask import jsonify
from . import v1_blueprint  # Importiert das Objekt aus deiner v1/__init__.py
from project.models import User # Passt den Pfad zu deinen Modellen an
from project import db



@v1_blueprint.route('/users', methods=['GET'])
def get_users_v1():
    # Kleiner Check, ob die DB-Anbindung in V1 steht
    users = db.session.execute(db.select(User)).scalars().all()
    user_list = [{"id": u.id, "username": u.username} for u in users]
    return jsonify(user_list), 200
