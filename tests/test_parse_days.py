"""Tests for parsing the full page into per-day food item lists."""

import pytest

from scrape_food import parse_day_sections, FoodItem


class TestParseDaySections:
    def test_returns_three_days(self, sample_html):
        result = parse_day_sections(sample_html)
        assert "Tuesday" in result
        assert "Wednesday" in result
        assert "Thursday" in result

    def test_no_extra_days(self, sample_html):
        result = parse_day_sections(sample_html)
        assert len(result) == 3

    def test_tuesday_has_items(self, sample_html):
        result = parse_day_sections(sample_html)
        assert len(result["Tuesday"]) > 0

    def test_wednesday_has_items(self, sample_html):
        result = parse_day_sections(sample_html)
        assert len(result["Wednesday"]) > 0

    def test_thursday_has_items(self, sample_html):
        result = parse_day_sections(sample_html)
        assert len(result["Thursday"]) > 0

    def test_all_items_are_food_items(self, sample_html):
        result = parse_day_sections(sample_html)
        for day, items in result.items():
            for item in items:
                assert isinstance(item, FoodItem), f"{item} is not a FoodItem"

    def test_every_item_has_a_name(self, sample_html):
        result = parse_day_sections(sample_html)
        for day, items in result.items():
            for item in items:
                assert item.name, f"Item in {day} has empty name"

    def test_every_item_has_correct_day(self, sample_html):
        result = parse_day_sections(sample_html)
        for day, items in result.items():
            for item in items:
                assert item.day == day

    def test_every_item_has_a_category(self, sample_html):
        result = parse_day_sections(sample_html)
        for day, items in result.items():
            for item in items:
                assert item.category, f"{item.name} has no category"


class TestTuesdaySpecificItems:
    """Verify specific known items from Tuesday's menu appear correctly."""

    def test_tofu_yellow_curry_present(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        names = [i.name for i in items]
        assert "Tofu yellow curry" in names

    def test_tofu_curry_is_vegan(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        tofu = next(i for i in items if i.name == "Tofu yellow curry")
        assert tofu.suitable_for == "Vegan"

    def test_tofu_curry_contains_soya(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        tofu = next(i for i in items if i.name == "Tofu yellow curry")
        assert "Soya" in tofu.contains

    def test_tofu_curry_nutrition_per100g(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        tofu = next(i for i in items if i.name == "Tofu yellow curry")
        assert tofu.nutrition.energy_kcal_per100g == "131"
        assert tofu.nutrition.protein_per100g == "4.8"
        assert tofu.nutrition.salt_per100g == "0.8"

    def test_tofu_curry_nutrition_per_portion(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        tofu = next(i for i in items if i.name == "Tofu yellow curry")
        assert tofu.nutrition.energy_kcal_per_portion == "304"

    def test_tofu_curry_category_is_mains(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        tofu = next(i for i in items if i.name == "Tofu yellow curry")
        assert tofu.category == "Mains"

    def test_tofu_curry_has_ingredients(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        tofu = next(i for i in items if i.name == "Tofu yellow curry")
        assert "Tofu" in tofu.ingredients
        assert len(tofu.ingredients) > 50

    def test_corn_fritters_present(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        names = [i.name for i in items]
        assert "Corn fritters" in names

    def test_thai_red_chicken_curry_present(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        names = [i.name for i in items]
        assert "Thai red chicken curry" in names

    def test_jasmine_rice_in_served_with(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        rice = next(i for i in items if i.name == "Jasmine rice")
        assert rice.category == "All served with:"

    def test_tortilla_soup_in_soup(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        soup_item = next(i for i in items if i.name == "Tortilla soup")
        assert soup_item.category == "Soup"

    def test_leafy_salad_in_salads(self, sample_html):
        items = parse_day_sections(sample_html)["Tuesday"]
        salad = next(i for i in items if i.name == "Leafy salad, sesame dressing")
        assert salad.category == "Salads"


class TestWednesdaySpecificItems:
    def test_gnocchi_present(self, sample_html):
        items = parse_day_sections(sample_html)["Wednesday"]
        names = [i.name for i in items]
        assert "Mixed mushroom & truffle gnocchi" in names

    def test_beef_bolognese_present(self, sample_html):
        items = parse_day_sections(sample_html)["Wednesday"]
        names = [i.name for i in items]
        assert "Beef Bolognese" in names

    def test_garlic_ciabatta_in_extras(self, sample_html):
        items = parse_day_sections(sample_html)["Wednesday"]
        ciabatta = next(i for i in items if i.name == "Garlic ciabatta")
        assert ciabatta.category == "Extras"

    def test_farfalle_in_served_with(self, sample_html):
        items = parse_day_sections(sample_html)["Wednesday"]
        farfalle = next(i for i in items if i.name == "Farfalle")
        assert farfalle.category == "All served with:"


class TestThursdaySpecificItems:
    def test_quinoa_meatballs_present(self, sample_html):
        items = parse_day_sections(sample_html)["Thursday"]
        names = [i.name for i in items]
        assert "Quinoa & mushroom meatballs" in names

    def test_pork_belly_present(self, sample_html):
        items = parse_day_sections(sample_html)["Thursday"]
        names = [i.name for i in items]
        assert "Slow roasted thyme & rosemary pork belly" in names

    def test_thursday_has_extras(self, sample_html):
        items = parse_day_sections(sample_html)["Thursday"]
        extras = [i for i in items if i.category == "Extras"]
        assert len(extras) > 0

    def test_potato_wedges_in_served_with(self, sample_html):
        items = parse_day_sections(sample_html)["Thursday"]
        wedges = next(i for i in items if i.name == "Garlic & rosemary potato wedges")
        assert wedges.category == "All served with:"

    def test_cheesy_cauliflower_soup(self, sample_html):
        items = parse_day_sections(sample_html)["Thursday"]
        soup_item = next(i for i in items if i.name == "Cheesy cauliflower soup")
        assert soup_item.category == "Soup"
        assert "Milk" in soup_item.contains


class TestDayNormalisation:
    def test_thursday_byo_normalised(self, sample_html):
        """'Thursday - BYO Hot Sandwiches' should normalise to 'Thursday'."""
        result = parse_day_sections(sample_html)
        assert "Thursday" in result
        assert "Thursday - BYO Hot Sandwiches" not in result
