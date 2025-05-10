import seaborn as sns  # matplotlib theme
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend before importing pyplot

sns.set_theme()


def format_currency(value):
    return f"{value:,.2f}"


def save_pie_chart(values, labels, title, filename):
    if len(values) != len(labels):
        raise ValueError("Length of values and labels must be the same.")

    # Create figure
    plt.figure(figsize=(5, 5))

    # Create pie chart
    plt.pie(
        values,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        labeldistance=1.1
    )

    plt.title(title)
    plt.axis('equal')  # Make sure it's a circle

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def save_bar_chart(data, title, filename):
    # Sort data by value (optional but clearer)
    sorted_items = sorted(data.items(), key=lambda item: item[1], reverse=True)
    labels = [k for k, v in sorted_items]
    values = [v for k, v in sorted_items]

    # Calculate percentages
    total = sum(values)
    percentages = [f"{(v/total)*100:.1f}%" for v in values]

    # Plot
    plt.figure(figsize=(8, 6))
    bars = plt.barh(labels, values, color="skyblue")
    plt.xlabel("Amounts")
    plt.title(title)

    # Add value labels on the bars
    for bar, pct in zip(bars, percentages):
        plt.text(bar.get_width() + 1, bar.get_y() +
                 bar.get_height()/2, pct, va='center')

    plt.tight_layout()
    plt.savefig(filename)


def draw_plots(stats):
    # category_total_expenses = stats["category_total_expenses"]
    # category_total_income = stats["category_total_income"]

    # save_bar_chart(category_total_expenses,
    #                "Total Expenses", "static/total_expenses.png")
    # save_bar_chart(category_total_income,
    #                "Total income", "static/total_income.png")

    # if stats["pie_chart_values"]:
    #     save_pie_chart(values=stats["pie_chart_values"],
    #                    labels=stats["pie_chart_labels"],
    #                    title="Balance Summary",
    #                    filename="static/balance_summary.png")

    stats["pivot_table"].plot()
    plt.title('Pivot Table Plot')
    plt.xlabel('Category')
    plt.ylabel('Value')

    plt.legend(title='Amount')
    plt.xticks(rotation=0)

    plt.savefig("static/pivot_table.png")


def create_pivot_table(df):
    # Pivot using the datetime column as index
    pivoted = df.pivot_table(index='month_dt', columns='category',
                             values='amount', aggfunc='sum', fill_value=0)

    # Sort the index (chronologically)
    pivoted = pivoted.sort_index()

    # Optional: Format datetime back to "Month Year" strings for display
    pivoted.index = pivoted.index.strftime('%b %Y')

    pivoted['Total'] = pivoted.sum(axis=1)
    pivoted.loc['Total'] = pivoted.sum(numeric_only=True)

    pivoted['Avg'] = pivoted.mean(axis=1)
    pivoted.loc['Avg'] = pivoted.mean(numeric_only=True)

    return pivoted


def pivot_table_to_html(pivoted):
    html_content = "<table border='1'>"
    html_content += "<tr><th>Month</th>" + \
        "".join([f"<th>{col}</th>" for col in pivoted.columns]) + "</tr>"

    for month, row in pivoted.iterrows():
        html_content += f"<tr><td>{month}</td>" + "".join(
            [f"<td>{format_currency(val)}</td>" for val in row]) + "</tr>"

    html_content += "</table>"

    return html_content


def get_summary_stats(transactions):
    df = pd.DataFrame(transactions)
    print(df.shape)

    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.strftime('%b %Y')

    # Convert 'month' to datetime for proper sorting
    df['month_dt'] = pd.to_datetime(df['month_year'], format='%b %Y')

    total_balance = df["amount"].sum()

    # expenses = df[df["amount"] < 0]
    # income = df[df["amount"] > 0]

    # total_rent = expenses[expenses["category"] == "Rent"]["amount"].sum()

    # total_expense = expenses["amount"].sum()
    # total_income = income["amount"].sum()
    # total_paycheck_income = income[income["category"]
    #                                == "Paycheck"]["amount"].sum()
    # total_savings_deposit = expenses[expenses["category"]
    #                                  == "Savings"]["amount"].sum()
    # total_savings_withdrawn = income[income["category"]
    #                                  == "Savings"]["amount"].sum()
    # total_savings = total_savings_deposit - total_savings_withdrawn
    # total_investment = expenses[expenses["category"]
    #                             == "Investment"]["amount"].sum()

    # monthly_paycheck = income[income['category'] == 'Paycheck'][[
    #     'month_year', 'amount']].groupby('month_year').sum().reset_index()
    # monthly_paycheck_result = {}
    # for _, row in monthly_paycheck.iterrows():
    #     monthly_paycheck_result[row["month_year"]] = row["amount"]

    # category_total_expenses = expenses[["amount", "category"]].groupby("category")[
    #     "amount"].sum().reset_index()
    # category_total_income = income[["amount", "category"]].groupby("category")[
    #     "amount"].sum().reset_index()

    # category_total_expenses = dict(
    #     zip(category_total_expenses.category, category_total_expenses.amount))
    # category_total_income = dict(
    #     zip(category_total_income.category, category_total_income.amount))

    # pie_chart_values = None
    # pie_chart_labels = None

    # if total_income > 0:
    #     total_other_expense = total_expense - \
    #         total_savings - total_investment - total_rent
    #     pie_chart_values = [
    #         total_other_expense/total_income,
    #         total_rent/total_income,
    #         total_savings/total_income,
    #         total_investment/total_income
    #     ]

    #     pie_chart_labels = [
    #         "other expenses %",
    #         "rent %",
    #         "savings %",
    #         "investment %"
    #     ]

    pivot_table = create_pivot_table(df)
    pivot_table_html = pivot_table_to_html(pivot_table)

    return {
        "total_balance": total_balance,
        # "pie_chart_values": pie_chart_values,
        # "pie_chart_labels": pie_chart_labels,
        # "total_expense": total_expense,
        # "total_income": total_income,
        # "total_paycheck_income": total_paycheck_income,
        # "total_savings": total_savings,
        # "total_investment": total_investment,
        # "monthly_paycheck_income": monthly_paycheck_result,
        # "category_total_expenses": category_total_expenses,
        # "category_total_income": category_total_income,
        "pivot_table": pivot_table,
        "pivot_table_html": pivot_table_html
    }
