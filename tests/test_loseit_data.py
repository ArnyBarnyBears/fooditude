"""Tests for Lose It automation data loading and utilities (no browser needed)."""

import csv
from pathlib import Path

import pytest

from loseit_automation import FoodEntry, load_foods_from_csv


@pytest.fixture
def sample_csv(tmp_path) -> Path:
    """Create a sample menu CSV matching scraper output format."""
    csv_path = tmp_path / "tuesday_menu.csv"
    rows = [
        {
            "name": "Tofu yellow curry",
            "day": "Tuesday",
            "category": "Mains",
            "suitable_for": "Vegan",
            "contains": "Soya",
            "may_contain": "Mustard",
            "ingredients": "Tofu; Coconut",
            "energy_kcal_per100g": "131",
            "protein_per100g": "4.8",
            "carb_per100g": "6.3",
            "sugars_per100g": "3.2",
            "fat_per100g": "9.3",
            "sat_fat_per100g": "4.2",
            "salt_per100g": "0.8",
            "energy_kcal_per_portion": "304",
            "protein_per_portion": "11.2",
            "carb_per_portion": "14.7",
            "sugars_per_portion": "7.4",
            "fat_per_portion": "21.7",
            "sat_fat_per_portion": "9.7",
            "salt_per_portion": "1.9",
        },
        {
            "name": "Jasmine rice",
            "day": "Tuesday",
            "category": "All served with:",
            "suitable_for": "Vegan",
            "contains": "",
            "may_contain": "",
            "ingredients": "Rice",
            "energy_kcal_per100g": "145",
            "protein_per100g": "3.3",
            "carb_per100g": "32.3",
            "sugars_per100g": "0.2",
            "fat_per100g": "0.2",
            "sat_fat_per100g": "0.1",
            "salt_per100g": "0.0",
            "energy_kcal_per_portion": "145",
            "protein_per_portion": "3.3",
            "carb_per_portion": "32.3",
            "sugars_per_portion": "0.2",
            "fat_per_portion": "0.3",
            "sat_fat_per_portion": "0.1",
            "salt_per_portion": "0.0",
        },
    ]
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


@pytest.fixture
def multi_category_csv(tmp_path) -> Path:
    """CSV with items across Mains, Extras, Salads, Soup, All served with."""
    csv_path = tmp_path / "wednesday_menu.csv"
    template = (
        "name,day,category,suitable_for,contains,may_contain,ingredients,"
        "energy_kcal_per100g,protein_per100g,carb_per100g,sugars_per100g,"
        "fat_per100g,sat_fat_per100g,salt_per100g,"
        "energy_kcal_per_portion,protein_per_portion,carb_per_portion,"
        "sugars_per_portion,fat_per_portion,sat_fat_per_portion,salt_per_portion\n"
    )
    rows = [
        "Gnocchi,Wednesday,Mains,Vegan,,,Stuff,100,5,10,2,3,1,0.5,200,10,20,4,6,2,1.0",
        "Bolognese,Wednesday,Mains,,,,Stuff,100,5,10,2,3,1,0.5,200,10,20,4,6,2,1.0",
        "Ciabatta,Wednesday,Extras,Vegan,,,Stuff,100,5,10,2,3,1,0.5,200,10,20,4,6,2,1.0",
        "Farfalle,Wednesday,All served with:,Vegan,,,Stuff,100,5,10,2,3,1,0.5,200,10,20,4,6,2,1.0",
        "Feta salad,Wednesday,Salads,,,,Stuff,100,5,10,2,3,1,0.5,200,10,20,4,6,2,1.0",
        "Squash soup,Wednesday,Soup,Vegan,,,Stuff,100,5,10,2,3,1,0.5,200,10,20,4,6,2,1.0",
    ]
    csv_path.write_text(template + "\n".join(rows) + "\n")
    return csv_path


class TestFoodEntry:
    def test_display_name(self):
        food = FoodEntry(
            name="Tofu curry", date_label="Tue 25/02/2026",
            calories="131", protein="4.8", carbs="6.3",
            sugars="3.2", fat="9.3", sat_fat="4.2", salt="0.8",
        )
        assert food.display_name == "Tofu curry (Tue 25/02/2026)"

    def test_sodium_conversion(self):
        food = FoodEntry(
            name="Test", date_label="x",
            calories="0", protein="0", carbs="0",
            sugars="0", fat="0", sat_fat="0", salt="1.0",
        )
        assert food.sodium_mg == 400.0

    def test_sodium_conversion_fractional(self):
        food = FoodEntry(
            name="Test", date_label="x",
            calories="0", protein="0", carbs="0",
            sugars="0", fat="0", sat_fat="0", salt="0.8",
        )
        assert food.sodium_mg == 320.0

    def test_sodium_zero_salt(self):
        food = FoodEntry(
            name="Test", date_label="x",
            calories="0", protein="0", carbs="0",
            sugars="0", fat="0", sat_fat="0", salt="0.0",
        )
        assert food.sodium_mg == 0.0

    def test_sodium_empty_salt(self):
        food = FoodEntry(
            name="Test", date_label="x",
            calories="0", protein="0", carbs="0",
            sugars="0", fat="0", sat_fat="0", salt="",
        )
        assert food.sodium_mg == 0.0


