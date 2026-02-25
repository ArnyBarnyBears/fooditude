"""Integration tests for the pipeline logic (no browser, no network)."""

from pathlib import Path

import pytest

from loseit_automation import FoodEntry, load_foods_from_csv

CSV_HEADER = (
    "name,day,category,suitable_for,contains,may_contain,ingredients,"
    "energy_kcal_per100g,protein_per100g,carb_per100g,sugars_per100g,"
    "fat_per100g,sat_fat_per100g,salt_per100g,"
    "energy_kcal_per_portion,protein_per_portion,carb_per_portion,"
    "sugars_per_portion,fat_per_portion,sat_fat_per_portion,salt_per_portion"
)

def _make_row(name: str, day: str, category: str = "Mains") -> str:
    return f"{name},{day},{category},Vegan,,,Stuff,100,5,10,2,3,1,0.5,200,10,20,4,6,2,1.0"


class TestPipelineCsvLoading:
    def test_discovers_all_csv_files(self, tmp_path):
        for day in ["tuesday", "wednesday", "thursday"]:
            p = tmp_path / f"{day}_menu.csv"
            p.write_text(CSV_HEADER + "\n" + _make_row("Food", day.title()) + "\n")

        csvs = sorted(tmp_path.glob("*_menu.csv"))
        assert len(csvs) == 3

        all_foods = []
        for csv_file in csvs:
            foods = load_foods_from_csv(csv_file, "test")
            all_foods.extend(foods)
        assert len(all_foods) == 3

    def test_food_entry_fields_complete(self):
        food = FoodEntry(
            name="Test Food",
            date_label="Tue 25/02/2026",
            calories="131",
            protein="4.8",
            carbs="6.3",
            sugars="3.2",
            fat="9.3",
            sat_fat="4.2",
            salt="0.8",
        )
        assert food.display_name == "Test Food (Tue 25/02/2026)"
        assert food.sodium_mg == 320.0
        assert food.calories == "131"


class TestDaySelection:
    """Test that loading specific day CSVs works with the pipeline pattern."""

    @pytest.fixture
    def csv_dir(self, tmp_path) -> Path:
        for day in ["tuesday", "wednesday", "thursday"]:
            p = tmp_path / f"{day}_menu.csv"
            p.write_text(CSV_HEADER + "\n" + _make_row(f"{day} food", day.title()) + "\n")
        return tmp_path

    def test_load_single_day(self, csv_dir):
        csvs = sorted(csv_dir.glob("*_menu.csv"))
        target_days = ["tuesday"]
        foods = []
        for csv_file in csvs:
            day_key = csv_file.stem.replace("_menu", "")
            if day_key not in target_days:
                continue
            foods.extend(load_foods_from_csv(csv_file, "test"))
        assert len(foods) == 1
        assert foods[0].name == "tuesday food"

    def test_load_all_days(self, csv_dir):
        csvs = sorted(csv_dir.glob("*_menu.csv"))
        foods = []
        for csv_file in csvs:
            foods.extend(load_foods_from_csv(csv_file, "test"))
        assert len(foods) == 3

    def test_day_filter_with_categories(self, tmp_path):
        p = tmp_path / "tuesday_menu.csv"
        rows = [
            _make_row("Main dish", "Tuesday", "Mains"),
            _make_row("Side dish", "Tuesday", "All served with:"),
            _make_row("Extra", "Tuesday", "Extras"),
        ]
        p.write_text(CSV_HEADER + "\n" + "\n".join(rows) + "\n")

        mains = load_foods_from_csv(p, "test", categories="mains")
        assert len(mains) == 1
        assert mains[0].name == "Main dish"

        mains_extras = load_foods_from_csv(p, "test", categories="mains-extras")
        assert len(mains_extras) == 2
        names = {f.name for f in mains_extras}
        assert names == {"Main dish", "Extra"}


class TestSodiumConversionEdgeCases:
    @pytest.mark.parametrize("salt_g,expected_mg", [
        ("0.0", 0.0),
        ("0.5", 200.0),
        ("1.0", 400.0),
        ("1.5", 600.0),
        ("2.5", 1000.0),
        ("0.1", 40.0),
    ])
    def test_various_salt_values(self, salt_g, expected_mg):
        food = FoodEntry(
            name="x", date_label="x",
            calories="0", protein="0", carbs="0",
            sugars="0", fat="0", sat_fat="0", salt=salt_g,
        )
        assert food.sodium_mg == expected_mg
