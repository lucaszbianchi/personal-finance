from datetime import datetime
import flet as ft
from database.database_manager import DatabaseManager
from view.create_cards import CreateCards


def main(page: ft.Page):
    # Configurações da página
    page.title = "Personal Finance"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    db_manager = DatabaseManager()
    create_cards = CreateCards(db_manager)
    dados_resumo = create_cards.calcular_dados_resumo()

    # Criar os cards de resumo
    cards = [create_cards.criar_card_resumo(titulo, valor) for titulo, valor in dados_resumo.items()]
    # Mês e ano atual
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    # Criar layout principal
    layout = ft.Column(
        [
            ft.Text(
                f"Summary of {mes_atual}/{ano_atual}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_ACCENT
            ),
            ft.Row(cards, spacing=10),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )

    # Adicionar layout à página
    page.add(layout)


# Inicializa o aplicativo Flet
ft.app(target=main)
