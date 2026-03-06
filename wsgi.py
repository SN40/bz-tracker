import os
import sys


# Pfad zum Projekt-Root (über 'project') sicherstellen
basedir = os.path.abspath(os.path.dirname(__file__))
if basedir not in sys.path:
    sys.path.append(basedir)

from project import create_app

app = create_app()

if __name__ == "__main__":
    # Achtung: app.run(debug=True) reicht hier völlig
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode)