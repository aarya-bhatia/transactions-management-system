import os
import sqlite3
from config import DB_PATH, STAGE

# Ensure the directory for the database exists
if os.path.dirname(DB_PATH):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_tables():
    print("Initializing db connection...")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if STAGE == "DEVELOPMENT":
            print("dropping tables.")
            # cursor.execute('DROP TABLE IF EXISTS uploads')
            # cursor.execute('DROP TABLE IF EXISTS transactions')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT READY
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                account_name TEXT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                type TEXT CHECK(type IN ('DEBIT', 'CREDIT')) NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
        print("Failed to connect to database.")
        exit(1)
