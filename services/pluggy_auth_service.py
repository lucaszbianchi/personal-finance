"""
Servico de autenticacao com a Pluggy API.
Responsavel por gerar o apiKey e o connect token.
"""

import requests

from repositories.settings_repository import SettingsRepository

PLUGGY_BASE_URL = "https://api.pluggy.ai"


def _load_credentials() -> tuple:
    """Carrega CLIENT_ID e CLIENT_SECRET do banco de dados (tabela settings)."""
    repo = SettingsRepository()
    try:
        client_id = repo.get_value("pluggy_client_id")
        client_secret = repo.get_value("pluggy_client_secret")
    finally:
        repo.close()
    if not client_id or not client_secret:
        raise ValueError(
            "Credenciais Pluggy nao configuradas. Complete o onboarding primeiro."
        )
    return client_id, client_secret


def get_api_key() -> str:
    """
    Autentica na Pluggy API e retorna um apiKey valido por 2 horas.
    Usado pelo backend para chamadas server-side a API.
    """
    client_id, client_secret = _load_credentials()
    payload = {"clientId": client_id, "clientSecret": client_secret}
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
    Gera um connect token de curta duracao para uso no widget Pluggy Connect.
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
