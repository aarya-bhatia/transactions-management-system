from database import get_connection
from transactions import Transaction


def get_transactions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT file_path, account_name, date, description, type, amount, category
            FROM transactions 
                   ''')

    rows = cursor.fetchall()
    t = []
    for r in rows:
        t.append({
            "file_path": r[0],
            "account_name": r[1],
            "date": r[2],
            "description": r[3],
            "type": r[4],
            "amount": r[5],
            "category": r[6],
        })

    conn.commit()
    conn.close()
    return t


def save_transactions(transactions: list[Transaction]):
    if not transactions:
        return

    conn = get_connection()
    cursor = conn.cursor()

    for transaction in transactions:
        cursor.execute('''
            INSERT INTO transactions (file_path, account_name, date, description, type, amount, category)
            VALUES (:file_path, :account_name, :date, :description, :type, :amount, :category)
            ''', transaction.to_dict())

    conn.commit()
    conn.close()
