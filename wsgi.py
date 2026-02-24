# wsgi.py
try:
    from project import create_app
except ImportError:
    # Falls der Linter den Pfad nicht findet, hilft oft ein absoluter Pfad-Fix
    import sys
    import os
    sys.path.append(os.getcwd())
    from project import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

