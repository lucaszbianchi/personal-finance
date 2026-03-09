"""
Serviço de autenticação com a Pluggy API.
Responsável por gerar o apiKey e o connect token.
"""

import json
import os

import dotenv
import requests

dotenv.load_dotenv()

PLUGGY_BASE_URL = "https://api.pluggy.ai"


def get_api_key() -> str:
    """
    Autentica na Pluggy API e retorna um apiKey válido por 2 horas.
    Usado pelo backend para chamadas server-side à API.
    """
    payload = {
        "clientId": os.getenv("CLIENT_ID"),
        "clientSecret": os.getenv("CLIENT_SECRET"),
    }
    headers = {"accept": "application/json", "content-type": "application/json"}
    response = requests.post(
        f"{PLUGGY_BASE_URL}/auth", json=payload, headers=headers, timeout=30
    )
    response.raise_for_status()
    return response.json().get("apiKey")


def get_item(item_id: str) -> dict:
    """Retorna os dados atuais de um item diretamente da Pluggy API."""
    api_key = get_api_key()
    headers = {"accept": "application/json", "X-API-KEY": api_key}
    response = requests.get(
        f"{PLUGGY_BASE_URL}/items/{item_id}", headers=headers, timeout=30
    )
    response.raise_for_status()
    return response.json()


def create_connect_token() -> dict:
    """
    Gera um connect token de curta duração para uso no widget Pluggy Connect.
    Retorna { accessToken, expiresAt }.
    """
    api_key = get_api_key()
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": api_key,
    }
    response = requests.post(
        f"{PLUGGY_BASE_URL}/connect_token", json={}, headers=headers, timeout=30
    )
    response.raise_for_status()
    return response.json()
