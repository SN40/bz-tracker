import os
import sys

# Fügt das aktuelle Verzeichnis zum Python-Pfad hinzu
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(basedir)

from project import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode)
