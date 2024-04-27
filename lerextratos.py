import pandas as pd
import sqlite3 as lite
import pdfplumber
import PyPDF2
import re
from datetime import datetime
from view import inserir_gastos, inserir_receita, inserir_credito, inserir_vale

con = lite.connect('dados.db')



def nubank_conta(caminho):
    extrato = pd.read_csv(caminho)
    gastos_cadastrados = pd.read_sql("SELECT * FROM Gastos", con)
    receitas_cadastradas = pd.read_sql("SELECT * FROM Receitas", con)
    extrato['Valor'] = extrato['Valor'].round(2)
    gastos_cadastrados['valor'] = gastos_cadastrados['valor'].round(2)
    for index, row in extrato.iterrows():
        categoria = 'A definir'
        descrição = row['Descrição'][:50]
        data = datetime.strptime(row['Data'], '%d/%m/%Y')
        valor = row['Valor']
        if valor > 0: categoria = 'Receita'
        if ((gastos_cadastrados['descrição'] == descrição) & (pd.to_datetime(gastos_cadastrados['data']) == data) & (gastos_cadastrados['valor'] == valor)).any(): continue
        if ((receitas_cadastradas['descrição'] == descrição) & (pd.to_datetime(receitas_cadastradas['data']) == data) & (receitas_cadastradas['valor'] == valor)).any(): continue
        if valor < 0:
            lista_inserir = [categoria, descrição, data, valor]
            inserir_gastos(lista_inserir)
        elif valor > 0:
            lista_inserir = [categoria, descrição, data, valor]
            inserir_receita(lista_inserir)
def nubank_credito(caminho):
    meses_pt_to_num = {
    'JAN': '01',
    'FEV': '02',
    'MAR': '03',
    'ABR': '04',
    'MAI': '05',
    'JUN': '06',
    'JUL': '07',
    'AGO': '08',
    'SET': '09',
    'OUT': '10',
    'NOV': '11',
    'DEZ': '12'
}
    gastos_cadastrados = pd.read_sql("SELECT * FROM Credito", con)
    with pdfplumber.open(caminho) as pdf:
        # Imprimir todas as extratos encontradas
        for linha in pdf.pages[3].extract_text().split('\n'):
            match = re.search(r'(202\w{1})',linha)
            if match: year = match.group(1)
        extrato = pdf.pages[3].extract_tables()[0]
        extrato = pd.DataFrame(extrato, columns=['data', 'categoria', 'descrição', 'valor'])
    for index, row in extrato.iterrows():
        categoria = 'A definir'
        descrição = 'credito - '+row['descrição']
        data = f"{row['data'].split()[0]}/{meses_pt_to_num[row['data'].split()[1]]}/{year}"
        data = datetime.strptime(data, '%d/%m/%Y')
        valor = -float(row['valor'].replace('.','').replace(',', '.'))
        if ((gastos_cadastrados['descrição'] == descrição) & (pd.to_datetime(gastos_cadastrados['data']) == data) & (gastos_cadastrados['valor'] == valor)).any() or 'Pagamento em' in descrição: continue
        lista_inserir = [categoria, descrição, data, valor]
        inserir_credito(lista_inserir)
def sodexo(caminho):
    meses_pt_to_num = {
    'janeiro': '01',
    'fevereiro': '02',
    'março': '03',
    'abril': '04',
    'maio': '05',
    'junho': '06',
    'julho': '07',
    'agosto': '08',
    'setembro': '09',
    'outubro': '10',
    'novembro': '11',
    'dezembro': '12'
}
    gastos_cadastrados = pd.read_sql("SELECT * FROM ValeRefeição", con)
    with open(caminho, 'rb') as arquivo_pdf:
        leitor_pdf = PyPDF2.PdfReader(arquivo_pdf)
        dados = []
        # Iterar sobre as páginas do PDF
        for pagina in leitor_pdf.pages:
            texto_pagina = pagina.extract_text()
            for linha in texto_pagina.split('\n'):
                if 'EXTRATO' in linha: continue
                elif not 'R$' in linha: 
                    data = re.search(r'\w+-?\w+\s-\s([\w\d\s]+)', linha).group(1)
                    data = f'{data.split()[0]}/{meses_pt_to_num[data.split()[2]]}/{data.split()[3]}'
                    data = datetime.strptime(data, '%d/%m/%Y')
                    continue
                else: 
                    descrição = re.search(r'([A-Za-z\s]+)\s+-\s+R\$\xa0([\d,]+)', linha).group(1)
                    valor = re.search(r'([A-Za-z\s]+)\s+-\s+R\$\xa0([\d,]+)', linha).group(2)
                    if 'DISPONIBILIZACAO DE VALOR' in descrição: valor = float(valor.replace('.','').replace(',', '.'))
                    else: valor = -float(valor.replace('.','').replace(',', '.'))
                    descrição = "sodexo - " + descrição.strip()
                    categoria = 'Alimentação'
                    if valor > 0: categoria = 'Receita VR'
                    if ((gastos_cadastrados['descrição'] == descrição) & (pd.to_datetime(gastos_cadastrados['data']) == data) & (gastos_cadastrados['valor'] == valor)).any(): continue
                    lista_inserir = [categoria, descrição, data, valor]
                    inserir_vale(lista_inserir)

