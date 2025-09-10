# Capstone Project - Emotion Recognition with Face Logging

## 📌 Overview
This project is a part of our multimodal AI assistant system.  
It uses **DeepFace**, **OpenCV**, and **MySQL** to:

- Recognize faces from a webcam feed  
- Detect emotions in real time  
- Store results (face embeddings + emotions) in a MySQL database  
- Log unknown users automatically  

Built with **Python 3.12**, managed in a **virtual environment**, and designed to integrate with a larger **Streamlit-based AI system**.

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/imAditya06/capstone.git
cd capstone

# Create venv
python -m venv venv

# Activate venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

# MYSQL SETUP
-- Create the database
CREATE DATABASE IF NOT EXISTS emotion_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a dedicated user
CREATE USER IF NOT EXISTS 'emotion_user'@'localhost' IDENTIFIED BY 'YourStrongPassword';

-- Grant privileges
GRANT ALL PRIVILEGES ON emotion_db.* TO 'emotion_user'@'localhost';
FLUSH PRIVILEGES;

# Create a .env file in the project root with:
DB_USER=emotion_user
DB_PASS=YourStrongPassword
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=emotion_db
POOL_NAME=emotion_pool
POOL_SIZE=5

# Running the Project
python build_embeddings.py
python camera_app.py

# Viewing results in Mysql

USE emotion_db;
SELECT * FROM logs;
SELECT * FROM users;
SELECT * FROM emotions;


