from flask import request, jsonify
from functools import wraps
from flask import Flask, request, render_template, redirect, g, jsonify
import os
import time
from parsers import DiscoverTransactionsReader, BiltMastercardTransactionsReader, AmericanExpressTransactionsReader, CapitalOneTransactionsReader, FidelityVisaTransactionsReader, BankOfAmerica, BankOfAmericaCCR
from summary import get_summary_stats, draw_plots
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

UPLOAD_DIR = os.environ.get("UPLOAD_DIR")
STAGE = os.environ.get("STAGE", "DEVELOPMENT")

# Configure MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "transactions_db")

# Connect to MongoDB
db = MongoClient(MONGO_URI)[DB_NAME]
connection = db.uploads

# Create Flask app
app = Flask(__name__)

accounts = [
    {"name": "discover", "parser": DiscoverTransactionsReader},
    {"name": "fidelity_visa", "parser": FidelityVisaTransactionsReader},
    {"name": "capital_one", "parser": CapitalOneTransactionsReader},
    {"name": "american_express", "parser": AmericanExpressTransactionsReader},
    {"name": "bilt_mastercard", "parser": BiltMastercardTransactionsReader},
    {"name": "bank_of_america", "parser": BankOfAmerica},
    {"name": "bank_of_america_CCR", "parser": BankOfAmericaCCR},
]

status_ready = "ready"
status_in_progress = "in_progress"
status_finished = "finished"
status_accepted = "accepted"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


def set_upload_status(upload, status):
    result = connection.update_one(
        {"_id": ObjectId(upload["_id"])},
        {"$set": {
            "status": status
        }}
    )

    if result.modified_count > 0:
        upload["status"] = status
        print(f"upload {upload['_id']} status changed to {status}")
        return True

    return False


def get_all_transactions():
    uploads = connection.find()
    transactions = []
    for upload in uploads:
        ts = upload["transactions"]
        for t in ts:
            t["account_name"] = upload["account_name"]

        transactions.extend(ts)

    return transactions


def upload_file(file_blob, file_path, account_name):
    if os.path.exists(file_path):
        os.remove(file_path)

    file_blob.save(file_path)

    connection.insert_one({
        "account_name": account_name,
        "file_path": file_path,
        "status": status_ready,
        "transactions": []
    })

    print(f"uploaded completed: " + file_path)


def process_transactions(upload):
    try:
        set_upload_status(upload, status_in_progress)

        reader = None
        with open(upload["file_path"], "r") as file:
            for account in accounts:
                if account["name"] == upload["account_name"]:
                    if not account["parser"]:
                        raise Exception(
                            "Parser not available for " + upload["account_name"])
                    reader = account["parser"]()
                    break

            if not reader:
                raise Exception("Account not found: " + upload["account_name"])

            print("start processing")

            transactions = reader.read_file(file)
            connection.update_one({"_id": ObjectId(upload["_id"])},
                                  {"$set": {
                                      "status": status_finished,
                                      "transactions": transactions,
                                  }})

            return transactions

    except Exception as e:
        print(e)
        set_upload_status(upload, status_ready)
        return None


def validate_fields(required_fields):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON payload"}), 400

            missing = [field for field in required_fields if field not in data]
            if missing:
                return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

            return f(*args, **kwargs)
        return wrapper
    return decorator


def check_and_load_upload():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            upload_id = kwargs.get("upload_id")
            upload = connection.find_one({"_id": ObjectId(upload_id)})
            if not upload:
                return jsonify({"error": f"Invalid upload ID: {upload_id}"}), 400
            g.upload = upload
            upload["_id"] = str(upload["_id"])
            print(f"Fetched upload object: {upload}")
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/')
def GET_index():
    uploads = connection.find()
    return render_template('index.html', uploads=uploads, accounts=accounts)


@app.route('/transactions')
def GET_transactions():
    return render_template('view-transactions.html', transactions=get_all_transactions())


@app.route('/delete_upload/<upload_id>', methods=['GET'])
@check_and_load_upload()
def GET_delete_upload(upload_id):
    if os.path.exists(g.upload["file_path"]):
        os.remove(g.upload["file_path"])
    count = connection.delete_one({"_id": ObjectId(upload_id)}).deleted_count
    print(f"delete {count} uploads")
    return redirect('/')


@app.route('/upload_file', methods=['POST'])
def POST_upload_file():
    file = request.files['uploaded_file']
    if not file or file.filename == '':
        return "No file selected", 400

    account_name = request.form.get("account_name")
    if not account_name:
        return "account name does not exist", 400

    timestamp = time.strftime("%Y-%m-%d")
    filename = file.filename.strip().lower().replace(' ', '_')
    filename = f"{timestamp}_{filename}"
    filename = filename.replace("_-_", "-")
    file_path = os.path.join(UPLOAD_DIR, filename)

    if connection.find_one({"file_path": file_path}):
        return "File path conflict", 400

    upload_file(file, file_path, account_name)
    return redirect('/')


@app.route('/uploads/<upload_id>')
@check_and_load_upload()
def GET_upload(upload_id):
    upload = g.upload
    return jsonify(upload)


@app.route('/process_transactions/<upload_id>')
@check_and_load_upload()
def GET_process_transactions(upload_id):
    upload = g.upload
    if upload["status"] == status_in_progress:
        return "in progress", 200

    print("processing upload: ", upload)
    transactions = process_transactions(upload)
    upload["transactions"] = transactions
    if not transactions:
        return "Failure", 500

    return jsonify({
        "upload": upload
    })


@app.route("/reset_upload_status/<upload_id>")
@check_and_load_upload()
def GET_reset_upload_status(upload_id):
    upload = g.upload
    if upload["status"] == status_ready:
        return "", 200
    if upload["status"] == status_accepted:
        return "Illegal", 400
    if upload["status"] == status_finished:
        set_upload_status(upload, status_ready)
    if upload["status"] == status_in_progress:
        return "Upload is in progress. Try again later", 400

    return "", 500


@app.route("/accept_transactions/<upload_id>")
@check_and_load_upload()
def GET_accept_transactions(upload_id):
    upload = g.upload
    if upload["status"] != status_finished:
        return "Illegal", 400

    set_upload_status(g.upload, status_accepted)
    return "", 200


@app.route("/discard_transactions/<upload_id>")
@check_and_load_upload()
def GET_discard_transactions(upload_id):
    upload = g.upload
    if upload["status"] != status_finished:
        return "Illegal", 400
    set_upload_status(g.upload, status_ready)
    return "", 200


@app.route("/summary")
def GET_summary():
    transactions = get_all_transactions()
    print("computing stats...")
    stats = get_summary_stats(transactions)
    # print("drawing plots...")
    # draw_plots(stats)
    return render_template("summary.html", stats=stats), 200


if __name__ == '__main__':
    app.run(debug=True)
