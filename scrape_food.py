"""
Fooditude menu scraper.

Fetches the weekly lunch menu from menus.tenkites.com/fooditude/tradedesk,
parses food items by day (Tuesday/Wednesday/Thursday), and outputs per-day
CSV files with name, category, dietary info, allergens, ingredients, and
full nutritional breakdown.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field, asdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

MENU_URL = "https://menus.tenkites.com/fooditude/tradedesk"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Nutrition:
    energy_kcal_per100g: str = ""
    protein_per100g: str = ""
    carb_per100g: str = ""
    sugars_per100g: str = ""
    fat_per100g: str = ""
    sat_fat_per100g: str = ""
    salt_per100g: str = ""
    energy_kcal_per_portion: str = ""
    protein_per_portion: str = ""
    carb_per_portion: str = ""
    sugars_per_portion: str = ""
    fat_per_portion: str = ""
    sat_fat_per_portion: str = ""
    salt_per_portion: str = ""


@dataclass
class FoodItem:
    name: str
    day: str
    category: str  # e.g. Mains, Salads, Soup, All served with, Extras
    suitable_for: str = ""
    contains: str = ""
    may_contain: str = ""
    ingredients: str = ""
    nutrition: Nutrition = field(default_factory=Nutrition)


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_menu_html(url: str = MENU_URL, timeout: int = 30) -> str:
    """Fetch the raw HTML of the menu page."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_NUTR_KEY_MAP_100G = {
    "Energy (kCal)": "energy_kcal_per100g",
    "Protein (g)": "protein_per100g",
    "Carb (g)": "carb_per100g",
    "of which Sugars (g)": "sugars_per100g",
    "Fat (g)": "fat_per100g",
    "Sat Fat (g)": "sat_fat_per100g",
    "Salt (g)": "salt_per100g",
}

_NUTR_KEY_MAP_PORTION = {
    "Energy (kCal)": "energy_kcal_per_portion",
    "Protein (g)": "protein_per_portion",
    "Carb (g)": "carb_per_portion",
    "of which Sugars (g)": "sugars_per_portion",
    "Fat (g)": "fat_per_portion",
    "Sat Fat (g)": "sat_fat_per_portion",
    "Salt (g)": "salt_per_portion",
}


def parse_nutrition_table(table: Tag, key_map: dict[str, str]) -> dict[str, str]:
    """Extract nutrition key/value pairs from a <table> Tag."""
    result: dict[str, str] = {}
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == 2:
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            attr = key_map.get(label)
            if attr:
                result[attr] = value
    return result


def parse_recipe_modal(modal: Tag) -> dict:
    """
    Parse a single k10-recipe-modal div into a dict with:
    name, suitable_for, contains, may_contain, ingredients, nutrition.
    """
    data: dict = {}

    # Name
    name_el = modal.select_one(".k10-recipe-modal__title_recipe-name")
    data["name"] = name_el.get_text(strip=True) if name_el else ""

    # Allergens
    suitable_el = modal.select_one(".k10-recipe-modal__allergens_suitable .k10-recipe-modal__allergens_value")
    data["suitable_for"] = suitable_el.get_text(strip=True) if suitable_el else ""

    contains_el = modal.select_one(".k10-recipe-modal__allergens_contains .k10-recipe-modal__allergens_value")
    data["contains"] = contains_el.get_text(strip=True) if contains_el else ""

    may_el = modal.select_one(".k10-recipe-modal__allergens_may .k10-recipe-modal__allergens_value")
    data["may_contain"] = may_el.get_text(strip=True) if may_el else ""

    # Ingredients
    ingr_el = modal.select_one(".k10-recipe-modal__ingredient-section .k10-w-recipe__ingredient")
    data["ingredients"] = ingr_el.get_text(strip=True) if ingr_el else ""

    # Nutrition — two tables: per 100g then per portion
    nutr = Nutrition()
    nutrient_divs = modal.select(".k10-recipe-modal__nutrients")
    for ndiv in nutrient_divs:
        caption = ndiv.select_one(".k10-recipe-modal__nutrients-caption")
        if not caption:
            continue
        caption_text = caption.get_text(strip=True)
        table = ndiv.select_one("table")
        if not table:
            continue
        if "per 100g" in caption_text:
            for k, v in parse_nutrition_table(table, _NUTR_KEY_MAP_100G).items():
                setattr(nutr, k, v)
        elif "per portion" in caption_text:
            for k, v in parse_nutrition_table(table, _NUTR_KEY_MAP_PORTION).items():
                setattr(nutr, k, v)

    data["nutrition"] = nutr
    return data


