from database import get_connection


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


def save_transactions(transactions):
    if not transactions:
        return

    conn = get_connection()
    cursor = conn.cursor()

    for transaction in transactions:
        file_path = transaction["file_path"]
        account_name = transaction["account_name"]
        date = transaction["date"]
        description = transaction["description"]
        type = transaction["type"]
        amount = transaction["amount"]
        category = transaction["category"]

        cursor.execute('''
            INSERT INTO transactions (file_path, account_name, date, description, type, amount, category)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ''',
                       (file_path, account_name, date, description, type, amount, category))

    conn.commit()
    conn.close()
