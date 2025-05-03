import sqlite3
from config import DB_PATH, UPLOAD_DIR
import os


def get_connection():
    return sqlite3.connect(DB_PATH)


def init():
    print("Initializing db connection...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                client_ip TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
        print("Failed to connect to database.")
        exit(1)

    # create uploads dir
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    if os.environ.get("STAGE", "") == "DEVELOPMENT":
        print("Development mode is on")


init()