class TestLoadFoodsFromCsv:
    def test_loads_correct_count(self, sample_csv):
        foods = load_foods_from_csv(sample_csv, "Tue 25/02/2026")
        assert len(foods) == 2

    def test_first_item_name(self, sample_csv):
        foods = load_foods_from_csv(sample_csv, "Tue 25/02/2026")
        assert foods[0].name == "Tofu yellow curry"

    def test_date_label_applied(self, sample_csv):
        foods = load_foods_from_csv(sample_csv, "Tue 25/02/2026")
        assert foods[0].date_label == "Tue 25/02/2026"
        assert foods[1].date_label == "Tue 25/02/2026"

    def test_uses_per100g_values(self, sample_csv):
        foods = load_foods_from_csv(sample_csv, "x")
        tofu = foods[0]
        assert tofu.calories == "131"
        assert tofu.protein == "4.8"
        assert tofu.carbs == "6.3"
        assert tofu.sugars == "3.2"
        assert tofu.fat == "9.3"
        assert tofu.sat_fat == "4.2"
        assert tofu.salt == "0.8"

    def test_display_name_includes_date(self, sample_csv):
        foods = load_foods_from_csv(sample_csv, "Tue 25/02/2026")
        assert foods[0].display_name == "Tofu yellow curry (Tue 25/02/2026)"

    def test_sodium_computed_correctly(self, sample_csv):
        foods = load_foods_from_csv(sample_csv, "x")
        tofu = foods[0]
        assert tofu.sodium_mg == 320.0

    def test_empty_csv(self, tmp_path):
        csv_path = tmp_path / "empty.csv"
        headers = "name,day,category,suitable_for,contains,may_contain,ingredients,"
        headers += "energy_kcal_per100g,protein_per100g,carb_per100g,sugars_per100g,"
        headers += "fat_per100g,sat_fat_per100g,salt_per100g,"
        headers += "energy_kcal_per_portion,protein_per_portion,carb_per_portion,"
        headers += "sugars_per_portion,fat_per_portion,sat_fat_per_portion,salt_per_portion"
        csv_path.write_text(headers + "\n")
        foods = load_foods_from_csv(csv_path, "x")
        assert len(foods) == 0


class TestCategoryFiltering:
    """Test the categories parameter of load_foods_from_csv."""

    def test_all_returns_everything(self, multi_category_csv):
        foods = load_foods_from_csv(multi_category_csv, "x", categories="all")
        assert len(foods) == 6

    def test_mains_only(self, multi_category_csv):
        foods = load_foods_from_csv(multi_category_csv, "x", categories="mains")
        assert len(foods) == 2
        assert all(f.name in ("Gnocchi", "Bolognese") for f in foods)

    def test_mains_extras(self, multi_category_csv):
        foods = load_foods_from_csv(multi_category_csv, "x", categories="mains-extras")
        assert len(foods) == 3
        names = {f.name for f in foods}
        assert names == {"Gnocchi", "Bolognese", "Ciabatta"}

    def test_mains_excludes_sides_and_salads(self, multi_category_csv):
        foods = load_foods_from_csv(multi_category_csv, "x", categories="mains")
        names = {f.name for f in foods}
        assert "Farfalle" not in names
        assert "Feta salad" not in names
        assert "Squash soup" not in names

    def test_default_is_all(self, multi_category_csv):
        foods_default = load_foods_from_csv(multi_category_csv, "x")
        foods_all = load_foods_from_csv(multi_category_csv, "x", categories="all")
        assert len(foods_default) == len(foods_all)


class TestLoadFromRealScraperOutput:
    """Test loading from actual scraper CSVs if they exist."""

    @pytest.fixture
    def output_dir(self) -> Path:
        p = Path("output")
        if not p.exists() or not list(p.glob("*_menu.csv")):
            pytest.skip("No scraper output in output/ — run scrape_food.py first")
        return p

    def test_load_tuesday(self, output_dir):
        csv_path = output_dir / "tuesday_menu.csv"
        if not csv_path.exists():
            pytest.skip("tuesday_menu.csv not found")
        foods = load_foods_from_csv(csv_path, "Tue 25/02/2026")
        assert len(foods) > 0
        assert all(f.name for f in foods)
        assert all(f.calories for f in foods)

    def test_load_all_days(self, output_dir):
        day_map = {"tuesday": "Tue", "wednesday": "Wed", "thursday": "Thu"}
        total = 0
        for csv_file in output_dir.glob("*_menu.csv"):
            day_key = csv_file.stem.replace("_menu", "")
            day_short = day_map.get(day_key, day_key)
            foods = load_foods_from_csv(csv_file, f"{day_short} 25/02/2026")
            assert len(foods) > 0, f"No foods in {csv_file.name}"
            total += len(foods)
        assert total > 0

    def test_mains_filter_on_real_data(self, output_dir):
        csv_path = output_dir / "tuesday_menu.csv"
        if not csv_path.exists():
            pytest.skip("tuesday_menu.csv not found")
        all_foods = load_foods_from_csv(csv_path, "x", categories="all")
        mains_foods = load_foods_from_csv(csv_path, "x", categories="mains")
        assert len(mains_foods) < len(all_foods)
        assert len(mains_foods) > 0
