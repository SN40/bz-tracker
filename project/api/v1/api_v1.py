from flask import jsonify
from flask_login import login_required, current_user
# In api_v1.py
from . import v1_blueprint
from project.models import Mess # Beispiel-Model
from project import db


@v1_blueprint.route('/werte', methods=['GET'])
@login_required
def get_werte_v1():
    # Jetzt filtern wir automatisch nach dem eingeloggten User!
    werte = db.session.execute(
        db.select(Mess).filter_by(user_id=current_user.id)
    ).scalars().all()
    return jsonify([w.to_dict() for w in werte]), 200