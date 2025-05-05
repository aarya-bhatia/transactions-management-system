import csv
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import TextIO, Callable, Union

DEFAULT_CATEGORY = "uncategorised"


class TransactionType(Enum):
    UNKNOWN = "UNKNOWN"
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


@dataclass
class Transaction:
    date: datetime.date
    description: str
    type: TransactionType
    amount: float
    category: str
    account_name: str
    file_path: str

    def to_dict(self) -> dict:
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "description": self.description,
            "type": self.type.name,
            "amount": self.amount,
            "category": self.category,
            "account_name": self.account_name,
            "file_path": self.file_path
        }


class TransactionReader:
    def __init__(self):
        self.failed_row_count = 0
        self.total_row_count = 0

    def read_file(self, file: TextIO) -> list[Transaction]:
        result = []
        csv_reader = csv.reader(file)

        try:
            next(csv_reader)  # skip header
        except StopIteration:
            return []

        for row in csv_reader:
            transaction = self.parse_row(row)
            if transaction:
                result.append(transaction)
            else:
                self.failed_row_count += 1

            self.total_row_count += 1

        return result

    def parse_row(self, row: list[str]) -> Union[Transaction, None]:
        return None
