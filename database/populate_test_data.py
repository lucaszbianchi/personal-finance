from datetime import datetime, timedelta
from database_manager import DatabaseManager


def populate_test_data():
    db_manager = DatabaseManager()

    db_manager.reset_database()

    categories = ["Food", "Transport", "Salary", "Investments", "Entertainment"]
    for category in categories:
        db_manager.inserir_categoria_unica(category)

    revenue_data = [
        (
            "Salary",
            "Monthly salary",
            (datetime.now() - timedelta(days=30)).date(),
            5000.00,
        ),
        (
            "Investments",
            "Stock dividends",
            (datetime.now() - timedelta(days=15)).date(),
            200.00,
        ),
        ("Salary", "Bonus", (datetime.now() - timedelta(days=5)).date(), 1000.00),
    ]
    for data in revenue_data:
        db_manager.insert_data("Revenue", data)

    expenses_data = [
        ("Food", "Groceries", (datetime.now() - timedelta(days=28)).date(), -150.00),
        (
            "Transport",
            "Gasoline",
            (datetime.now() - timedelta(days=20)).date(),
            -100.00,
        ),
        (
            "Entertainment",
            "Movie tickets",
            (datetime.now() - timedelta(days=10)).date(),
            -50.00,
        ),
        ("Food", "Restaurant", (datetime.now() - timedelta(days=2)).date(), -80.00),
    ]
    for data in expenses_data:
        db_manager.insert_data("Expenses", data)

    credit_data = [
        (
            "Transport",
            "Uber ride",
            (datetime.now() - timedelta(days=25)).date(),
            -30.00,
        ),
        ("Food", "Coffee shop", (datetime.now() - timedelta(days=18)).date(), -20.00),
        (
            "Entertainment",
            "Concert tickets",
            (datetime.now() - timedelta(days=7)).date(),
            -120.00,
        ),
    ]
    for data in credit_data:
        db_manager.insert_data("Credit", data)


if __name__ == "__main__":
    populate_test_data()
    print("Test data populated successfully.")
