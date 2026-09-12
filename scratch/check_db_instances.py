import sqlite3
import os

for db_path in ['flowshield.db', os.path.join('apps', 'api', 'flowshield.db')]:
    if os.path.exists(db_path):
        size = os.path.getsize(db_path) / (1024 * 1024)
        conn = sqlite3.connect(db_path)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        print(f"{db_path} ({size:.2f} MB): {len(tables)} tables")
        counts = {}
        for t in tables[:10]:
            try:
                cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                counts[t] = cnt
            except:
                pass
        print(f"  Counts: {counts}")
        conn.close()
