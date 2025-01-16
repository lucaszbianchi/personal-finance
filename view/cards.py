from datetime import datetime
import flet as ft


class Cards:
    def __init__(self, db_manager):
        """
        Inicializa a classe de visualizações.

        Args:
            db_manager (DatabaseManager): Instância do gerenciador de banco de data.
        """
        self.db_manager = db_manager

    def calculate_summary_data(self):
        """Calcula os data de resumo para os cards."""
        actual_month = datetime.now().month
        actual_year = datetime.now().year

        month_revenue = self.db_manager.fetch_by_condition(
            "Revenue",
            "strftime('%Y', data) = ? AND strftime('%m', data) = ? AND "
            + "category NOT IN ('Receita - Investments', 'Receita - Fixed income')",
            (str(actual_year), f"{actual_month:02d}"),
        )
        month_expenses = self.db_manager.fetch_by_condition(
            "Expenses",
            "strftime('%Y', data) = ? AND strftime('%m', data) = ? AND "
            + "category NOT IN ('Investments', 'Fixed income') AND "
            + "description NOT IN ('Pagamento de fatura', 'Transferência enviada|Latam Gateway')",
            (str(actual_year), f"{actual_month:02d}"),
        ) + self.db_manager.fetch_by_condition(
            "Credit",
            "strftime('%Y', data) = ? AND strftime('%m', data) = ?",
            (str(actual_year), f"{actual_month:02d}"),
        )

        revenue = sum(r[4] for r in month_revenue)
        expenses = sum(g[4] for g in month_expenses)
        balance = revenue + expenses

        all_time_expenses = self.db_manager.fetch_by_condition(
            "Expenses",
            "category NOT IN ('Investments', 'Fixed income') AND "
            + "description NOT IN ('Pagamento de fatura', 'Transferência enviada|Latam Gateway')",
            (),
        ) + self.db_manager.fetch_all("Credit")
        number_of_months = set((g[3][:7] for g in all_time_expenses))  # YYYY-MM format
        average_spending_by_month = (
            sum(g[4] for g in all_time_expenses) / len(number_of_months)
            if number_of_months
            else 0
        )

        return {
            "Revenue": revenue,
            "Expenses": expenses,
            "Balance": balance,
            "Average spending": average_spending_by_month,
        }

    def create_cards(self, title, value):
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f": R${value:,.2f}", size=18, weight=ft.FontWeight.BOLD
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5,
                ),
                padding=0,
                bgcolor=ft.Colors.LIGHT_BLUE_50,
                border_radius=10,
                alignment=ft.alignment.center,
                width=295,
                height=50,
            )
        )


if __name__ == "__main__":
    from database.database_manager import DatabaseManager

    db_manager = DatabaseManager()
    view = Cards(db_manager)
    data_resumo = view.calculate_summary_data()
    print(data_resumo)
