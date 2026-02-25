"""Tests for the main scrape_and_export orchestrator."""

from pathlib import Path
from unittest.mock import patch

import pytest

from scrape_food import scrape_and_export


class TestScrapeAndExport:
    def test_creates_csv_files(self, sample_html, tmp_path):
        with patch("scrape_food.fetch_menu_html", return_value=sample_html):
            paths = scrape_and_export(output_dir=tmp_path)

        assert len(paths) == 3
        for p in paths:
            assert p.exists()
            assert p.suffix == ".csv"

    def test_csv_filenames(self, sample_html, tmp_path):
        with patch("scrape_food.fetch_menu_html", return_value=sample_html):
            paths = scrape_and_export(output_dir=tmp_path)

        names = sorted(p.name for p in paths)
        assert "tuesday_menu.csv" in names
        assert "wednesday_menu.csv" in names
        assert "thursday_menu.csv" in names

    def test_csvs_have_content(self, sample_html, tmp_path):
        with patch("scrape_food.fetch_menu_html", return_value=sample_html):
            paths = scrape_and_export(output_dir=tmp_path)

        for p in paths:
            lines = p.read_text().strip().split("\n")
            assert len(lines) >= 2, f"{p.name} should have header + data rows"

    def test_output_dir_created_if_missing(self, sample_html, tmp_path):
        out = tmp_path / "new_dir"
        with patch("scrape_food.fetch_menu_html", return_value=sample_html):
            paths = scrape_and_export(output_dir=out)

        assert out.exists()
        assert len(paths) == 3

    def test_passes_url_to_fetch(self, sample_html, tmp_path):
        with patch("scrape_food.fetch_menu_html", return_value=sample_html) as mock_fetch:
            scrape_and_export(output_dir=tmp_path, url="https://custom.url")
            mock_fetch.assert_called_once_with("https://custom.url")
