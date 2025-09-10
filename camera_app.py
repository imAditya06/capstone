import cv2
import numpy as np
import json
from deepface import DeepFace
import mysql.connector
from dotenv import load_dotenv
import os

# ------------------- Load environment variables -------------------
load_dotenv()

# ------------------- MySQL Setup -------------------
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT"))
)
cursor = conn.cursor(dictionary=True)

# Load known embeddings from DB
cursor.execute("SELECT u.id, u.name, e.embedding FROM users u JOIN embeddings e ON u.id = e.user_id")
known_users = cursor.fetchall()
for user in known_users:
    user['embedding'] = np.array(json.loads(user['embedding']))

# ------------------- Face Detector -------------------
faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise IOError("Cannot open webcam")

# ------------------- Main Loop -------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray, 1.1, 4)

    # ------------------- Analyze emotion -------------------
    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        dominant_emotion = result[0]['dominant_emotion']
    except:
        dominant_emotion = "No Face"

    # ------------------- Get embedding -------------------
    try:
        embedding_result = DeepFace.represent(frame, model_name='Facenet', enforce_detection=False)
        if embedding_result:
            face_embedding_from_deepface = np.array(embedding_result[0]["embedding"])
        else:
            face_embedding_from_deepface = None
    except:
        face_embedding_from_deepface = None

    # ------------------- Match Face -------------------
    user_id = None
    matched_name = "Unknown"

    if face_embedding_from_deepface is not None:
        det_embedding = face_embedding_from_deepface
        for user in known_users:
            sim = np.dot(det_embedding, user['embedding'])  # cosine similarity can also be used
            if sim > 0.7:  # threshold for match
                user_id = user['id']
                matched_name = user['name']
                break

        # ------------------- Auto-add unknown user -------------------
        if user_id is None:
            new_name = input("Enter name for unknown face: ")
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (new_name,))
            conn.commit()
            new_user_id = cursor.lastrowid

            embedding_json = json.dumps(det_embedding.tolist())
            cursor.execute("INSERT INTO embeddings (user_id, embedding) VALUES (%s, %s)", (new_user_id, embedding_json))
            conn.commit()

            known_users.append({'id': new_user_id, 'name': new_name, 'embedding': det_embedding})
            user_id = new_user_id
            matched_name = new_name

    # ------------------- Insert Emotion -------------------
    if user_id is not None:
        sql = "INSERT INTO emotions (user_id, emotion) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, dominant_emotion))
        conn.commit()

    # ------------------- Draw Rectangles & Labels -------------------
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f"{matched_name}: {dominant_emotion}", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Show frame
    cv2.imshow('Realtime Emotion Recognition', frame)

    if cv2.waitKey(2) & 0xFF == ord('q'):
        break

# ------------------- Cleanup -------------------
cap.release()
cv2.destroyAllWindows()
conn.close()
