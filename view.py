import sys
import sqlite3 as lite
from datetime import datetime

# importing pandas
import pandas as pd

# Criando conexão
con = lite.connect('dados.db')

# Inserir categoria
def inserir_categoria(i):
    with con:
        cur = con.cursor()
        query = "INSERT INTO Categoria (nome) VALUES (?)"
        cur.execute(query, i)
# Deletar categoria
def deletar_categoria(i):
    with con:
        cur = con.cursor()
        query = "DELETE FROM Categoria WHERE nome=?"
        cur.execute(query, i)
# Inserir receitas
def inserir_receita(i):
    with con:
        cur = con.cursor()
        query = "INSERT INTO Receitas (fonte, descrição, data, valor) VALUES (?,?,?,?)"
        cur.execute(query, i)

# Inserir gastos
def inserir_gastos(i):
    with con:
        cur = con.cursor()
        query = "INSERT INTO Gastos (categoria, descrição, data, valor) VALUES (?,?,?,?)"
        cur.execute(query, i)

def inserir_credito(i):
    with con:
        cur = con.cursor()
        query = "INSERT INTO Credito (categoria, descrição, data, valor) VALUES (?,?,?,?)"
        cur.execute(query, i)

def inserir_vale(i):
    with con:
        cur = con.cursor()
        query = "INSERT INTO ValeRefeição (categoria, descrição, data, valor) VALUES (?,?,?,?)"
        cur.execute(query, i)

# Deletar receitas
def deletar_receitas(i):
    with con:
        cur = con.cursor()
        query = "DELETE FROM Receitas WHERE id=?"
        cur.execute(query, i)

# Deletar creditos
def deletar_credito(i):
    with con:
        cur = con.cursor()
        query = "DELETE FROM Credito WHERE id=?"
        cur.execute(query, i)

# Deletar ValeRefeição
def deletar_valerefeição(i):
    with con:
        cur = con.cursor()
        query = "DELETE FROM ValeRefeição WHERE id=?"
        cur.execute(query, i)

# Deletar gastos
def deletar_gastos(i):
    with con:
        cur = con.cursor()
        query = "DELETE FROM Gastos WHERE id=?"
        cur.execute(query, i)
# Atualizar gastos
def atualizar_gastos(id, nova_categoria, nova_descricao):
    with con:
        cur = con.cursor()
        query = "UPDATE Gastos SET categoria=?, descrição=? WHERE id=?"
        cur.execute(query, (nova_categoria, nova_descricao, id))
# Atualizar receitas
def atualizar_receitas(id, nova_categoria, nova_descricao):
    with con:
        cur = con.cursor()
        query = "UPDATE Receitas SET categoria=?, descrição=? WHERE id=?"
        cur.execute(query, (nova_categoria, nova_descricao, id))
# Atualizar credito
def atualizar_credito(id, nova_categoria, nova_descricao):
    with con:
        cur = con.cursor()
        query = "UPDATE Credito SET categoria=?, descrição=? WHERE id=?"
        cur.execute(query, (nova_categoria, nova_descricao, id))
# Atualizar ValeRefeição
def atualizar_vale(id, nova_categoria, nova_descricao):
    with con:
        cur = con.cursor()
        query = "UPDATE ValeRefeilção SET categoria=?, descrição=? WHERE id=?"
        cur.execute(query, (nova_categoria, nova_descricao, id))
# Ver Categorias
def ver_categorias():
    lista_itens = []
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM Categoria")
        rows = cur.fetchall()
        for row in rows:
            lista_itens.append(row[1])
    return lista_itens

# Ver Receitas
def ver_receitas(data_inicio=None, data_fim=None):
    lista_itens = []
    with con:
        cur = con.cursor()
        if data_inicio is None or data_fim is None:
            cur.execute("SELECT * FROM Receitas")
        else:
            cur.execute("SELECT * FROM Receitas WHERE data BETWEEN ? AND ?", (data_inicio, data_fim))
        rows = cur.fetchall()
        for row in rows:
            lista_itens.append(row)
    return lista_itens


