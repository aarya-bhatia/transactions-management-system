from flask import Flask, jsonify, request, render_template, redirect
import os
import time
from config import accounts, UPLOAD_DIR
from uploads import get_uploads, delete_upload, upload_exists, add_upload, get_upload
from transactions import DiscoverTransactionsReader, transactions_as_dict
from dao import save_transactions, get_transactions

app = Flask(__name__)

pending_transactions = {}


@app.route('/')
def GET_index():
    return render_template('index.html', uploads=get_uploads(), accounts=accounts)


@app.route('/transactions')
def GET_transactions():
    return render_template('view-transactions.html', transactions=get_transactions())


@app.route('/delete_upload/<int:id>', methods=['GET'])
def GET_delete_upload(id):
    try:
        delete_upload(id)

        return redirect('/')
    except Exception as e:
        print(e)
        return "Failed to delete upload.", 500


@app.route('/upload_file', methods=['POST'])
def POST_upload_file():
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
    if upload_exists(file_path):
        return "File already exists in the database", 400

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        file.save(file_path)
        print(f"file uploaded successfully: " + file_path)
        add_upload(account_name, file_path, request.remote_addr)
        return redirect('/')

    except Exception as e:
        print(e)
        return "File not saved.", 500


@app.route('/process_transactions/<int:upload_id>')
def GET_process_transactions(upload_id):
    upload = get_upload(upload_id)
    print("processing upload: ", upload)
    if not upload:
        return "upload does not exist", 400

    if not os.path.exists(upload["file_path"]):
        return "uploaded file not found", 500

    with open(upload["file_path"], "r") as file:
        if upload["account_name"] == "discover":
            reader = DiscoverTransactionsReader(file)
            transactions = reader.get_transactions()
            transactions = transactions_as_dict(transactions)
            for row in transactions:
                row["account_name"] = upload["account_name"]
                row["file_path"] = upload["file_path"]
            pending_transactions[upload_id] = transactions
            return render_template("confirm-transactions-page.html", transactions=transactions, file_id=upload_id), 200
        else:
            return "no available parsers for account: " + upload["account_name"], 500


@app.route("/accept_transactions/<int:upload_id>")
def GET_accept_transactions(upload_id):
    if upload_id not in pending_transactions:
        return "", 400

    transactions = pending_transactions[upload_id]
    save_transactions(transactions)
    del pending_transactions[upload_id]
    return "", 200


@app.route("/discard_transactions/<int:upload_id>")
def GET_discard_transactions(upload_id):
    if upload_id in pending_transactions:
        del pending_transactions[upload_id]
    return "", 200


if __name__ == '__main__':
    app.run(debug=True)
