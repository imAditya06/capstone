# camera_app.py
import cv2
import numpy as np
import json
import sqlite3
from deepface import DeepFace
from datetime import datetime, timedelta

# timezone support (python 3.9+ zoneinfo, fallback to no tz)
try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("Asia/Kolkata")   # force to your desired zone
except Exception:
    LOCAL_TZ = None  # will use naive local time

DB_FILE = "capstone.db"
THRESHOLD = 0.7           # embedding similarity threshold (tune)
DEBOUNCE_SECONDS = 1.0    # do not log same user more often than this (seconds)

# ------------------- SQLite Setup -------------------
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# Create tables if not exist and ensure detected_at column exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    embedding TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
''')

# create emotions table if not exists (with detected_at)
cursor.execute('''
CREATE TABLE IF NOT EXISTS emotions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    emotion TEXT,
    detected_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
''')
conn.commit()

# If older table lacked detected_at, add it (safe to run repeatedly)
cursor.execute("PRAGMA table_info(emotions)")
cols = [r[1] for r in cursor.fetchall()]
if "detected_at" not in cols:
    cursor.execute("ALTER TABLE emotions ADD COLUMN detected_at TEXT")
    conn.commit()

# ------------------- Load known embeddings -------------------
cursor.execute("SELECT u.id, u.name, e.embedding FROM users u JOIN embeddings e ON u.id = e.user_id")
rows = cursor.fetchall()
known_users = []
for r in rows:
    uid, name, emb_json = r
    try:
        emb = np.array(json.loads(emb_json))
    except Exception:
        # fallback if embedding stored as repr string
        emb = np.array(eval(emb_json))
    known_users.append({"id": uid, "name": name, "embedding": emb})

print(f"Loaded {len(known_users)} known embeddings.")

# ------------------- Helper functions -------------------
def now_with_tz():
    """Return timezone-aware ISO timestamp string (space-separated), falling back to naive local time."""
    if LOCAL_TZ is not None:
        dt = datetime.now(LOCAL_TZ)
        # produce "YYYY-MM-DD HH:MM:SS+05:30"
        iso = dt.isoformat(sep=' ', timespec='seconds')  # includes offset if tz-aware
        return iso
    else:
        # naive local time
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def cosine_similarity(a, b):
    a = a / (np.linalg.norm(a) + 1e-10)
    b = b / (np.linalg.norm(b) + 1e-10)
    return float(np.dot(a, b))

def get_or_create_user(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE name = ?", (name,))
    r = cur.fetchone()
    if r:
        return r[0]
    cur.execute("INSERT INTO users (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid

def save_embedding(conn, user_id, embedding):
    emj = json.dumps(np.asarray(embedding).tolist())
    cur = conn.cursor()
    cur.execute("INSERT INTO embeddings (user_id, embedding) VALUES (?, ?)", (user_id, emj))
    conn.commit()

def save_emotion(conn, user_id, emotion, detected_at):
    cur = conn.cursor()
    cur.execute("INSERT INTO emotions (user_id, emotion, detected_at) VALUES (?, ?, ?)", (user_id, emotion, detected_at))
    conn.commit()

# ------------------- Face Detector -------------------
faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise IOError("Cannot open webcam")

# per-user debounce dictionary (user_id -> datetime of last logged)
last_logged = {}

print("Starting camera. Press 'q' to quit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.1, 4)

        # analyze whole frame for emotion (or you may analyze ROI per-face)
        try:
            analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            if isinstance(analysis, list) and len(analysis) > 0:
                dominant_emotion = analysis[0].get("dominant_emotion", "Unknown")
            elif isinstance(analysis, dict):
                dominant_emotion = analysis.get("dominant_emotion", "Unknown")
            else:
                dominant_emotion = "Unknown"
        except Exception:
            dominant_emotion = "Unknown"

        # get embedding for whole frame (you can change to ROI if desired)
        try:
            rep = DeepFace.represent(frame, model_name='Facenet', enforce_detection=False)
            if isinstance(rep, list) and len(rep) > 0 and isinstance(rep[0], dict) and "embedding" in rep[0]:
                emb = np.array(rep[0]["embedding"])
            elif isinstance(rep, (list, tuple, np.ndarray)):
                emb = np.asarray(rep).flatten()
            else:
                emb = None
        except Exception:
            emb = None

        matched_name = "Unknown"
        matched_id = None

        if emb is not None and len(known_users) > 0:
            best_sim = -1.0
            best_user = None
            for u in known_users:
                sim = cosine_similarity(emb, u["embedding"])
                if sim > best_sim:
                    best_sim = sim
                    best_user = u
            if best_user and best_sim >= THRESHOLD:
                matched_name = best_user["name"]
                matched_id = best_user["id"]

        # if unknown and embedding exists -> prompt to add (blocking)
        if matched_id is None and emb is not None:
            new_name = input("Unknown face detected. Enter name to register (or press Enter to skip): ").strip()
            if new_name:
                user_id = get_or_create_user(conn, new_name)
                save_embedding(conn, user_id, emb.tolist())
                known_users.append({"id": user_id, "name": new_name, "embedding": np.array(emb)})
                matched_name = new_name
                matched_id = user_id

        # Save emotion with timezone-aware timestamp, and debounce frequent writes
        if matched_id is not None:
            ts = now_with_tz()
            # check debounce
            last = last_logged.get(matched_id)
            log_allowed = True
            if last is not None:
                # parse last (it may be iso string) -> compare seconds
                # we stored datetimes in the dict as datetime objects
                if isinstance(last, datetime):
                    elapsed = datetime.now(localize_if_possible := (LOCAL_TZ is not None and LOCAL_TZ) or None) - last if LOCAL_TZ is None else datetime.now(LOCAL_TZ) - last
                    # above line attempts to compare timezone-aware or naive accordingly
                else:
                    elapsed = timedelta.max
                if elapsed.total_seconds() < DEBOUNCE_SECONDS:
                    log_allowed = False
            if log_allowed:
                # store current as datetime object for next debounce comparison
                last_logged[matched_id] = datetime.now(LOCAL_TZ) if LOCAL_TZ is not None else datetime.now()
                save_emotion(conn, matched_id, dominant_emotion, ts)
                print(f"Logged: user={matched_name} emotion={dominant_emotion} at {ts}")

        # Draw boxes + label
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(frame, f"{matched_name}: {dominant_emotion}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        cv2.imshow("Face+Emotion", frame)
        if cv2.waitKey(2) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    conn.close()
