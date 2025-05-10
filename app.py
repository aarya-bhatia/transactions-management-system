from flask import request, jsonify, session
from functools import wraps
from flask import Flask, request, render_template, redirect, g, jsonify
import os
import time
from parsers import DiscoverTransactionsReader, BiltMastercardTransactionsReader, AmericanExpressTransactionsReader, CapitalOneTransactionsReader, FidelityVisaTransactionsReader, BankOfAmerica, BankOfAmericaCCR
from summary import get_summary_stats, pivot_table_to_html, pivot_table_with_mean_and_sum
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
import urllib
import numpy as np
from scipy.interpolate import CubicSpline

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

# setup session
app.config['SECRET_KEY'] = '3592c963-c4f1-4446-a75a-479099a16cb9'

# account and parser config
accounts = [
    {"name": "discover", "parser": DiscoverTransactionsReader},
    {"name": "fidelity_visa", "parser": FidelityVisaTransactionsReader},
    {"name": "capital_one", "parser": CapitalOneTransactionsReader},
    {"name": "american_express", "parser": AmericanExpressTransactionsReader},
    {"name": "bilt_mastercard", "parser": BiltMastercardTransactionsReader},
    {"name": "bank_of_america", "parser": BankOfAmerica},
    {"name": "bank_of_america_CCR", "parser": BankOfAmericaCCR},
]

# define upload statuses
status_ready = "ready"
status_in_progress = "in_progress"
status_finished = "finished"
status_accepted = "accepted"

# create local upload dir
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD", "supersecret")


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


def requires_auth():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "authenticated" not in session or session["authenticated"] == False:
                session["next_url"] = request.url
                return redirect("/login")
            else:
                return f(*args, **kwargs)
        return wrapper
    return decorator


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


@app.route('/login', methods=["GET"])
def GET_login():
    return render_template("login.html"), 200


@app.route('/logout', methods=["GET"])
def GET_logout():
    session["authenticated"] = False
    session.clear()
    return render_template("login.html"), 200


@app.route('/login', methods=["POST"])
def POST_login():
    password = request.form["password"]
    if password != LOGIN_PASSWORD:
        return "Unauthorized", 400

    session["authenticated"] = True

    if "next_url" in session and session["next_url"]:
        next_url = session["next_url"]
        del session["next_url"]
        return redirect(next_url)

    return "", 200


@app.route('/')
@requires_auth()
def GET_index():
    uploads = connection.find()
    return render_template('index.html', uploads=uploads, accounts=accounts)


@app.route('/transactions')
@requires_auth()
def GET_transactions():
    return render_template('view-transactions.html', transactions=get_all_transactions())


@app.route('/categories/<path:category>')
@requires_auth()
def GET_transactions_by_category(category):
    print("Search for category: ", category)
    ts = []
    for row in connection.find({"transactions.category": category}):
        for t in row["transactions"]:
            if t["category"] == category:
                ts.append(t)

    return jsonify({"transactions": ts})


@app.route('/rename-category')
@requires_auth()
def GET_rename_category_transactions():
    from_name = request.args.get("from")
    to_name = request.args.get("to")
    if not from_name or not to_name:
        return "", 400

    print(f"Rename category from '{from_name}' to '{to_name}'")
    result = connection.update_many({"transactions.category": from_name}, {"$set": {
                                    "transactions.$[elem].category": to_name}}, array_filters=[{"elem.category": from_name}])
    print(result)
    return "", 200


@app.route('/delete_upload/<upload_id>', methods=['GET'])
@requires_auth()
@check_and_load_upload()
def GET_delete_upload(upload_id):
    if os.path.exists(g.upload["file_path"]):
        os.remove(g.upload["file_path"])
    count = connection.delete_one({"_id": ObjectId(upload_id)}).deleted_count
    print(f"delete {count} uploads")
    return redirect('/')


@app.route('/upload_file', methods=['POST'])
@requires_auth()
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
@requires_auth()
@check_and_load_upload()
def GET_upload(upload_id):
    upload = g.upload
    return jsonify(upload)


@app.route('/process_transactions/<upload_id>')
@requires_auth()
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
@requires_auth()
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
@requires_auth()
@check_and_load_upload()
def GET_accept_transactions(upload_id):
    upload = g.upload
    if upload["status"] != status_finished:
        return "Illegal", 400

    set_upload_status(g.upload, status_accepted)
    return "", 200


@app.route("/discard_transactions/<upload_id>")
@requires_auth()
@check_and_load_upload()
def GET_discard_transactions(upload_id):
    upload = g.upload
    if upload["status"] != status_finished:
        return "Illegal", 400
    set_upload_status(g.upload, status_ready)
    return "", 200


@app.route("/summary")
@requires_auth()
def GET_summary():
    transactions = get_all_transactions()
    print("computing stats...")
    stats = get_summary_stats(transactions)
    pivot_table = stats["pivot_table"]
    pivot_table = pivot_table.transpose()
    pivot_table = pivot_table_with_mean_and_sum(pivoted=pivot_table)

    cols = pivot_table.columns.tolist()
    new_order = reversed(cols)
    pivot_table = pivot_table[new_order]

    table_html = pivot_table_to_html(pivot_table)
    return render_template("summary.html", stats=stats, table_html=table_html), 200


@app.route("/get-chart-data")
@requires_auth()
def GET_get_chart_data():
    transactions = get_all_transactions()
    stats = get_summary_stats(transactions)
    pivoted = stats["pivot_table"]

    # Step 2: Combine categories using a dictionary
    category_groups = {
        'food': ['groceries', 'dining', 'drug store'],
        'leisure': ['entertainment', 'shopping', 'friends', 'travel', 'family/friends'],
        'income': ['paycheck', 'interest', 'rewards', 'refund'],
        'housing': ['rent', 'household'],
    }

    for new_cat, old_cats in category_groups.items():
        # Sum across all matching old categories (use .get to avoid KeyErrors)
        pivoted[new_cat] = pivoted[old_cats].sum(axis=1)

    flattened_old = [cat for group in category_groups.values()
                     for cat in group]
    pivoted.drop(
        columns=[c for c in flattened_old if c in pivoted.columns], inplace=True)

    # Step 3: Drop unwanted categories
    categories_to_drop = ['Total', 'Avg', 'card payment', 'initial balance']
    pivoted.drop(
        columns=[c for c in categories_to_drop if c in pivoted.columns], inplace=True)

    # Step 4: Drop unwanted months (e.g., first 3)
    pivoted = pivoted.iloc[:-2]
    pivoted_logged = pivoted.map(lambda x: np.sign(x) * np.log1p(abs(x)))

    labels = pivoted.index.tolist()
    datasets = [
        {
            'label': category,
            # 'data': pivoted[category].tolist(),
            'data': pivoted_logged[category].tolist(),
        }
        for category in pivoted.columns
    ]

    x = np.arange(len(pivoted))  # x = months (or time axis)
    smoothed_datasets = []

    for category in pivoted.columns:
        y = pivoted_logged[category].values
        cs = CubicSpline(x, y)

        # Smooth the curve with 500 points
        x_smooth = np.linspace(0, len(pivoted)-1, 60)
        y_smooth = cs(x_smooth)

        smoothed_datasets.append({
            'label': category,
            'data': y_smooth.tolist()  # Convert the smoothed data to list for JSON
        })

    return jsonify({'labels': labels, 'datasets': datasets, 'smoothed_datasets': smoothed_datasets})


@app.route("/plot")
@requires_auth()
def GET_plot():
    return render_template("plot.html"), 200


if __name__ == '__main__':
    app.run(debug=True)
