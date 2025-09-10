import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",        # 👈 replace with your MySQL username
        password="6Aditya@703",  # 👈 replace with your MySQL password
        database="emotion_db"  # 👈 the DB you created
    )
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
