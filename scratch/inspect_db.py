import sqlite3

conn = sqlite3.connect('flowshield.db')
c = conn.cursor()

print("--- TABLES ---")
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
print(tables)

print("\n--- VILLAGES COUNT & SAMPLES ---")
print("Total villages:", c.execute("SELECT count(*) FROM villages").fetchone()[0])
for row in c.execute("SELECT id, name, district, state, latitude, longitude FROM villages LIMIT 15").fetchall():
    print(row)

print("\n--- STATES & DISTRICTS IN VILLAGES ---")
for row in c.execute("SELECT state, district, count(*) FROM villages GROUP BY state, district").fetchall():
    print(row)

print("\n--- RIVERS ---")
for row in c.execute("SELECT id, name, basin, gauge_station, danger_level_meters, warning_level_meters FROM rivers").fetchall():
    print(row)

print("\n--- OBSERVATIONS COUNT ---")
print("Total observations:", c.execute("SELECT count(*) FROM environmental_observations").fetchone()[0])

print("\n--- OBSERVATIONS SAMPLE ---")
for row in c.execute("SELECT id, village_id, timestamp, rainfall_1h, rainfall_intensity, soil_moisture, river_level, source FROM environmental_observations ORDER BY timestamp DESC LIMIT 5").fetchall():
    print(row)
