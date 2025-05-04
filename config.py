from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()


UPLOAD_DIR = os.environ.get("UPLOAD_DIR")
DEV_DB_PATH = os.environ.get("DEV_DB_PATH")
PROD_DB_PATH = os.environ.get("PROD_DB_PATH")
STAGE = os.environ.get("STAGE", "DEVELOPMENT")

if STAGE == "PRODUCTION":
    DB_PATH = PROD_DB_PATH
else:
    DB_PATH = DEV_DB_PATH

if not all([UPLOAD_DIR, DB_PATH]):
    print("env variable is missing.")
    exit(1)

accounts = ["discover", "fidelity_visa", "capital_one",
            "bank_of_america", "american_express", "bilt_mastercard"]
