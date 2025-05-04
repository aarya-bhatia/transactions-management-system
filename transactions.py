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


@dataclass
class TransactionReaderColumns:
    date_column: int
    description_column: int
    amount_column: int
    category_column: int


class TransactionReader:
    def __init__(self, column_info_parser: Callable[[list[str]], TransactionReaderColumns], date_parser: Callable[[str], datetime.date], type_parser: Callable[[float], TransactionType]):
        self.column_info_parser = column_info_parser
        self.date_parser = date_parser
        self.type_parser = type_parser
        self.failed_row_count = 0
        self.total_row_count = 0

    def read_file(self, file: TextIO) -> list[Transaction]:
        result = []
        csv_reader = csv.reader(file)

        try:
            column_info = self.column_info_parser(next(csv_reader))
        except StopIteration:
            return []

        for row in csv_reader:
            transaction = self._parse_row(column_info, row)
            if transaction:
                result.append(transaction)
            else:
                self.failed_row_count += 1

            self.total_row_count += 1

        return result

    def _parse_row(self, column_info: TransactionReaderColumns, row: list[str]) -> Union[Transaction, None]:
        try:
            try:
                date_str = row[column_info.date_column]
                amount_str = row[column_info.amount_column]
                description = row[column_info.description_column]
                category = row[column_info.category_column] if column_info.category_column < len(
                    row) else DEFAULT_CATEGORY
            except IndexError:
                return None

            amount = float(amount_str)
            date = self.date_parser(date_str)
            type = self.type_parser(amount)
            amount = abs(amount)

            return Transaction(
                amount=amount,
                date=date,
                description=description,
                type=type,
                category=category or DEFAULT_CATEGORY
            )
        except ValueError:
            return None


class DiscoverTransactionsReader:

    def __init__(self, file):
        self.file = file
        self.reader = TransactionReader(column_info_parser=DiscoverTransactionsReader.column_info_parser,
                                        date_parser=DiscoverTransactionsReader.date_parser, type_parser=DiscoverTransactionsReader.type_parser)

    def date_parser(date_str: str) -> datetime.date:
        return datetime.strptime(date_str, "%m/%d/%Y")

    def type_parser(amount: float) -> TransactionType:
        if amount < 0:
            return TransactionType.CREDIT
        else:
            return TransactionType.DEBIT

    def column_info_parser(headers: list[str]) -> TransactionReaderColumns:
        return TransactionReaderColumns(
            date_column=0, description_column=2, amount_column=3, category_column=5)

    def get_transactions(self) -> list[Transaction]:
        return self.reader.read_file(self.file)


def transactions_as_dict(transactions: list[Transaction]) -> list[any]:
    result = []

    for t in transactions:
        row = {
            "date": t.date.strftime("%Y-%m-%d"),
            "description": t.description,
            "type": t.type.name,
            "amount": f"${t.amount:.2f}",
            "category": t.category
        }

        result.append(row)

    return result
