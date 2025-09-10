import sqlite3

# connect to the SQLite database
conn = sqlite3.connect("capstone.db")
cursor = conn.cursor()

print("\n--- Users ---")
for row in cursor.execute("SELECT * FROM users"):
    print(row)

print("\n--- Emotions ---")
for row in cursor.execute("SELECT * FROM emotions"):
    print(row)

print("\n--- Embeddings ---")
for row in cursor.execute("SELECT * FROM embeddings"):
    print(row)

conn.close()
