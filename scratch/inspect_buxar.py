import sqlite3
import json

conn = sqlite3.connect('flowshield.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- BUXAR VILLAGE DETAILS ---")
rows = c.execute("SELECT * FROM villages WHERE district='Buxar' OR name LIKE '%Buxar%'").fetchall()
for r in rows:
    d = dict(r)
    if 'geometry' in d and d['geometry']:
        try:
            d['geometry'] = json.loads(d['geometry'])
        except Exception:
            pass
    print(d)

print("\n--- SHELTERS FOR BUXAR ---")
for r in c.execute("SELECT * FROM shelters WHERE village_id IN (SELECT id FROM villages WHERE district='Buxar')").fetchall():
    print(dict(r))

print("\n--- ROUTES FOR BUXAR ---")
for r in c.execute("SELECT * FROM routes WHERE from_village_id IN (SELECT id FROM villages WHERE district='Buxar')").fetchall():
    print(dict(r))

print("\n--- OBSERVATIONS FOR BUXAR ---")
for r in c.execute("SELECT * FROM environmental_observations WHERE village_id IN (SELECT id FROM villages WHERE district='Buxar') ORDER BY timestamp DESC LIMIT 5").fetchall():
    print(dict(r))
