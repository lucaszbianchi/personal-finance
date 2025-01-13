import sqlite3 as lite

class DatabaseManager:
    def __init__(self, db_name=r"data.db"):
        self.db_name = db_name
        self._initialize_database()

    def _connect(self):
        """Estabelece uma conexão com o banco de data."""
        return lite.connect(self.db_name)

    def _initialize_database(self):
        """Cria as tabelas no banco de data se elas não existirem."""
        with self._connect() as con:
            cur = con.cursor()
            # Tabela para categorias de gastos
            cur.execute('''CREATE TABLE IF NOT EXISTS Categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT
            )''')

            # Tabela para registrar receitas
            cur.execute('''CREATE TABLE IF NOT EXISTS Revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                description TEXT,
                data DATE,
                valor DECIMAL
            )''')

            # Tabela para registrar gastos
            cur.execute('''CREATE TABLE IF NOT EXISTS Expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                description TEXT,
                data DATE,
                valor DECIMAL
            )''')

            # Tabela para registrar transações de crédito
            cur.execute('''CREATE TABLE IF NOT EXISTS Credit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                description TEXT,
                data DATE,
                valor DECIMAL
            )''')

    def reset_database(self):
        """Remove todas as tabelas e recria a estrutura inicial do banco de data."""
        with self._connect() as con:
            cur = con.cursor()
            # Remove tabelas existentes
            cur.execute("DROP TABLE IF EXISTS Categorias")
            cur.execute("DROP TABLE IF EXISTS Revenue")
            cur.execute("DROP TABLE IF EXISTS Expenses")
            cur.execute("DROP TABLE IF EXISTS Credit")
            # Recria as tabelas
            self._initialize_database()


    # Função para inserir categorias únicas
    def inserir_categoria_unica(self,category):
        query = "SELECT 1 FROM Categorias WHERE nome = ?"
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(query, (category,))
            if not cur.fetchone():  # Categoria não existe
                self.insert_data("Categorias", [category])

    def insert_data(self, table, data):
        """Insere data em uma tabela específica.

        Args:
            table (str): Nome da tabela.
            data (list): Dados a serem inseridos, excluindo o ID.
        """
        with self._connect() as con:
            cur = con.cursor()
            placeholders = ", ".join(["?"] * len(data))
            query = f"INSERT INTO {table} VALUES (NULL, {placeholders})"
            cur.execute(query, data)

    def delete_data(self, table, row_id):
        """Remove uma linha específica de uma tabela.

        Args:
            table (str): Nome da tabela.
            row_id (int): ID da linha a ser removida.
        """
        with self._connect() as con:
            cur = con.cursor()
            query = f"DELETE FROM {table} WHERE id = ?"
            cur.execute(query, (row_id,))

    def update_data(self, table, row_id, column, value):
        """Atualiza um valor em uma linha específica de uma tabela.

        Args:
            table (str): Nome da tabela.
            row_id (int): ID da linha a ser atualizada.
            column (str): Nome da coluna a ser atualizada.
            value: Novo valor para a coluna.
        """
        with self._connect() as con:
            cur = con.cursor()
            query = f"UPDATE {table} SET {column} = ? WHERE id = ?"
            cur.execute(query, (value, row_id))

    def fetch_all(self, table):
        """Retorna todas as linhas de uma tabela.

        Args:
            table (str): Nome da tabela.

        Returns:
            list: Lista de tuplas com os data das linhas.
        """
        with self._connect() as con:
            cur = con.cursor()
            query = f"SELECT * FROM {table}"
            cur.execute(query)
            return cur.fetchall()

    def fetch_by_condition(self, table, condition, params):
        """Retorna linhas de uma tabela que satisfaçam uma condição.

        Args:
            table (str): Nome da tabela.
            condition (str): Condição SQL para filtrar os data.
            params (tuple): Valores a serem utilizados na condição.

        Returns:
            list: Lista de tuplas com os data das linhas.
        """
        with self._connect() as con:
            cur = con.cursor()
            query = f"SELECT * FROM {table} WHERE {condition}"
            cur.execute(query, params)
            return cur.fetchall()

# Exemplo de uso
if __name__ == "__main__":
    db = DatabaseManager()
    credito = db.fetch_all("credito")
    print("credito:", credito)
