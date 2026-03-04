import hashlib
from project import create_app, db
# WICHTIG: Kein Punkt vor models, wenn die Datei im Hauptverzeichnis liegt
from project.models import User 

app = create_app()
with app.app_context():
    # Hole den Encryptor aus der App-Konfiguration
    encryptor = app.cipher_suite 
    users = User.query.all()
    
    print(f"Starte Update für {len(users)} User...")
    
    for u in users:
        # Nur wenn SVNR da ist, aber der Hash noch fehlt
        if u.svnr and not u.svnr_hash:
            try:
                # 1. SVNR entschlüsseln
                decrypted_svnr = encryptor.decrypt(u.svnr.encode()).decode()
                # 2. SHA-256 Hash erzeugen
                u.svnr_hash = hashlib.sha256(decrypted_svnr.encode()).hexdigest()
                print(f"✅ Hash für {u.email} generiert.")
            except Exception as e:
                print(f"❌ Fehler bei {u.email}: {e}")
    
    db.session.commit()
    print("Fertig! Alle Hashes wurden aktualisiert.")