#!/usr/bin/env python3
"""
Script de teste para verificar se a API de categorias está funcionando corretamente.
"""

import sys
import traceback
from services.category_service import CategoryService
from models.category import Category

def test_category_service():
    """Testa o CategoryService diretamente"""
    print("=== TESTANDO CATEGORY SERVICE ===")

    try:
        service = CategoryService()
        print("[OK] CategoryService inicializado com sucesso")

        # Testa get_all_categories
        categories = service.get_all_categories()
        print(f"[OK] Total de categorias encontradas: {len(categories)}")

        if categories:
            print("Primeiras 3 categorias:")
            for i, cat in enumerate(categories[:3]):
                print(f"  {i+1}. ID: {cat.id}, Nome: {cat.name}")
        else:
            print("[WARN] Nenhuma categoria encontrada no banco")

        return True

    except Exception as e:
        print(f"[ERROR] Erro no CategoryService: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return False

def test_api_route():
    """Testa a rota da API simulando uma requisição"""
    print("\n=== TESTANDO ROTA DA API ===")

    try:
        from api.routes.categories_routes import list_categories
        from flask import Flask

        app = Flask(__name__)

        with app.app_context():
            response = list_categories()

            # Se é um Response object
            if hasattr(response, 'get_json'):
                data = response.get_json()
                print(f"[OK] Resposta da API: {len(data)} categorias")
                if data:
                    print("Primeira categoria da API:")
                    print(f"   {data[0]}")
            else:
                print(f"[OK] Resposta da API (raw): {response}")

        return True

    except Exception as e:
        print(f"[ERROR] Erro na rota da API: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return False

def test_database_connection():
    """Testa a conexão direta com o banco de dados"""
    print("\n=== TESTANDO CONEXAO COM BANCO ===")

    try:
        from repositories.category_repository import CategoryRepository

        repo = CategoryRepository()
        print("[OK] CategoryRepository inicializado")

        # Executa query direta
        cursor = repo.execute_query("SELECT COUNT(*) as total FROM categories")
        result = cursor.fetchone()
        print(f"[OK] Total de registros na tabela categories: {result['total']}")

        # Testa query completa
        cursor = repo.execute_query("SELECT id, name FROM categories LIMIT 3")
        rows = cursor.fetchall()
        print("[OK] Primeiros 3 registros:")
        for row in rows:
            print(f"   ID: {row['id']}, Nome: {row['name']}")

        return True

    except Exception as e:
        print(f"[ERROR] Erro na conexao com banco: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("DIAGNOSTICO DA API DE CATEGORIAS")
    print("=" * 50)

    success_count = 0

    # Testa cada componente
    if test_database_connection():
        success_count += 1

    if test_category_service():
        success_count += 1

    if test_api_route():
        success_count += 1

    print("\n" + "=" * 50)
    print(f"RESULTADO: {success_count}/3 testes passaram")

    if success_count == 3:
        print("[OK] Todas as camadas estao funcionando!")
        print("[INFO] O problema pode estar no frontend ou na configuracao do servidor.")
    else:
        print("[ERROR] Ha problemas na infraestrutura backend.")
        print("[INFO] Corrija os erros acima antes de testar o frontend.")