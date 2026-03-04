import pandas as pd
from datetime import timedelta

# 1. Datei laden (das britische Format mit Kommas)
input_file = 'deine_datei.csv'  # <--- Hier deinen Dateinamen eintragen
df = pd.read_csv(input_file)

# 2. Spalte 'Datum' in echte Zeit-Objekte umwandeln
df['Datum'] = pd.to_datetime(df['Datum'])

# 3. Sekunden auf 00 setzen (Sekunden-Eliminator)
df['Datum'] = df['Datum'].dt.floor('min')

# 4. Bonus: Duplikate innerhalb derselben Minute verhindern
# Falls zwei Werte die gleiche Minute haben, wird der zweite um 1 Minute verschoben
while df['Datum'].duplicated().any():
    df.loc[df['Datum'].duplicated(), 'Datum'] += timedelta(minutes=1)

# 5. Sauber speichern (ohne Sekunden im Textformat)
df.to_csv('sissi_bereit.csv', index=False, date_format='%Y-%m-%d %H:%M')

print("Fertig! Die Datei 'sissi_bereit.csv' ist nun kaiserlich sauber.")
