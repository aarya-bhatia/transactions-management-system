from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()


UPLOAD_DIR = os.environ.get("UPLOAD_DIR")
DB_PATH = os.environ.get("DB_PATH")

if not all([UPLOAD_DIR, DB_PATH]):
    print("env variable is missing.")
    exit(1)

accounts = ["discover", "fidelity_visa", "capital_one",
            "bank_of_america", "american_express"]
