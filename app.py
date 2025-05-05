from flask import Flask, request, render_template, redirect, g
import os
import time
from config import accounts, UPLOAD_DIR, DB_PATH
from uploads import get_uploads, delete_upload, upload_exists, add_upload, get_upload, update_upload_status, ProcessingStatus
from parsers import DiscoverTransactionsReader, BiltMastercardTransactionsReader, AmericanExpressTransactionsReader, CapitalOneTransactionsReader, FidelityVisaTransactionsReader
from dao import save_transactions, get_transactions
from database import init_tables
import sqlite3

app = Flask(__name__)

pending_transactions = {}

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

init_tables()


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # Optional: makes rows behave like dicts
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.route('/')
def GET_index():
    db = get_db()
    return render_template('index.html', uploads=get_uploads(db), accounts=accounts)


@app.route('/transactions')
def GET_transactions():
    db = get_db()
    return render_template('view-transactions.html', transactions=get_transactions(db))


@app.route('/delete_upload/<int:id>', methods=['GET'])
def GET_delete_upload(id):
    db = get_db()
    try:
        upload = get_upload(db, id)
        if not upload:
            return "Upload not found", 400

        os.remove(upload["file_path"])
        delete_upload(db, id)
        return redirect('/')
    except Exception as e:
        print(e)
        return "Failed to delete upload.", 500


@app.route('/upload_file', methods=['POST'])
def POST_upload_file():
    db = get_db()
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

    # Check if file_path already exists in the database
    if upload_exists(db, file_path):
        return "File already exists in the database", 400

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        file.save(file_path)
        print(f"file uploaded successfully: " + file_path)
        add_upload(db, account_name, file_path)
        return redirect('/')

    except Exception as e:
        print(e)
        return "File not saved.", 500


@app.route('/process_transactions/<int:upload_id>')
def GET_process_transactions(upload_id):
    db = get_db()
    upload = get_upload(db, upload_id)
    if not upload:
        return "upload does not exist", 400
    print(upload)
    if upload["status"] != ProcessingStatus.READY.value:
        return "Already processed", 200

    print("processing upload: ", upload)
    if not upload:
        return "upload does not exist", 400

    if not os.path.exists(upload["file_path"]):
        return "uploaded file not found", 500

    update_upload_status(db, upload_id, ProcessingStatus.IN_PROGRESS)

    with open(upload["file_path"], "r") as file:
        if upload["account_name"] == "discover":
            reader = DiscoverTransactionsReader()
        elif upload["account_name"] == "capital_one":
            reader = CapitalOneTransactionsReader()
        elif upload["account_name"] == "fidelity_visa":
            reader = FidelityVisaTransactionsReader()
        elif upload["account_name"] == "american_express":
            reader = AmericanExpressTransactionsReader()
        elif upload["account_name"] == "bilt_mastercard":
            reader = BiltMastercardTransactionsReader()
        else:
            reader = None

        if reader:
            print("start processing")
            transactions = reader.read_file(file)

            update_upload_status(db, upload_id, ProcessingStatus.FINISHED)

            for t in transactions:
                t.account_name = upload["account_name"]
                t.file_path = upload["file_path"]

            pending_transactions[upload_id] = transactions
            transactions_serialized = [t.to_dict() for t in transactions]

            return render_template("confirm-transactions-page.html", transactions=transactions_serialized, file_id=upload_id), 200

        return "No parser found for " + upload["account_name"], 500


@app.route("/view_transactions/<int:upload_id>")
def GET_view_transactions(upload_id):
    db = get_db()
    upload = get_upload(db, upload_id)
    if not upload:
        return "upload does not exist", 400

    if upload_id not in pending_transactions:  # this can happen if the app was restarted and state was lost
        return f"Transactions not found. Please reset status at {request.host_url}reset_upload_status/{upload_id}", 400

    transactions = pending_transactions[upload_id]
    transactions_serialized = [t.to_dict() for t in transactions]
    return render_template("confirm-transactions-page.html", transactions=transactions_serialized, file_id=upload_id), 200


@app.route("/reset_upload_status/<int:upload_id>")
def GET_reset_upload_status(upload_id):
    db = get_db()
    upload = get_upload(db, upload_id)
    if not upload:
        return "upload does not exist", 400

    if upload["status"] == ProcessingStatus.READY.value:
        return "", 200
    if upload["status"] == ProcessingStatus.ACCEPTED.value:
        return "unable to reset", 400
    if upload["status"] == ProcessingStatus.FINISHED.value:
        update_upload_status(db, upload_id, ProcessingStatus.READY)
        return "", 200
    if upload["status"] == ProcessingStatus.IN_PROGRESS.value:
        return "try again later", 400

    return "", 500


@app.route("/accept_transactions/<int:upload_id>")
def GET_accept_transactions(upload_id):
    db = get_db()

    if upload_id not in pending_transactions:  # this can happen if the app was restarted and state was lost
        return f"Transactions not found. Please reset status at {request.base_url}/reset_upload_status/{upload_id}", 400

    upload = get_upload(db, upload_id)
    if not upload:
        return "upload does not exist", 400

    if upload["status"] != ProcessingStatus.FINISHED.value:
        return "invalid state", 400

    transactions = pending_transactions[upload_id]
    save_transactions(db, transactions)
    update_upload_status(db, upload_id, ProcessingStatus.ACCEPTED)
    del pending_transactions[upload_id]
    return "", 200


@app.route("/discard_transactions/<int:upload_id>")
def GET_discard_transactions(upload_id):
    db = get_db()
    if upload_id in pending_transactions:
        update_upload_status(db, upload_id, ProcessingStatus.READY)
        del pending_transactions[upload_id]
    return "", 200


if __name__ == '__main__':
    app.run(debug=True)
