import flet as ft
from datetime import datetime


class Table:
    def __init__(self, db_manager):
        """
        Inicializa a classe de visualização de tabelas.

        Args:
            db_manager (DatabaseManager): Instância do gerenciador de banco de dados.
        """
        self.db_manager = db_manager
        self.selected_table = "Expenses"
        self.selected_period = "All"

    def fetch_table_data(self, table_name, period):
        """Busca os dados da tabela selecionada no banco de dados.

        Args:
            table_name (str): Nome da tabela a ser buscada.
            period (str): Período selecionado no formato "YYYY-MM" ou "YYYY".

        Returns:
            list: Lista de tuplas com os dados da tabela.
        """
        if period == "All":
            return self.db_manager.fetch_all(table_name)
        if len(period) == 4:  # Ano completo
            return self.db_manager.fetch_by_condition(
                table_name, "strftime('%Y', data) = ?", (period,)
            )
        # Mês/Ano específico
        year, month = period.split("-")
        return self.db_manager.fetch_by_condition(
            table_name,
            "strftime('%Y', data) = ? AND strftime('%m', data) = ?",
            (year, month),
        )

    def get_available_periods(self, table_name):
        """Obtém os períodos disponíveis (mês/ano e ano) nas tabelas.

        Args:
            table_name (str): Nome da tabela.

        Returns:
            list: Lista de períodos disponíveis no formato "YYYY-MM" e "YYYY".
        """
        data = self.db_manager.fetch_all(table_name)
        if not data:
            return ["All"]

        dates = [row[3] for row in data]  # Coluna de data
        unique_periods = set(
            datetime.strptime(date.split()[0], "%Y-%m-%d").strftime("%Y-%m") for date in dates
        )
        unique_years = set(date[:4] for date in unique_periods)

        periods = sorted(unique_periods) + sorted(unique_years)
        return ["All"] + periods

    def create_table_view(self, table_name, period):
        """Cria a visualização da tabela com base nos dados do banco.

        Args:
            table_name (str): Nome da tabela a ser exibida.
            period (str): Período selecionado no formato "YYYY-MM" ou "YYYY".

        Returns:
            ft.Container: Tabela dentro de um container com scrollbar.
        """
        data = self.fetch_table_data(table_name, period)
        if not data:
            return ft.Text("No data available", size=16, weight=ft.FontWeight.BOLD)

        # Cabeçalhos da tabela
        headers = ["ID", "Category", "Description", "Date", "Value"]

        # Criação das linhas da tabela
        rows = [
            ft.DataRow(cells=[ft.DataCell(ft.Text(str(cell))) for cell in row])
            for row in data
        ]

        table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(header)) for header in headers],
            rows=rows,
            border=ft.border.all(1, ft.Colors.GREY),
            column_spacing=10,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        )

        # Envolver a tabela em um Container com rolagem vertical
        return ft.Container(
            content=ft.Column(
                [table],
                scroll=ft.ScrollMode.AUTO,  # Habilita a rolagem se necessário
            ),
            height=300,  # Altura fixa da tabela (ajuste conforme necessário)
            clip_behavior=ft.ClipBehavior.HARD_EDGE,  # Recorta conteúdo extra
        )

    def create_dropdown(self, options, value, on_change, width=200):
        """Cria um dropdown genérico.

        Args:
            options (list): Lista de opções para o dropdown.
            value (str): Valor inicial selecionado.
            on_change (function): Função a ser chamada quando o valor do dropdown mudar.
            width (int): Largura do dropdown.

        Returns:
            ft.Dropdown: Componente de dropdown do Flet.
        """
        return ft.Dropdown(
            options=[ft.dropdown.Option(option) for option in options],
            value=value,
            on_change=on_change,
            width=width,
        )

    def build(self):
        """Constrói a interface da tabela com os dropdowns.

        Returns:
            ft.Column: Layout contendo os dropdowns e a tabela.
        """
        available_periods = self.get_available_periods(self.selected_table)
        table_view = ft.Container(
            content=self.create_table_view(self.selected_table, self.selected_period),
            padding=10,
        )

        def on_table_dropdown_change(e):
            self.selected_table = e.control.value
            self.selected_period = "All"  # Resetar o período ao mudar a tabela
            period_dropdown.options = [
                ft.dropdown.Option(option)
                for option in self.get_available_periods(self.selected_table)
            ]
            period_dropdown.value = self.selected_period
            period_dropdown.update()
            table_view.content = self.create_table_view(
                self.selected_table, self.selected_period
            )
            table_view.update()

        def on_period_dropdown_change(e):
            self.selected_period = e.control.value
            table_view.content = self.create_table_view(
                self.selected_table, self.selected_period
            )
            table_view.update()

        table_dropdown = self.create_dropdown(
            ["Expenses", "Credit", "Revenue"],
            self.selected_table,
            on_table_dropdown_change,
        )

        period_dropdown = self.create_dropdown(
            available_periods,
            self.selected_period,
            on_period_dropdown_change,
        )

        return ft.Column(
            [
                ft.Text("Select Table", size=18, weight=ft.FontWeight.BOLD),
                table_dropdown,
                ft.Text("Select Period", size=18, weight=ft.FontWeight.BOLD),
                period_dropdown,
                table_view,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        )
