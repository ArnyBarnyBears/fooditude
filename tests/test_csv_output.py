"""Tests for CSV generation."""

import csv
from pathlib import Path

import pytest

from scrape_food import (
    write_csv,
    food_item_to_row,
    FoodItem,
    Nutrition,
    CSV_COLUMNS,
    parse_day_sections,
)


@pytest.fixture
def sample_item() -> FoodItem:
    return FoodItem(
        name="Tofu yellow curry",
        day="Tuesday",
        category="Mains",
        suitable_for="Vegan",
        contains="Soya",
        may_contain="Mustard",
        ingredients="Tofu; Coconut Milk",
        nutrition=Nutrition(
            energy_kcal_per100g="131",
            protein_per100g="4.8",
            carb_per100g="6.3",
            sugars_per100g="3.2",
            fat_per100g="9.3",
            sat_fat_per100g="4.2",
            salt_per100g="0.8",
            energy_kcal_per_portion="304",
            protein_per_portion="11.2",
            carb_per_portion="14.7",
            sugars_per_portion="7.4",
            fat_per_portion="21.7",
            sat_fat_per_portion="9.7",
            salt_per_portion="1.9",
        ),
    )


class TestFoodItemToRow:
    def test_returns_dict(self, sample_item):
        row = food_item_to_row(sample_item)
        assert isinstance(row, dict)

    def test_has_all_csv_columns(self, sample_item):
        row = food_item_to_row(sample_item)
        for col in CSV_COLUMNS:
            assert col in row, f"Missing column: {col}"

    def test_name_matches(self, sample_item):
        row = food_item_to_row(sample_item)
        assert row["name"] == "Tofu yellow curry"

    def test_nutrition_values_flattened(self, sample_item):
        row = food_item_to_row(sample_item)
        assert row["energy_kcal_per100g"] == "131"
        assert row["protein_per_portion"] == "11.2"

    def test_allergen_fields(self, sample_item):
        row = food_item_to_row(sample_item)
        assert row["suitable_for"] == "Vegan"
        assert row["contains"] == "Soya"
        assert row["may_contain"] == "Mustard"


class TestWriteCsv:
    def test_creates_file(self, tmp_path, sample_item):
        out = tmp_path / "test.csv"
        result = write_csv([sample_item], out)
        assert result.exists()

    def test_creates_parent_dirs(self, tmp_path, sample_item):
        out = tmp_path / "sub" / "dir" / "test.csv"
        write_csv([sample_item], out)
        assert out.exists()

    def test_header_matches_columns(self, tmp_path, sample_item):
        out = tmp_path / "test.csv"
        write_csv([sample_item], out)
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header == CSV_COLUMNS

    def test_single_data_row(self, tmp_path, sample_item):
        out = tmp_path / "test.csv"
        write_csv([sample_item], out)
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["name"] == "Tofu yellow curry"
        assert rows[0]["energy_kcal_per100g"] == "131"

    def test_multiple_items(self, tmp_path, sample_item):
        item2 = FoodItem(
            name="Corn fritters",
            day="Tuesday",
            category="Mains",
            nutrition=Nutrition(),
        )
        out = tmp_path / "test.csv"
        write_csv([sample_item, item2], out)
        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[1]["name"] == "Corn fritters"

    def test_empty_list_writes_header_only(self, tmp_path):
        out = tmp_path / "test.csv"
        write_csv([], out)
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            data_rows = list(reader)
        assert header == CSV_COLUMNS
        assert len(data_rows) == 0


class TestEndToEndCsv:
    """Parse real fixture HTML and write CSVs to verify round-trip."""

    def test_write_tuesday_csv(self, sample_html, tmp_path):
        days = parse_day_sections(sample_html)
        out = tmp_path / "tuesday.csv"
        write_csv(days["Tuesday"], out)

        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        names = [r["name"] for r in rows]
        assert "Tofu yellow curry" in names
        assert "Jasmine rice" in names

        tofu_row = next(r for r in rows if r["name"] == "Tofu yellow curry")
        assert tofu_row["energy_kcal_per100g"] == "131"
        assert tofu_row["suitable_for"] == "Vegan"

    def test_write_all_three_days(self, sample_html, tmp_path):
        days = parse_day_sections(sample_html)
        for day_name, items in days.items():
            out = tmp_path / f"{day_name.lower()}.csv"
            write_csv(items, out)
            assert out.exists()
            with open(out, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) > 0, f"{day_name} CSV has no rows"
