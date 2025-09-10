# Capstone Project - Multimodal AI Agentic System

This project is part of a larger **multimodal AI agentic system**.  
It includes **real-time face recognition and emotion detection** using `DeepFace`, integrated with an **SQLite database** for persistence.

---

## 🚀 Features
- Real-time face detection via OpenCV
- Face recognition & embeddings storage in SQLite
- Emotion analysis with DeepFace
- Auto-enroll new users when unknown faces appear
- Streamlit integration planned for assistant, weather API, news, and Gemini API

---

## 📂 Project Structure
capstone/
│── camera_app.py # Main app for webcam face & emotion detection
│── embeddings.py # Script to add face embeddings to DB
│── test_db.py # Quick DB test script
│── capstone.db # SQLite database (auto-created)
│── requirements.txt # Python dependencies
│── README.md # Project documentation
│── .gitignore # Ignored files/folders
│── venv/ # Virtual environment (not in repo)

```yaml
---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repo
```bash
git clone https://github.com/imAditya06/capstone.git
cd capstone
```
## 2️⃣ Create & activate virtual environment
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
# OR
source venv/bin/activate  # On Mac/Linux
```

## 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

## 4️⃣ Run the camera app
```bash
python camera_app.py
```

Press q to exit the webcam feed.

If an unknown face appears → it will prompt you to enter a name and auto-save the embedding.

## 🗄️ Database Info
We now use SQLite instead of MySQL:

Database file: capstone.db

Tables:

users → stores enrolled users
embeddings → stores face embeddings
emotions → stores detected emotions with timestamps

To inspect database contents:
```bash
sqlite3 capstone.db
sqlite> .tables
sqlite> SELECT * FROM users;
sqlite> SELECT * FROM emotions;

```
