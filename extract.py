import time
import re
import os
from datetime import datetime
import sqlite3 as lite
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd

from database.database_manager import DatabaseManager

db_manager = DatabaseManager()

DRIVER_PATH = r"driver\chromedriver.exe"
URL = "https://meu.pluggy.ai/account"

service = Service(DRIVER_PATH)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)
load_dotenv()


def send_email_for_login(chrome_driver):
    chrome_driver.get(URL)
    time.sleep(2)
    chrome_driver.find_element(By.XPATH, '//*[@id="1-email"]').send_keys(os.environ.get("EMAIL"))
    chrome_driver.find_element(By.XPATH, '//*[@id="1-submit"]').click()
    return
def extract_credit_data(chrome_driver):
    WebDriverWait(chrome_driver, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/div/div[4]/div/div/div/div[3]/div[2]/button'))
    ).click()

    WebDriverWait(chrome_driver, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/div/div[6]/div/div[1]/div[1]/div/div[3]/span'))
    ).click()

    data = chrome_driver.find_elements(By.XPATH, '//*[@id="__next"]/div/div/div[6]/div/div[1]/div[1]')
    text = data[0].text

    lines = text.split("\n")[text.split("\n").index("Ocultar Transações") + 1:]
    transactions = []

    for i, _ in enumerate(lines):
        if re.match(r"\d{2}/\d{2}/\d{4}", lines[i]) and i + 3 < len(lines):
            transactions.append([lines[i], lines[i + 1], lines[i + 2], lines[i + 3]])
    return transactions

def create_df(data):
    df = pd.DataFrame(data, columns=["Data", "Descricao", "Categoria", "Valor"])[["Categoria", "Descricao", "Data", "Valor"]]
    return df

def save_csv(df, schema):
    today = datetime.now().strftime("%Y-%m-%d")
    path = "extracts/"
    files_csv = [
        os.path.join(path, file)
        for file in os.listdir(path)
        if os.path.isfile(os.path.join(path, file)) and schema in file
    ]

    dataframes = [df]
    for file in files_csv:
        schema_csv = pd.read_csv(file)
        dataframes.append(schema_csv)

    df_concat = pd.concat(dataframes, ignore_index=True)[df.columns].sort_values(by="Data", ascending=False)
    df_concat.to_csv(rf"extracts\extract_{schema}_{today}.csv", index=False, encoding="utf-8")

    for file in files_csv:
        if not today in file:
            os.remove(file)

def insert_credit_data(df):
    expenses_until_now: pd.DataFrame = pd.read_sql("SELECT * FROM Credit", lite.connect('data.db'))
    for _, row in df.iterrows():
        cleaned_value = -float(re.sub(r"[^\d.,-]", "", row["Valor"]).replace(".", "").replace(",", "."))
        formated_date = datetime.strptime(row["Data"], '%d/%m/%Y')
        formated_description = 'credito - ' + row['Descricao']
        cleaned_category = row["Categoria"].strip()

        expenses_until_now['data'] = pd.to_datetime(expenses_until_now['data'], errors='coerce')

        if not expenses_until_now.empty and (
            (expenses_until_now['description'] == formated_description) &
            (expenses_until_now['data'] == formated_date) &
            (expenses_until_now['valor'] == cleaned_value)
        ).any():
            continue

        db_manager.insert_data("Credit", [cleaned_category, formated_description, formated_date, cleaned_value])
        db_manager.inserir_categoria_unica(row["Categoria"])
        return
def extract_account_data(chrome_driver):
    WebDriverWait(chrome_driver, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/div/div[6]/div/div[2]/div/div/div[3]/span'))
    ).click()

    page_source = chrome_driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    table = soup.find("table", class_="Table pluggy Transactions pluggy")
    rows = table.find_all("tr")

    data = [[cell.get_text(strip=True) for cell in row.find_all(["td", "th"])] for row in rows]

    reformatted_data = []
    current_row = []

    for row in data[1:]:
        if row[0] == "Data":
            if current_row:
                reformatted_data.append(current_row)
            current_row = [""] * 4
            current_row[0] = row[1]
        elif row[0] == "Descrição":
            current_row[1] = row[1]
        elif row[0] == "Categoria":
            current_row[2] = row[1]
        elif row[0] == "Valor":
            current_row[3] = row[1]

    if current_row:
        reformatted_data.append(current_row)
    return reformatted_data

def insert_account_data(df):
    expenses_until_now: pd.DataFrame = pd.read_sql("SELECT * FROM Expenses", lite.connect('data.db'))
    receitas_cadastradas: pd.DataFrame = pd.read_sql("SELECT * FROM Revenue", lite.connect('data.db'))
    df['Valor'] = df['Valor'].round(2)
    expenses_until_now['valor'] = expenses_until_now['valor'].round(2)
    for _, row in df.iterrows():
        cleaned_value = float(re.sub(r"[^\d.,-]", "", row["Valor"]).replace(".", "").replace(",", "."))
        formated_date = datetime.strptime(row["Data"], '%d/%m/%Y')
        descricao_limpa = row['Descricao'].strip()
        cleaned_category = row["Categoria"].strip()
        if cleaned_value > 0:
            cleaned_category = 'Receita - ' + cleaned_category

        expenses_until_now['data'] = pd.to_datetime(expenses_until_now['data'], errors='coerce')

        if not expenses_until_now.empty and (
            ((expenses_until_now['description'] == descricao_limpa) &
            (pd.to_datetime(expenses_until_now['data']) == formated_date) &
            (expenses_until_now['valor'] == cleaned_value))).any():
            continue
        if not receitas_cadastradas.empty and (
            ((receitas_cadastradas['description'] == descricao_limpa) &
            (pd.to_datetime(receitas_cadastradas['data']) == formated_date) &
            (receitas_cadastradas['valor'] == cleaned_value))).any():
            continue
        if cleaned_value < 0:
            db_manager.insert_data("Expenses", [cleaned_category, descricao_limpa, formated_date, cleaned_value])
            db_manager.inserir_categoria_unica(row["Categoria"])
        else:
            db_manager.insert_data("Revenue", [cleaned_category, descricao_limpa, formated_date, cleaned_value])
            db_manager.inserir_categoria_unica(row["Categoria"])
    return

try:
    send_email_for_login(driver)
    credit_data = extract_credit_data(driver)
    df_credit = create_df(credit_data)
    save_csv(df_credit, schema="credit")
    insert_credit_data(df_credit)
    account_data = extract_account_data(driver)
    df_account = create_df(account_data)
    save_csv(df_account, schema = "account")
    insert_account_data(df_account)

finally:
    driver.quit()
