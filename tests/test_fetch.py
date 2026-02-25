"""Tests for the HTML fetching function."""

from unittest.mock import patch, MagicMock

import pytest

from scrape_food import fetch_menu_html, MENU_URL


class TestFetchMenuHtml:
    def test_returns_html_string(self):
        """fetch_menu_html should return the response text."""
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>Hello</body></html>"
        mock_resp.raise_for_status = MagicMock()

        with patch("scrape_food.requests.get", return_value=mock_resp) as mock_get:
            result = fetch_menu_html()
            mock_get.assert_called_once_with(MENU_URL, timeout=30)
            assert result == "<html><body>Hello</body></html>"

    def test_uses_custom_url(self):
        """Should pass custom URL to requests.get."""
        mock_resp = MagicMock()
        mock_resp.text = "custom"
        mock_resp.raise_for_status = MagicMock()

        with patch("scrape_food.requests.get", return_value=mock_resp) as mock_get:
            fetch_menu_html(url="https://example.com")
            mock_get.assert_called_once_with("https://example.com", timeout=30)

    def test_raises_on_http_error(self):
        """Should propagate HTTP errors via raise_for_status."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("404")

        with patch("scrape_food.requests.get", return_value=mock_resp):
            with pytest.raises(Exception, match="404"):
                fetch_menu_html()

    def test_custom_timeout(self):
        """Should respect the timeout parameter."""
        mock_resp = MagicMock()
        mock_resp.text = "ok"
        mock_resp.raise_for_status = MagicMock()

        with patch("scrape_food.requests.get", return_value=mock_resp) as mock_get:
            fetch_menu_html(timeout=10)
            mock_get.assert_called_once_with(MENU_URL, timeout=10)