def parse_day_sections(html: str) -> dict[str, list[FoodItem]]:
    """
    Parse full page HTML and return a dict mapping day name
    (e.g. 'Tuesday') to a list of FoodItem instances.
    """
    soup = BeautifulSoup(html, "html.parser")

    day_sections: dict[str, list[FoodItem]] = {}

    level1_sections = soup.select("section.k10-course_level_1")

    for section in level1_sections:
        day_header = section.select_one("h2.k10-course__name")
        if not day_header:
            continue
        day_name = day_header.get_text(strip=True)
        # Normalise: "Thursday - BYO Hot Sandwiches" → "Thursday"
        day_short = day_name.split(" - ")[0].split(" –")[0].strip()

        items: list[FoodItem] = []

        level2_sections = section.select(".k10-course_level_2")
        for l2 in level2_sections:
            cat_header = l2.select_one("h2.k10-course__name")
            category = cat_header.get_text(strip=True) if cat_header else "Uncategorised"

            # Collect recipe-ids from level-3 so we can skip them at level-2
            l3_recipe_ids: set[str] = set()
            for l3 in l2.select(".k10-course_level_3"):
                for modal in l3.select(".k10-recipe-modal"):
                    rid = modal.get("data-recipe-id", "")
                    if rid:
                        l3_recipe_ids.add(rid)

            # Recipes directly in this level-2 section (not inside a level-3)
            for modal in l2.select(".k10-recipe-modal"):
                rid = modal.get("data-recipe-id", "")
                if rid in l3_recipe_ids:
                    continue
                parsed = parse_recipe_modal(modal)
                items.append(FoodItem(
                    name=parsed["name"],
                    day=day_short,
                    category=category,
                    suitable_for=parsed["suitable_for"],
                    contains=parsed["contains"],
                    may_contain=parsed["may_contain"],
                    ingredients=parsed["ingredients"],
                    nutrition=parsed["nutrition"],
                ))

            # Level-3 sub-sections (e.g. Extras nested under Mains)
            for l3 in l2.select(".k10-course_level_3"):
                sub_header = l3.select_one("h2.k10-course__name")
                sub_category = sub_header.get_text(strip=True) if sub_header else category
                for modal in l3.select(".k10-recipe-modal"):
                    parsed = parse_recipe_modal(modal)
                    items.append(FoodItem(
                        name=parsed["name"],
                        day=day_short,
                        category=sub_category,
                        suitable_for=parsed["suitable_for"],
                        contains=parsed["contains"],
                        may_contain=parsed["may_contain"],
                        ingredients=parsed["ingredients"],
                        nutrition=parsed["nutrition"],
                    ))

        day_sections[day_short] = items

    return day_sections


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "name",
    "day",
    "category",
    "suitable_for",
    "contains",
    "may_contain",
    "ingredients",
    "energy_kcal_per100g",
    "protein_per100g",
    "carb_per100g",
    "sugars_per100g",
    "fat_per100g",
    "sat_fat_per100g",
    "salt_per100g",
    "energy_kcal_per_portion",
    "protein_per_portion",
    "carb_per_portion",
    "sugars_per_portion",
    "fat_per_portion",
    "sat_fat_per_portion",
    "salt_per_portion",
]


def food_item_to_row(item: FoodItem) -> dict[str, str]:
    """Flatten a FoodItem into a dict suitable for csv.DictWriter."""
    row = {
        "name": item.name,
        "day": item.day,
        "category": item.category,
        "suitable_for": item.suitable_for,
        "contains": item.contains,
        "may_contain": item.may_contain,
        "ingredients": item.ingredients,
    }
    nutr = asdict(item.nutrition)
    row.update(nutr)
    return row


def write_csv(items: list[FoodItem], path: Path) -> Path:
    """Write a list of FoodItems to a CSV file. Returns the path written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for item in items:
            writer.writerow(food_item_to_row(item))
    return path


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def scrape_and_export(output_dir: Path | str = Path("output"), url: str = MENU_URL) -> list[Path]:
    """
    End-to-end: fetch menu, parse all days, write one CSV per day.
    Returns list of CSV file paths created.
    """
    output_dir = Path(output_dir)
    html = fetch_menu_html(url)
    day_sections = parse_day_sections(html)

    created: list[Path] = []
    for day, items in day_sections.items():
        if not items:
            continue
        csv_path = output_dir / f"{day.lower()}_menu.csv"
        write_csv(items, csv_path)
        created.append(csv_path)
        print(f"  ✓ {csv_path}  ({len(items)} items)")

    return created


if __name__ == "__main__":
    print("Scraping Fooditude menu...")
    paths = scrape_and_export()
    print(f"\nDone — wrote {len(paths)} CSV file(s).")
