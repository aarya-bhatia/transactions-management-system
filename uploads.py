from enum import Enum


class ProcessingStatus(Enum):
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    ACCEPTED = "ACCEPTED"


def update_upload_status(db, upload_id, status: ProcessingStatus):
    db.execute("UPDATE uploads SET status=? WHERE id=?",
               (status.name, upload_id))
    db.commit()


def get_uploads(db):
    rows = db.execute('SELECT * FROM uploads').fetchall()
    uploads = [dict(row) for row in rows]
    return uploads


def add_upload(db, account_name, file_path):
    db.execute('''INSERT INTO uploads (account_name, file_path, status) VALUES (?, ?, ?)''',
               (account_name, file_path, "READY"))
    db.commit()


def upload_exists(db, file_path):
    row = db.execute(
        'SELECT COUNT(*) FROM uploads WHERE file_path = ?', (file_path,)).fetchone()
    return row[0] > 0


def get_upload(db, id):
    row = db.execute('SELECT * FROM uploads WHERE id=?', (id,)).fetchone()
    return dict(row) if row else None


def delete_upload(db, id):
    upload = get_upload(db, id)
    db.execute('DELETE FROM transactions WHERE file_path = ? AND account_name = ?',
               (upload["file_path"], upload["account_name"]))
    db.execute('DELETE FROM uploads WHERE id = ?', (id,))
    db.commit()
