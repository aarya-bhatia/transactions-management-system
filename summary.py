import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict


def format_currency(value):
    return f"${value:,.2f}"


def get_summary_stats(uploads, transactions):
    df = pd.DataFrame(transactions)
    print(df.head())

    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.strftime('%b %Y')

    expenses = df[df["type"] == "DEBIT"]
    income = df[df["type"] == "CREDIT"]

    total_expense = expenses["amount"].sum()
    total_income = income["amount"].sum()
    total_paycheck_income = income[income["category"]
                                   == "Paycheck"]["amount"].sum()
    total_savings_deposit = expenses[expenses["category"]
                                     == "Savings"]["amount"].sum()
    total_savings_withdrawn = income[income["category"]
                                     == "Savings"]["amount"].sum()
    total_savings = total_savings_deposit - total_savings_withdrawn
    total_investment = expenses[expenses["category"]
                                == "Investment"]["amount"].sum()

    monthly_paycheck = income[income['category'] == 'Paycheck'][[
        'month_year', 'amount']].groupby('month_year').sum().reset_index()
    monthly_paycheck_result = {}
    for _, row in monthly_paycheck.iterrows():
        monthly_paycheck_result[row["month_year"]] = row["amount"]

    category_expenses = expenses[["category", "month_year", "amount"]].groupby(
        ["category", "month_year"]).sum().reset_index()
    category_expenses_result = defaultdict(dict)
    for _, row in category_expenses.iterrows():
        category = row['category']
        month_year = row['month_year']
        amount = row['amount']
        category_expenses_result[category][month_year] = amount

    category_income = income[["category", "month_year", "amount"]].groupby(
        ["category", "month_year"]).sum().reset_index()
    category_income_result = defaultdict(dict)
    for _, row in category_income.iterrows():
        category = row['category']
        month_year = row['month_year']
        amount = row['amount']
        category_income_result[category][month_year] = amount

    return {
        "total_expense": format_currency(total_expense),
        "total_income": format_currency(total_income),
        "total_paycheck_income": format_currency(total_paycheck_income),
        "total_savings": format_currency(total_savings),
        "total_investment": format_currency(total_investment),
        "monthly_paycheck_income": monthly_paycheck_result,
        "category_expenses": category_expenses_result,
        "category_income": category_income_result,
    }
