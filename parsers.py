from datetime import datetime
from transactions import Transaction, TransactionReader, DEFAULT_CATEGORY, TransactionType


class DiscoverTransactionsReader(TransactionReader):
    def parse_row(self, row: list[str]) -> Transaction:
        return Transaction(
            date=datetime.strptime(row[0], "%m/%d/%Y"),
            description=row[2],
            amount=abs(float(row[3])),
            category=row[5] if 5 < len(row) else DEFAULT_CATEGORY,
            type=TransactionType.CREDIT if float(
                row[3]) < 0 else TransactionType.DEBIT,
            file_path="",
            account_name=""
        )


class CapitalOneTransactionsReader(TransactionReader):
    def parse_row(self, row: list[str]) -> Transaction:
        return Transaction(
            date=datetime.strptime(row[2], "%m/%d/%y"),
            description=row[1],
            amount=abs(float(row[4])),
            category=row[6] if 6 < len(row) else DEFAULT_CATEGORY,
            type=TransactionType.CREDIT if row[3] == "Credit" else TransactionType.DEBIT,
            file_path="",
            account_name=""
        )


class BiltMastercardTransactionsReader(TransactionReader):
    def parse_row(self, row: list[str]) -> Transaction:
        return Transaction(
            date=datetime.strptime(row[0], "%m/%d/%Y"),
            description=row[4],
            amount=abs(float(row[1])),
            category=row[5] if 5 < len(row) else DEFAULT_CATEGORY,
            type=TransactionType.CREDIT if float(
                row[1]) > 0 else TransactionType.DEBIT,
            file_path="",
            account_name=""
        )


class AmericanExpressTransactionsReader(TransactionReader):
    def parse_row(self, row: list[str]) -> Transaction:
        return Transaction(
            date=datetime.strptime(row[0], "%m/%d/%Y"),
            description=row[1],
            amount=abs(float(row[2])),
            category=row[3] if 3 < len(row) else DEFAULT_CATEGORY,
            type=TransactionType.CREDIT if float(
                row[3]) < 0 else TransactionType.DEBIT,
            file_path="",
            account_name=""
        )


class FidelityVisaTransactionsReader(TransactionReader):
    def parse_row(self, row: list[str]) -> Transaction:
        return Transaction(
            date=datetime.strptime(row[0], "%m/%d/%Y"),
            description=row[2],
            amount=abs(float(row[4])),
            category=row[5] if 5 < len(row) else DEFAULT_CATEGORY,
            type=TransactionType.CREDIT if row[1] == "CREDIT" else TransactionType.DEBIT,
            file_path="",
            account_name=""
        )
