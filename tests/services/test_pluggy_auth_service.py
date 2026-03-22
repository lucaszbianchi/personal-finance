import unittest
from unittest.mock import MagicMock, patch
from requests import HTTPError
import services.pluggy_auth_service as auth_service


class TestGetApiKey(unittest.TestCase):
    @patch("services.pluggy_auth_service.requests.post")
    @patch(
        "services.pluggy_auth_service._load_credentials",
        return_value=("my-id", "my-secret"),
    )
    def test_returns_api_key_on_success(self, _mock_creds, mock_post):
        mock_post.return_value = MagicMock(
            raise_for_status=lambda: None,
            json=lambda: {"apiKey": "test-key-123"},
        )

        result = auth_service.get_api_key()

        self.assertEqual(result, "test-key-123")

    @patch("services.pluggy_auth_service.requests.post")
    @patch(
        "services.pluggy_auth_service._load_credentials",
        return_value=("my-id", "my-secret"),
    )
    def test_posts_to_auth_endpoint(self, _mock_creds, mock_post):
        mock_post.return_value = MagicMock(
            raise_for_status=lambda: None,
            json=lambda: {"apiKey": "key"},
        )

        auth_service.get_api_key()

        url = mock_post.call_args[0][0]
        self.assertIn("/auth", url)

    @patch("services.pluggy_auth_service.requests.post")
    @patch(
        "services.pluggy_auth_service._load_credentials",
        return_value=("my-id", "my-secret"),
    )
    def test_raises_on_http_error(self, _mock_creds, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response

        with self.assertRaises(HTTPError):
            auth_service.get_api_key()

    @patch("services.pluggy_auth_service.requests.post")
    @patch(
        "services.pluggy_auth_service._load_credentials",
        return_value=("my-id", "my-secret"),
    )
    def test_sends_client_credentials_from_db(self, _mock_creds, mock_post):
        mock_post.return_value = MagicMock(
            raise_for_status=lambda: None,
            json=lambda: {"apiKey": "key"},
        )

        auth_service.get_api_key()

        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["clientId"], "my-id")
        self.assertEqual(payload["clientSecret"], "my-secret")

    def test_load_credentials_raises_when_not_configured(self):
        with patch(
            "services.pluggy_auth_service.SettingsRepository"
        ) as MockRepo:
            instance = MockRepo.return_value
            instance.get_value.return_value = None
            instance.close = MagicMock()

            with self.assertRaises(ValueError):
                auth_service._load_credentials()


class TestGetItem(unittest.TestCase):
    @patch("services.pluggy_auth_service.requests.get")
    @patch("services.pluggy_auth_service.get_api_key", return_value="api-key")
    def test_returns_item_data(self, _mock_key, mock_get):
        expected = {"id": "item-1", "status": "UPDATED"}
        mock_get.return_value = MagicMock(
            raise_for_status=lambda: None,
            json=lambda: expected,
        )

        result = auth_service.get_item("item-1")

        self.assertEqual(result, expected)

    @patch("services.pluggy_auth_service.requests.get")
    @patch("services.pluggy_auth_service.get_api_key", return_value="api-key")
    def test_raises_on_http_error(self, _mock_key, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with self.assertRaises(HTTPError):
            auth_service.get_item("item-inexistente")

    @patch("services.pluggy_auth_service.requests.get")
    @patch("services.pluggy_auth_service.get_api_key", return_value="api-key")
    def test_sends_api_key_header(self, _mock_key, mock_get):
        mock_get.return_value = MagicMock(
            raise_for_status=lambda: None,
            json=lambda: {},
        )

        auth_service.get_item("item-1")

        headers = mock_get.call_args[1]["headers"]
        self.assertEqual(headers["X-API-KEY"], "api-key")


class TestCreateConnectToken(unittest.TestCase):
    @patch("services.pluggy_auth_service.requests.post")
    @patch("services.pluggy_auth_service.get_api_key", return_value="api-key")
    def test_returns_token_data(self, _mock_key, mock_post):
        expected = {"accessToken": "token-abc", "expiresAt": "2026-03-09T00:00:00Z"}
        mock_post.return_value = MagicMock(
            raise_for_status=lambda: None,
            json=lambda: expected,
        )

        result = auth_service.create_connect_token()

        self.assertEqual(result, expected)

    @patch("services.pluggy_auth_service.requests.post")
    @patch("services.pluggy_auth_service.get_api_key", return_value="api-key")
    def test_posts_to_connect_token_endpoint(self, _mock_key, mock_post):
        mock_post.return_value = MagicMock(
            raise_for_status=lambda: None,
            json=lambda: {},
        )

        auth_service.create_connect_token()

        url = mock_post.call_args[0][0]
        self.assertIn("connect_token", url)

    @patch("services.pluggy_auth_service.requests.post")
    @patch("services.pluggy_auth_service.get_api_key", return_value="api-key")
    def test_raises_on_http_error(self, _mock_key, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("500")
        mock_post.return_value = mock_response

        with self.assertRaises(HTTPError):
            auth_service.create_connect_token()


if __name__ == "__main__":
    unittest.main()
