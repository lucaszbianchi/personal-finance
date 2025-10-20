from flask import Blueprint, jsonify
from services.finance_summary_service import FinanceSummaryService
from datetime import date
from dateutil.relativedelta import relativedelta

bp = Blueprint("dashboard", __name__)
finance_summary_service = FinanceSummaryService()


@bp.route("/data", methods=["GET"])
def get_dashboard_data():
    # Cria gráfico de pizza para despesas bancárias e de crédito
    current_date = date.today()
    start_date = current_date.replace(day=1).strftime("%Y-%m-%d")
    end_date = (
        (current_date + relativedelta(months=1)).replace(day=1).strftime("%Y-%m-%d")
    )

    # Usa o serviço de resumo financeiro para obter despesas por categoria
    category_expenses = finance_summary_service.get_category_expenses(
        start_date, end_date
    )

    # Separa as categorias que não devem entrar no gráfico
    excluded_categories = {
        "Investments",
        "Transfers",
        "Same person transfer",
        "Fixed income",
    }

    # Organiza os dados para os gráficos de pizza
    category_pie = []

    for expense in category_expenses:
        if expense["name"] not in excluded_categories:
            category_pie.append(
                {"category": expense["name"], "total": abs(expense["total"])}
            )

    # Para o gráfico de linhas, vamos coletar dados dos últimos 12 meses
    line_data = []
    for i in range(-11, 1):  # últimos 12 meses
        start = (current_date + relativedelta(months=i)).replace(day=1)
        end = (start + relativedelta(months=1)).replace(day=1)

        # Formata as datas
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        # Obtém receitas e despesas do mês
        income = finance_summary_service.get_income(start_str, end_str)
        expenses = finance_summary_service.get_expenses(start_str, end_str)

        line_data.append(
            {
                "month": start.strftime("%Y-%m"),
                "expenses": round(abs(expenses), 2),
                "income": round(income, 2),
            }
        )

    return jsonify(
        {
            "category_pie": category_pie,
            "line_data": sorted(line_data, key=lambda x: x["month"]),
        }
    )
