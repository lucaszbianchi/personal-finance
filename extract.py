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

    dados = chrome_driver.find_elements(By.XPATH, '//*[@id="__next"]/div/div/div[6]/div/div[1]/div[1]')
    texto = dados[0].text

    linhas = texto.split("\n")[texto.split("\n").index("Ocultar Transações") + 1:]
    transacoes = []

    for i, _ in enumerate(linhas):
        if re.match(r"\d{2}/\d{2}/\d{4}", linhas[i]) and i + 3 < len(linhas):
            transacoes.append([linhas[i], linhas[i + 1], linhas[i + 2], linhas[i + 3]])
    return transacoes

def create_df(data):
    df = pd.DataFrame(data, columns=["Data", "Descricao", "Categoria", "Valor"])[["Categoria", "Descricao", "Data", "Valor"]]
    return df

def save_csv(df, tabela):
    hoje = datetime.now().strftime("%Y-%m-%d")
    caminho = "extratos/"
    arquivos_csv = [
        os.path.join(caminho, arquivo)
        for arquivo in os.listdir(caminho)
        if os.path.isfile(os.path.join(caminho, arquivo)) and tabela in arquivo
    ]

    # Concatena df com os arquivos encontrados
    dataframes = [df]
    for arquivo in arquivos_csv:
        tabela_csv = pd.read_csv(arquivo)
        dataframes.append(tabela_csv)

    # Concatenar e reorganizar as colunas
    df_concatenado = pd.concat(dataframes, ignore_index=True)[df.columns].sort_values(by="Data", ascending=False)

    # Salvar tabela concatenada
    df_concatenado.to_csv(rf"extratos\extrato_{tabela}_{hoje}.csv", index=False, encoding="utf-8")

    # Excluir arquivos processados
    for arquivo in arquivos_csv:
        if not hoje in arquivo:
            os.remove(arquivo)

def insert_credit_data(df):
    gastos_cadastrados: pd.DataFrame = pd.read_sql("SELECT * FROM Credito", lite.connect('dados.db'))
    for _, row in df.iterrows():
        valor_limpo = -float(re.sub(r"[^\d.,-]", "", row["Valor"]).replace(".", "").replace(",", "."))  # Remove caracteres inválidos
        data_formatada = datetime.strptime(row["Data"], '%d/%m/%Y')
        descricao_formatada = 'credito - ' + row['Descricao']
        categoria_limpa = row["Categoria"].strip()

        # Converte a coluna de data para datetime, com erro coercitivo
        gastos_cadastrados['data'] = pd.to_datetime(gastos_cadastrados['data'], errors='coerce')

        # Verifica se há alguma linha correspondente, sem considerar as datas inválidas (NaT)
        if not gastos_cadastrados.empty and (
            (gastos_cadastrados['descricao'] == descricao_formatada) &
            (gastos_cadastrados['data'] == data_formatada) &  # Comparação com data já validada
            (gastos_cadastrados['valor'] == valor_limpo)
        ).any():
            continue
        
        db_manager.insert_data("Credito", [categoria_limpa, descricao_formatada, data_formatada, valor_limpo])
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
    gastos_cadastrados: pd.DataFrame = pd.read_sql("SELECT * FROM Gastos", lite.connect('dados.db'))
    receitas_cadastradas: pd.DataFrame = pd.read_sql("SELECT * FROM Receitas", lite.connect('dados.db'))
    df['Valor'] = df['Valor'].round(2)
    gastos_cadastrados['valor'] = gastos_cadastrados['valor'].round(2)
    for _, row in df.iterrows():
        valor_limpo = float(re.sub(r"[^\d.,-]", "", row["Valor"]).replace(".", "").replace(",", "."))  # Remove caracteres inválidos
        data_formatada = datetime.strptime(row["Data"], '%d/%m/%Y')
        descricao_limpa = row['Descricao'].strip()
        categoria_limpa = row["Categoria"].strip()
        if valor_limpo > 0:
            categoria_limpa = 'Receita - ' + categoria_limpa

        # Converte a coluna de data para datetime, com erro coercitivo
        gastos_cadastrados['data'] = pd.to_datetime(gastos_cadastrados['data'], errors='coerce')

        # Verifica se há alguma linha correspondente, sem considerar as datas inválidas (NaT)
        if not gastos_cadastrados.empty and (
            ((gastos_cadastrados['descricao'] == descricao_limpa) &
            (pd.to_datetime(gastos_cadastrados['data']) == data_formatada) &
            (gastos_cadastrados['valor'] == valor_limpo))).any():
            continue
        if not receitas_cadastradas.empty and (
            ((receitas_cadastradas['descricao'] == descricao_limpa) &
            (pd.to_datetime(receitas_cadastradas['data']) == data_formatada) &
            (receitas_cadastradas['valor'] == valor_limpo))).any():
            continue
        if valor_limpo < 0:
            db_manager.insert_data("Gastos", [categoria_limpa, descricao_limpa, data_formatada, valor_limpo])
            db_manager.inserir_categoria_unica(row["Categoria"])
        else:
            db_manager.insert_data("Receitas", [categoria_limpa, descricao_limpa, data_formatada, valor_limpo])
            db_manager.inserir_categoria_unica(row["Categoria"])
    return  

try:
    send_email_for_login(driver)
    credit_data = extract_credit_data(driver)
    df_credit = create_df(credit_data)
    save_csv(df_credit, tabela="crédito")
    insert_credit_data(df_credit)
    account_data = extract_account_data(driver)
    df_account = create_df(account_data)
    save_csv(df_account, tabela = "conta")
    insert_account_data(df_account)

finally:
    driver.quit()
