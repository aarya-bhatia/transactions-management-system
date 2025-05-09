from typing import TextIO
from bson.objectid import ObjectId
import pandas as pd
from datetime import datetime

date_formats = ["%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"]

DEFAULT_CATEGORY = "uncategorised"


class TransactionReader:
    def read_file(self, file: TextIO) -> list[dict]:
        df = pd.read_csv(file)
        df["id"] = df.apply(lambda _: ObjectId())
        df.columns = df.columns.str.lower()
        self.format_data(df)
        if "category" not in df.columns:
            df["category"] = DEFAULT_CATEGORY
        df["category"] = df["category"].str.lower()
        return df[["date", "amount", "description", "category"]].to_dict(orient='records')

    def format_data(self, df: pd.DataFrame) -> any:
        return None


def invert(amount):
    return -amount


def get_type(amount):
    return "DEBIT" if amount < 0 else "CREDIT"


def format_date(date_str):
    for fmt in date_formats:
        try:
            d = datetime.strptime(date_str, fmt)
            return d.strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Date format not recognized: {date_str}")


class DiscoverTransactionsReader(TransactionReader):
    def format_data(self, df):
        df["date"] = df.iloc[:, 0].apply(format_date)
        df["description"] = df.iloc[:, 2]
        df["amount"] = df.iloc[:, 3].apply(float).apply(invert)


class CapitalOneTransactionsReader(TransactionReader):
    def format_data(self, df):
        df["date"] = df.iloc[:, 2].apply(format_date)
        df["description"] = df.iloc[:, 1]
        df["amount"] = df.iloc[:, 4].apply(float)
        df["type"] = df.iloc[:, 3].apply(lambda v: 1 if v == "Credit" else -1)
        df["amount"] *= df["type"]


class BiltMastercardTransactionsReader(TransactionReader):
    def format_data(self, df):
        df["date"] = df.iloc[:, 0].apply(format_date)
        df["description"] = df.iloc[:, 4]
        df["amount"] = df.iloc[:, 1].apply(float)


class AmericanExpressTransactionsReader(TransactionReader):
    def format_data(self, df):
        df["date"] = df.iloc[:, 0].apply(format_date)
        df["description"] = df.iloc[:, 1]
        df["amount"] = df.iloc[:, 2].apply(float).apply(invert)


class FidelityVisaTransactionsReader(TransactionReader):
    def format_data(self, df):
        df["date"] = df.iloc[:, 0].apply(format_date)
        df["description"] = df.iloc[:, 2]
        df["amount"] = df.iloc[:, 4].apply(float)


class BankOfAmerica(TransactionReader):
    def format_data(self, df):
        df["date"] = df.iloc[:, 0].apply(format_date)
        df["description"] = df.iloc[:, 1]
        df["amount"] = df.iloc[:, 2].apply(float)

class BankOfAmericaCCR(TransactionReader):
    def format_data(self, df):
        df["date"] = df.iloc[:, 0].apply(format_date)
        df["description"] = df.iloc[:, 2]
        df["amount"] = df.iloc[:, 4].apply(float)
