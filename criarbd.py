import sqlite3 as lite
import os

if os.path.exists('dados.db'): os.remove('dados.db')
con = lite.connect('dados.db')

with con:
    cur = con.cursor()
    cur.execute('CREATE TABLE Categoria(id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)')
    
with con:
    cur = con.cursor()
    cur.execute('CREATE TABLE Receitas(id INTEGER PRIMARY KEY AUTOINCREMENT, fonte TEXT, descrição TEXT, data DATE, valor DECIMAL)')

with con:
    cur = con.cursor()
    cur.execute('CREATE TABLE Gastos(id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, descrição TEXT, data DATE, valor DECIMAL)')

with con:
    cur = con.cursor()
    cur.execute('CREATE TABLE Credito(id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, descrição TEXT, data DATE, valor DECIMAL)')

with con:
    cur = con.cursor()
    cur.execute('CREATE TABLE ValeRefeição(id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, descrição TEXT, data DATE, valor DECIMAL)')