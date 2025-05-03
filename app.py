from flask import Flask, jsonify, request, render_template, redirect
import os
import time
from flask import session
from dotenv import load_dotenv
from datetime import datetime
import sqlite3

load_dotenv()

app = Flask(__name__)

UPLOAD_DIR = os.environ.get("UPLOAD_DIR")
DB_PATH = os.environ.get("DB_PATH")

if not all([UPLOAD_DIR, DB_PATH]):
    print("missing env variable")
    exit(1)

accounts = ["discover", "fidelity_visa", "capital_one",
            "bank_of_america", "american_express"]


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


def get_uploads():
    db_connection = sqlite3.connect(DB_PATH)
    cursor = db_connection.cursor()
    cursor.execute('SELECT account_name, file_path, created_at FROM uploads')
    rows = cursor.fetchall()
    db_connection.close()

    uploads = [{"account_name": row[0], "file_path": row[1],
                "created_at": row[2]} for row in rows]
    return uploads


def add_upload(account_name, file_path, client_ip):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO uploads (account_name, file_path, client_ip)
        VALUES (?, ?, ?)
    ''', (account_name, file_path, client_ip))
    conn.commit()
    conn.close()


@app.route('/')
def index():
    return render_template('index.html', uploads=get_uploads(), accounts=accounts)


# handle new file upload
@app.route('/upload_file', methods=['POST'])
def upload_file():
    file = request.files['uploaded_file']

    if not file or file.filename == '':
        return "No file selected", 400

    user_filename = request.form.get('user_filename')
    if not user_filename:
        user_filename = file.filename

    account_name = request.form.get("account_name")
    if not account_name:
        return "account name does not exist", 400

    timestamp = time.strftime("%Y-%m-%d")
    user_filename = user_filename.strip().lower().replace(' ', '_')
    filename = f"{timestamp}_{user_filename}.csv"
    file_path = os.path.join(UPLOAD_DIR, filename)

    if os.path.exists(file_path):
        return "file name is taken: " + file_path, 400

    try:
        file.save(file_path)
        add_upload(account_name, file_path, request.remote_addr)
        print(f"file uploaded successfully: " + file_path)
        return jsonify({"message": "File uploaded successfully", "file_path": file_path}), 200

    except Exception as e:
        print(e)
        return "File not saved.", 500


if __name__ == '__main__':
    app.run(debug=True)