# Ver Gastos
def ver_gastos(data_inicio=None, data_fim=None):
    lista_itens = []
    with con:
        cur = con.cursor()
        if data_inicio is None or data_fim is None:
            cur.execute("SELECT * FROM Gastos")
        else:
            cur.execute("SELECT * FROM Gastos WHERE data BETWEEN ? AND ?", (data_inicio, data_fim))
        rows = cur.fetchall()
        for row in rows:
            lista_itens.append(row)
    return lista_itens

def ver_credito(data_inicio=None, data_fim=None):
    lista_itens = []
    with con:
        cur = con.cursor()
        if data_inicio is None or data_fim is None:
            cur.execute("SELECT * FROM Credito")
        else:
            cur.execute("SELECT * FROM Credito WHERE data BETWEEN ? AND ?", (data_inicio, data_fim))
        rows = cur.fetchall()
        for row in rows:
            lista_itens.append(row)
    return lista_itens

def ver_vale(data_inicio=None, data_fim=None):
    lista_itens = []
    with con:
        cur = con.cursor()
        if data_inicio is None or data_fim is None:
            cur.execute("SELECT * FROM ValeRefeição")
        else:
            cur.execute("SELECT * FROM ValeRefeição WHERE data BETWEEN ? AND ?", (data_inicio, data_fim))
        rows = cur.fetchall()
        for row in rows:
            lista_itens.append(row)
    return lista_itens

def tabela(data_inicio=None, data_fim=None):
    gastos = ver_gastos(data_inicio=data_inicio,data_fim=data_fim)
    receitas = ver_receitas(data_inicio=data_inicio,data_fim=data_fim)
    credito = ver_credito(data_inicio=data_inicio,data_fim=data_fim)
    vale = ver_vale(data_inicio=data_inicio,data_fim=data_fim)

    tabela_lista = []

    for i in gastos:
        tabela_lista.append(i)
    for i in receitas:
        tabela_lista.append(i)
    for i in credito:
        tabela_lista.append(i)
    for i in vale:
        tabela_lista.append(i)

    return tabela_lista

def bar_valores():
    # Receita Total ------------------------
    receitas = ver_receitas()
    receitas_lista = []

    for i in receitas:
        receitas_lista.append(i[3])

    receita_total = sum(receitas_lista)

    # Despesas Total ------------------------
    receitas = ver_gastos()
    despesas_lista = []

    for i in receitas:
        despesas_lista.append(i[3])

    despesas_total = sum(despesas_lista)

    # Despesas Total ------------------------
    saldo_total = receita_total - despesas_total

    return[receita_total,despesas_total,saldo_total]

def percentagem_valor():

    # Receita Total ------------------------
    receitas = ver_receitas()
    receitas_lista = []

    for i in receitas:
        receitas_lista.append(i[3])

    receita_total = sum(receitas_lista)

    # Despesas Total ------------------------
    receitas = ver_gastos()
    despesas_lista = []

    for i in receitas:
        despesas_lista.append(i[3])

    despesas_total = sum(despesas_lista)

    # Despesas Total ------------------------
    total =  ((receita_total - despesas_total) / receita_total) * 100

    return[total]


def pie_valores():
    gastos = ver_gastos()
    tabela_lista = []

    for i in gastos:
        tabela_lista.append(i)

    dataframe = pd.DataFrame(tabela_lista,columns = ['id', 'Categoria', 'Data', 'valor'])

    # Get the sum of the durations per month
    dataframe = dataframe.groupby('Categoria')['valor'].sum()
   
    lista_quantias = dataframe.values.tolist()
    lista_categorias = []

    for i in dataframe.index:
        lista_categorias.append(i)

    return([lista_categorias,lista_quantias])