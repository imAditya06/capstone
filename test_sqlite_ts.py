# test_sqlite_ts.py
import sqlite3
from datetime import datetime
conn = sqlite3.connect("capstone.db")
cur = conn.cursor()
print("Latest 20 emotions:")
for row in cur.execute("SELECT id, user_id, emotion, detected_at FROM emotions ORDER BY id DESC LIMIT 20"):
    print(row)
conn.close()
