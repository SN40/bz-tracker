from flask import Blueprint

v1_blueprint = Blueprint('v1', __name__)

# Der Hofmarschall sucht jetzt nach 'api_v1.py' statt 'routes.py'
from . import api_v1 