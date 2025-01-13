from datetime import datetime
import flet as ft
from database.database_manager import DatabaseManager
from view.create_cards import CreateCards


def main(page: ft.Page):
    page.title = "Personal Finance"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    db_manager = DatabaseManager()
    create_cards = CreateCards(db_manager)
    summary_data = create_cards.calculate_summary_data()

    cards = [create_cards.create_cards(title, value) for title, value in summary_data.items()]

    layout = ft.Column(
        [
            ft.Text(
                f"Summary of {datetime.now().month}/{datetime.now().year}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_ACCENT
            ),
            ft.Row(cards, spacing=10),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )

    page.add(layout)

ft.app(target=main)
