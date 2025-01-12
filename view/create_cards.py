from datetime import datetime
import flet as ft


class CreateCards:
    def __init__(self, db_manager):
        """
        Inicializa a classe de visualizações.

        Args:
            db_manager (DatabaseManager): Instância do gerenciador de banco de dados.
        """
        self.db_manager = db_manager

    def calcular_dados_resumo(self):
        """Calcula os dados de resumo para os cards."""
        # Mês e ano atual
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year

        # Dados de receitas e despesas do mês atual
        receitas = self.db_manager.fetch_by_condition(
            "Receitas",
            "strftime('%Y', data) = ? AND strftime('%m', data) = ? AND " + 
            "categoria NOT IN ('Receita - Investments', 'Receita - Fixed income')",
            (str(ano_atual), f"{mes_atual:02d}")
        )
        gastos = self.db_manager.fetch_by_condition(
            "Gastos",
            "strftime('%Y', data) = ? AND strftime('%m', data) = ? AND " + 
            "categoria NOT IN ('Investments', 'Fixed income') AND " + 
            "descricao NOT IN ('Pagamento de fatura', 'Transferência enviada|Latam Gateway')",
            (str(ano_atual), f"{mes_atual:02d}")
        ) + self.db_manager.fetch_by_condition(
            "Credito",
            "strftime('%Y', data) = ? AND strftime('%m', data) = ?",
            (str(ano_atual), f"{mes_atual:02d}")
        )


        # Calcular Revenue, Expenses e Balance
        revenue = sum(r[4] for r in receitas)  # Coluna "valor" em Receitas
        expenses = sum(g[4] for g in gastos)  # Coluna "valor" em Gastos
        balance = revenue + expenses

        # Calcular média de gastos por mês
        todos_gastos = self.db_manager.fetch_by_condition(
            "Gastos",
            "categoria NOT IN ('Investments', 'Fixed income') AND " + 
            "descricao NOT IN ('Pagamento de fatura', 'Transferência enviada|Latam Gateway')",
            ()
        ) + self.db_manager.fetch_all("Credito")
        meses_distintos = set((g[3][:7] for g in todos_gastos))  # YYYY-MM format
        average_spending = sum(g[4] for g in todos_gastos) / len(meses_distintos) if meses_distintos else 0

        return {
            "Revenue": revenue,
            "Expenses": expenses,
            "Balance": balance,
            "Average spending": average_spending,
        }

    def criar_card_resumo(self, titulo, valor):
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f": R${valor:,.2f}", size=18, weight=ft.FontWeight.BOLD),
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
    view = CreateCards(db_manager)
    dados_resumo = view.calcular_dados_resumo()
    print(dados_resumo)