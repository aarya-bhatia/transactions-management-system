from flask import Flask, jsonify, request, render_template, redirect
import os
import time
from flask import session
from dotenv import load_dotenv
from datetime import datetime
from config import accounts, UPLOAD_DIR
from uploads import get_uploads, delete_upload, upload_exists, add_upload

app = Flask(__name__)


@app.route('/')
def GET_index():
    return render_template('index.html', uploads=get_uploads(), accounts=accounts)


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


if __name__ == '__main__':
    app.run(debug=True)
