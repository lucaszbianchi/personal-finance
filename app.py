from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)
DB_PATH = "finance.db"


def query_db(query):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.route("/bank", methods=["GET"])
def get_bank_transactions():
    import datetime

    def format_date(date_str):
        try:
            # Exemplo: '2025-09-17T22:06:48.252Z'
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            # Ajusta para GMT-3
            dt = dt - datetime.timedelta(hours=3)
            return dt.strftime("%Y-%m-%d\n%H:%M:%S")
        except Exception:
            return date_str

    data = query_db(
        "SELECT id, description, amount, date, category, operationType FROM bank_transactions WHERE description NOT IN ('Resgate RDB', 'Aplicação RDB')"
    )
    for row in data:
        row["date"] = format_date(row["date"])
    return jsonify(data)


@app.route("/credit", methods=["GET"])
def get_credit_transactions():
    import datetime

    def format_date(date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            dt = dt - datetime.timedelta(hours=3)
            return dt.strftime("%Y-%m-%d\n%H:%M:%S")
        except Exception:
            return date_str

    data = query_db(
        "SELECT id, description, amount, date, category, status FROM credit_transactions"
    )
    for row in data:
        row["date"] = format_date(row["date"])
    return jsonify(data)


@app.route("/investments", methods=["GET"])
def get_investments():
    import datetime

    def format_date(date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            dt = dt - datetime.timedelta(hours=3)
            return dt.strftime("%Y-%m-%d\n%H:%M:%S")
        except Exception:
            return date_str

    data = query_db(
        "SELECT id, name, amount, date, rate, type, subtype FROM investments WHERE amount != 0"
    )
    for row in data:
        row["date"] = format_date(row["date"])
    return jsonify(data)


@app.route("/dashboard-data", methods=["GET"])
def dashboard_data():
    import datetime
    import re

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Piechart: Gastos por categoria (banking)
    cur.execute(
        """
        SELECT category, SUM(amount) as total
        FROM bank_transactions
        WHERE amount < 0
        AND category NOT IN ('Investments', 'Transfers', 'Same person transfer', 'Fixed income')
        GROUP BY category
    """
    )
    bank_pie = [
        {"category": row[0], "total": abs(row[1])} for row in cur.fetchall() if row[0]
    ]

    # Piechart: Gastos por categoria (credit)
    cur.execute(
        """
        SELECT category, SUM(amount) as total
        FROM credit_transactions
        WHERE amount > 0 
        GROUP BY category
    """
    )
    credit_pie = [
        {"category": row[0], "total": abs(row[1])} for row in cur.fetchall() if row[0]
    ]

    # Line: Expenses/Income per month (bank + credit)
    def month_key(date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            dt = dt - datetime.timedelta(hours=3)
            return dt.strftime("%Y-%m")
        except Exception:
            return date_str[:7]

    # Expenses
    cur.execute(
        """
        SELECT date, amount, category, description FROM bank_transactions WHERE description NOT IN ('Aplicação RDB', 'Pagamento de fatura', 'Aplicação em CDB')
        """
    )
    expenses = {}
    for date, amount, category, description in cur.fetchall():
        key = month_key(date)
        if amount < 0:
            expenses[key] = expenses.get(key, 0) + abs(amount)
        elif category == "Transfers" and re.match(
            r"^Transferência Recebida\|[A-Za-zÀ-ÿ\s]+$", description
        ):
            expenses[key] = expenses.get(key, 0) - abs(amount)

    cur.execute(
        """
        SELECT date, amount FROM credit_transactions WHERE amount > 0
        """
    )
    for date, amount in cur.fetchall():
        key = month_key(date)
        expenses[key] = expenses.get(key, 0) + abs(amount)

    # Income
    cur.execute(
        """
        SELECT date, amount, category, description FROM bank_transactions WHERE amount > 0 AND description != 'Resgate RDB'
    """
    )
    income = {}
    for date, amount, category, description in cur.fetchall():
        if category == "Transfers" and re.match(
            r"^Transferência Recebida\|[A-Za-zÀ-ÿ\s]+$", description
        ):
            continue
        key = month_key(date)
        income[key] = income.get(key, 0) + amount

    months = sorted(set(expenses.keys()) | set(income.keys()))
    line_data = []
    for m in months:
        line_data.append(
            {
                "month": m,
                "expenses": round(expenses.get(m, 0), 2),
                "income": round(income.get(m, 0), 2),
            }
        )

    conn.close()
    return jsonify(
        {"bank_pie": bank_pie, "credit_pie": credit_pie, "line_data": line_data}
    )


if __name__ == "__main__":
    app.run(debug=True)
