import sqlite3
from config import DB_PATH, UPLOAD_DIR
import os
from database import get_connection


def get_uploads():
    db_connection = sqlite3.connect(DB_PATH)
    cursor = db_connection.cursor()
    cursor.execute(
        'SELECT id, account_name, file_path, created_at FROM uploads')
    rows = cursor.fetchall()
    db_connection.close()

    uploads = [{"id": row[0], "account_name": row[1], "file_path": row[2],
                "created_at": row[3]} for row in rows]

    uploads = [upload for upload in uploads if os.path.exists(
        upload["file_path"])]

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


def upload_exists(file_path):
    # Check if file_path already exists in the database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT COUNT(*) FROM uploads WHERE file_path = ?', (file_path,))
    ans = cursor.fetchone()[0] > 0
    conn.close()
    return ans


def get_upload(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, account_name, file_path, created_at FROM uploads WHERE id=?', (id,))
    ans = cursor.fetchone()
    conn.close()
    return {
        "id": ans[0],
        "account_name": ans[1],
        "file_path": ans[2],
        "created_at": ans[3]
    }


def delete_upload(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM uploads WHERE id = ?', (id,))
    conn.commit()
    conn.close()
