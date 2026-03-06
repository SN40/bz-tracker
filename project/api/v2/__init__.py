from flask import Blueprint

v2_blueprint = Blueprint('v2', __name__)

# Hier wird die 'api_v2.py' für die neue Version geladen
from . import api_v2
