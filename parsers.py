from datetime import datetime
from transactions import Transaction, TransactionReader, DEFAULT_CATEGORY, TransactionType

# Add more formats as needed
date_formats = ["%m/%d/%y", "%d/%m/%Y", "%Y-%m-%d"]


def parse_date(date_str):
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date format not recognized: {date_str}")


class DiscoverTransactionsReader(TransactionReader):
    def parse_row(self, row: list[str]) -> Transaction:
        return Transaction(
            date=parse_date(row[0]),
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
            date=parse_date(row[2]),
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
            date=parse_date(row[0]),
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
            date=parse_date(row[0]),
            description=row[1],
            amount=abs(float(row[2])),
            category=row[3] if 3 < len(row) else DEFAULT_CATEGORY,
            type=TransactionType.CREDIT if float(
                row[2]) < 0 else TransactionType.DEBIT,
            file_path="",
            account_name=""
        )


class FidelityVisaTransactionsReader(TransactionReader):
    def parse_row(self, row: list[str]) -> Transaction:
        return Transaction(
            date=parse_date(row[0]),
            description=row[2],
            amount=abs(float(row[4])),
            category=row[5] if 5 < len(row) else DEFAULT_CATEGORY,
            type=TransactionType.CREDIT if float(
                row[4]) > 0 else TransactionType.DEBIT,
            file_path="",
            account_name=""
        )
