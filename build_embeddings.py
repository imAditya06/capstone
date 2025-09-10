from deepface import DeepFace
import cv2
import os
import mysql.connector
from dotenv import load_dotenv
import json

load_dotenv()

# Connect to DB
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASS", "6Aditya@703"),
    database=os.getenv("DB_NAME", "emotion_db"),
    port=int(os.getenv("DB_PORT", 3306))  # 👈 force to int with default
)

cursor = conn.cursor()

known_dir = "known_people"  # folder with subfolders for each user

for person_name in os.listdir(known_dir):
    person_folder = os.path.join(known_dir, person_name)

    if os.path.isdir(person_folder):
        # Get user_id from DB
        cursor.execute("SELECT id FROM users WHERE name=%s", (person_name,))
        result = cursor.fetchone()

        if result:
            user_id = result[0]
        else:
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (person_name,))
            conn.commit()
            user_id = cursor.lastrowid

        # Loop through images in person's folder
        for image_name in os.listdir(person_folder):
            img_path = os.path.join(person_folder, image_name)

            try:
                embedding_obj = DeepFace.represent(img_path=img_path, model_name="Facenet")[0]
                embedding = embedding_obj["embedding"]

                cursor.execute(
                    "INSERT INTO embeddings (user_id, embedding) VALUES (%s, %s)",
                    (user_id, json.dumps(embedding))
                )
                conn.commit()
                print(f"✅ Saved embedding for {person_name}: {image_name}")

            except Exception as e:
                print(f"❌ Error processing {img_path}: {e}")

cursor.close()
conn.close()
