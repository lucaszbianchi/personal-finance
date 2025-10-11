from flask import Flask, jsonify
import sqlite3

from fetch_data import FetchData
from services.transaction_service import TransactionService
from services.category_service import CategoryService

app = Flask(__name__)
DB_PATH = "finance.db"
category_service = CategoryService()
transaction_service = TransactionService()


@app.route("/bank", methods=["GET"])
def get_bank_transactions():
    bank_transactions = transaction_service.get_bank_transactions()
    transactions = []
    for transaction in bank_transactions:
        tx_dict = transaction.__dict__
        if "category_id" in tx_dict:
            category = category_service.get_category_by_id(tx_dict["category_id"])
            tx_dict["category"] = category.name
            del tx_dict["category_id"]
        transactions.append(tx_dict)
    return jsonify(transactions)


@app.route("/credit", methods=["GET"])
def get_credit_transactions():
    credit_transactions = transaction_service.get_credit_transactions()
    transactions = []
    for transaction in credit_transactions:
        tx_dict = transaction.__dict__
        if "category_id" in tx_dict:
            category = category_service.get_category_by_id(tx_dict["category_id"])
            tx_dict["category"] = category.name
            del tx_dict["category_id"]
        transactions.append(tx_dict)
    return jsonify(transactions)


@app.route("/investments", methods=["GET"])
def get_investments():
    investments = transaction_service.get_investments()
    return jsonify([inv.__dict__ for inv in investments])


@app.route("/dashboard-data", methods=["GET"])
def dashboard_data():
    import datetime
    import re

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Piechart: Gastos por categoria (banking)
    cur.execute(
        """
        SELECT categories.name, SUM(amount) as total
        FROM bank_transactions
        LEFT JOIN categories ON bank_transactions.category_id = categories.id
        WHERE amount < 0
        AND categories.name NOT IN ('Investments', 'Transfers', 'Same person transfer', 'Fixed income')
        GROUP BY categories.name
    """
    )
    bank_pie = [
        {"category": row[0], "total": abs(row[1])} for row in cur.fetchall() if row[0]
    ]

    # Piechart: Gastos por categoria (credit)
    cur.execute(
        """
        SELECT categories.name, SUM(amount) as total
        FROM credit_transactions
        LEFT JOIN categories ON credit_transactions.category_id = categories.id
        WHERE amount > 0
        GROUP BY categories.name
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
        SELECT date, amount, categories.name, description FROM bank_transactions
        LEFT JOIN categories ON bank_transactions.category_id = categories.id
        WHERE description NOT IN ('Aplicação RDB', 'Pagamento de fatura', 'Aplicação em CDB')
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
        SELECT date, amount, categories.name, description FROM bank_transactions
        LEFT JOIN categories ON bank_transactions.category_id = categories.id
        WHERE amount > 0 AND description != 'Resgate RDB'
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


@app.route("/summary", methods=["GET"])
def summary():
    import datetime
    import re

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Configura período (mês/ano atual) -> TODO: pode ser parâmetro futuramente
    month = "09"
    year = "2025"
    # Nome do usuário (para identificar salário) TODO: obter nome do usuário de forma dinâmica
    user_name = "LUCAS ZIWICH BIANCHI"

    income = 0
    expenses = 0
    total_expenses = 0
    months = set()
    salary = 0
    investments = 0

    def month_key(date_str):
        """Converte uma string de data para uma chave de mês.
        Ex: "2025-09-15T12:34:56.789Z" -> "2025-09"
        """
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            dt = dt - datetime.timedelta(hours=3)
            return dt.strftime("%Y-%m")
        except Exception:
            return date_str[:7]

    # --- Transações bancárias ---
    cur.execute(
        """
        SELECT date, description, amount, categories.name
        FROM bank_transactions
        LEFT JOIN categories ON bank_transactions.category_id = categories.id
        WHERE description NOT IN ('Resgate RDB', 'Aplicação RDB')
        """
    )
    for (
        date,
        description,
        amount,
        category,
    ) in cur.fetchall():  # TODO: importar partner_id
        key = month_key(date)
        y, m = key.split("-")

        partner_id = False
        if description[:23] in [
            user_name,
            "SIMONI DA SILVA ZIWICH BIANCHI",
            "Iacrypto Intermediation &amp; Administration Ltda",
            "SECR. DA RECEITA FEDERAL -  LOTE 2025/02 - RMS 0136",
        ]:
            partner_id = None

        if m == month and y == year:
            # Transferências recebidas do parceiro (não contam como receita)
            if re.match(r"^Transferência Recebida\|.+$", description) and partner_id:
                expenses -= amount
                print(f"Transferência recebida ignorada: {description} | {amount}")
                continue
            # Receita
            if amount > 0:
                income += amount
                # Salário
                if (
                    category == "Same person transfer"
                    and description == f"Transferência Recebida|{user_name}"
                ):
                    salary += amount
            # Despesa
            elif amount < 0 and description not in (
                "Aplicação RDB",
                "Pagamento de fatura",
                "Aplicação em CDB",
            ):
                expenses += abs(amount)
                total_expenses += abs(amount)
                months.add(key)

    # --- Transações de crédito ---
    cur.execute("SELECT date, amount FROM credit_transactions WHERE amount > 0")
    for date, amount in cur.fetchall():
        key = month_key(date)
        y, m = key.split("-")

        if m == month and y == year:
            expenses += amount
            total_expenses += amount

        months.add(key)

    # --- Investimentos ---
    cur.execute("SELECT balance FROM investments")
    investments = sum(row[0] for row in cur.fetchall())

    conn.close()

    # Cálculos finais
    balance = income - expenses
    avg_spending = total_expenses / len(months) if months else 0

    return jsonify(
        {
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "balance": round(balance, 2),
            "avg_spending": round(avg_spending, 2),
            "salary": round(salary, 2),
            "investments": round(investments, 2),
            "month": f"{month}/{year}",
        }
    )


from flask import request


@app.route("/transactions", methods=["GET"])
def get_transactions():
    import datetime

    # Parâmetros da query string
    ttype = request.args.get("type")  # bank | credit | investments
    month = request.args.get("month")  # ex: 2025-09
    category = request.args.get("category")  # string para filtro

    if ttype == "bank":
        query = "SELECT id, description, amount, date, category, operationType FROM bank_transactions WHERE 1=1"
    elif ttype == "credit":
        query = "SELECT id, description, amount, date, category, status FROM credit_transactions WHERE 1=1"
    elif ttype == "investments":
        query = (
            "SELECT id, name, balance, date, type, subtype FROM investments WHERE 1=1"
        )
    else:
        return jsonify([])

    params = []

    # Filtro por mês
    if month and ttype != "investments":
        query += " AND substr(date, 1, 7) = ?"
        params.append(month)

    # Filtro por categoria
    if category and ttype in ("bank", "credit"):
        query += " AND LOWER(category) LIKE ?"
        params.append(f"%{category.lower()}%")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    # Formatar datas
    def format_date(date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            dt = dt - datetime.timedelta(hours=3)
            return dt.strftime("%Y-%m-%d\n%H:%M:%S")
        except Exception:
            return date_str

    for row in rows:
        if "date" in row:
            row["date"] = format_date(row["date"])
        if "dueDate" in row:
            row["dueDate"] = format_date(row["dueDate"])

    return jsonify(rows)


@app.route("/import-data", methods=["POST"])
def import_data():
    fetch_data = FetchData()
    fetch_data.execute()
    return jsonify({"status": "success", "message": "Data imported successfully."})


if __name__ == "__main__":
    app.run(debug=True)
