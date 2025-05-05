from transactions import Transaction


def get_transactions(db):
    rows = db.execute('SELECT * FROM transactions').fetchall()
    return [dict(row) for row in rows]


def save_transactions(db, transactions: list[Transaction]):
    if not transactions:
        return

    cursor = db.cursor()

    for transaction in transactions:
        cursor.execute('''
            INSERT INTO transactions (file_path, account_name, date, description, type, amount, category)
            VALUES (:file_path, :account_name, :date, :description, :type, :amount, :category)
            ''', transaction.to_dict())
