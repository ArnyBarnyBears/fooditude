"""Tests for parsing individual recipe modals."""

from bs4 import BeautifulSoup

from scrape_food import parse_recipe_modal, parse_nutrition_table, _NUTR_KEY_MAP_100G, Nutrition


class TestParseNutritionTable:
    def test_extracts_all_seven_fields(self):
        html = """
        <table>
            <tbody>
                <tr><td>Energy (kCal)</td><td>131</td></tr>
                <tr><td>Protein (g)</td><td>4.8</td></tr>
                <tr><td>Carb (g)</td><td>6.3</td></tr>
                <tr><td>of which Sugars (g)</td><td>3.2</td></tr>
                <tr><td>Fat (g)</td><td>9.3</td></tr>
                <tr><td>Sat Fat (g)</td><td>4.2</td></tr>
                <tr><td>Salt (g)</td><td>0.8</td></tr>
            </tbody>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        result = parse_nutrition_table(table, _NUTR_KEY_MAP_100G)
        assert result["energy_kcal_per100g"] == "131"
        assert result["protein_per100g"] == "4.8"
        assert result["salt_per100g"] == "0.8"

    def test_handles_empty_table(self):
        html = "<table><tbody></tbody></table>"
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        result = parse_nutrition_table(table, _NUTR_KEY_MAP_100G)
        assert result == {}

    def test_ignores_unknown_labels(self):
        html = """
        <table><tbody>
            <tr><td>Unknown Field</td><td>99</td></tr>
            <tr><td>Energy (kCal)</td><td>200</td></tr>
        </tbody></table>
        """
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        result = parse_nutrition_table(table, _NUTR_KEY_MAP_100G)
        assert "energy_kcal_per100g" in result
        assert len(result) == 1


class TestParseRecipeModal:
    def test_parses_name(self, single_recipe_html):
        soup = BeautifulSoup(single_recipe_html, "html.parser")
        modal = soup.select_one(".k10-recipe-modal")
        data = parse_recipe_modal(modal)
        assert data["name"] == "Tofu yellow curry"

    def test_parses_suitable_for(self, single_recipe_html):
        soup = BeautifulSoup(single_recipe_html, "html.parser")
        modal = soup.select_one(".k10-recipe-modal")
        data = parse_recipe_modal(modal)
        assert data["suitable_for"] == "Vegan"

    def test_parses_contains(self, single_recipe_html):
        soup = BeautifulSoup(single_recipe_html, "html.parser")
        modal = soup.select_one(".k10-recipe-modal")
        data = parse_recipe_modal(modal)
        assert data["contains"] == "Soya, Sulphur Dioxide/ Sulphites"

    def test_parses_may_contain(self, single_recipe_html):
        soup = BeautifulSoup(single_recipe_html, "html.parser")
        modal = soup.select_one(".k10-recipe-modal")
        data = parse_recipe_modal(modal)
        assert "Mustard" in data["may_contain"]
        assert "Cereals with Gluten" in data["may_contain"]

    def test_parses_ingredients(self, single_recipe_html):
        soup = BeautifulSoup(single_recipe_html, "html.parser")
        modal = soup.select_one(".k10-recipe-modal")
        data = parse_recipe_modal(modal)
        assert "Tofu" in data["ingredients"]
        assert "Coconut Milk" in data["ingredients"]

    def test_parses_nutrition_per100g(self, single_recipe_html):
        soup = BeautifulSoup(single_recipe_html, "html.parser")
        modal = soup.select_one(".k10-recipe-modal")
        data = parse_recipe_modal(modal)
        nutr = data["nutrition"]
        assert nutr.energy_kcal_per100g == "131"
        assert nutr.protein_per100g == "4.8"
        assert nutr.carb_per100g == "6.3"
        assert nutr.sugars_per100g == "3.2"
        assert nutr.fat_per100g == "9.3"
        assert nutr.sat_fat_per100g == "4.2"
        assert nutr.salt_per100g == "0.8"

    def test_parses_nutrition_per_portion(self, single_recipe_html):
        soup = BeautifulSoup(single_recipe_html, "html.parser")
        modal = soup.select_one(".k10-recipe-modal")
        data = parse_recipe_modal(modal)
        nutr = data["nutrition"]
        assert nutr.energy_kcal_per_portion == "304"
        assert nutr.protein_per_portion == "11.2"
        assert nutr.salt_per_portion == "1.9"

    def test_missing_allergens_returns_empty_strings(self):
        """A recipe with no allergen section should still parse cleanly."""
        html = """
        <div class="k10-recipe-modal">
            <div class="k10-recipe-modal__recipe-wrapper">
                <div class="k10-recipe-modal__title">
                    <div class="k10-recipe-modal__title_recipe-name">Plain Rice</div>
                </div>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        modal = soup.select_one(".k10-recipe-modal")
        data = parse_recipe_modal(modal)
        assert data["name"] == "Plain Rice"
        assert data["suitable_for"] == ""
        assert data["contains"] == ""
        assert data["may_contain"] == ""
        assert data["ingredients"] == ""
