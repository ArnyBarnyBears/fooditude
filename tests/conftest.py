from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_html() -> str:
    """Full HTML from the live Fooditude menu page (saved as fixture)."""
    return (FIXTURES_DIR / "sample_menu.html").read_text(encoding="utf-8")


@pytest.fixture
def single_recipe_html() -> str:
    """Minimal HTML containing exactly one recipe modal (Tofu yellow curry)."""
    return """
    <div class="k10-recipe-modal modal fade" data-recipe-id="74999">
        <div class="modal-dialog modal-lg k10-recipe-modal__wrapper" role="document">
            <div class="modal-content"><div>
                <div class="modal-body k10-recipe-modal__body">
                    <div class="k10-recipe-modal__recipe-wrapper">
                        <div class="k10-recipe-modal__title">
                            <div class="k10-recipe-modal__title_recipe-name">Tofu yellow curry</div>
                        </div>
                        <div class="k10-recipe-modal__allergens">
                            <div class="k10-recipe-modal__section k10-recipe-modal__allergens-section">
                                <div class="k10-recipe-modal__allergens-section_row k10-recipe-modal__allergens_suitable">
                                    <div class="k10-recipe-modal__allergens-caption_sub">Suitable for:</div>
                                    <div class="k10-recipe-modal__allergens_value">Vegan</div>
                                </div>
                                <div class="k10-recipe-modal__allergens-section_row k10-recipe-modal__allergens_contains">
                                    <div class="k10-recipe-modal__allergens-caption_sub">Contains:</div>
                                    <div class="k10-recipe-modal__allergens_value">Soya, Sulphur Dioxide/ Sulphites</div>
                                </div>
                                <div class="k10-recipe-modal__allergens-section_row k10-recipe-modal__allergens_may">
                                    <div class="k10-recipe-modal__allergens-caption_sub">May contain:</div>
                                    <div class="k10-recipe-modal__allergens_value">Mustard, Cereals with Gluten (Barley, Oats, Rye, Wheat)</div>
                                </div>
                            </div>
                        </div>
                        <div class="k10-recipe-modal__ingredient">
                            <div class="k10-recipe-modal__section k10-recipe-modal__ingredient-section">
                                <div class="k10-recipe-modal__section-values k10-w-recipe__ingredient">
                                    Tofu; Coconut Milk; Courgette
                                </div>
                            </div>
                        </div>
                        <div class="k10-recipe-modal__nutrients">
                            <div class="k10-recipe-modal__caption k10-recipe-modal__nutrients-caption">
                                Nutrition (per 100g)
                            </div>
                            <div class="k10-recipe-modal__section k10-recipe-modal__nutrients-section">
                                <table class="k10-recipe-modal__nutrients-table k10-table">
                                    <tbody>
                                        <tr><td>Energy (kCal)</td><td class="k10-recipe-modal__td_val">131</td></tr>
                                        <tr><td>Protein (g)</td><td class="k10-recipe-modal__td_val">4.8</td></tr>
                                        <tr><td>Carb (g)</td><td class="k10-recipe-modal__td_val">6.3</td></tr>
                                        <tr><td>of which Sugars (g)</td><td class="k10-recipe-modal__td_val">3.2</td></tr>
                                        <tr><td>Fat (g)</td><td class="k10-recipe-modal__td_val">9.3</td></tr>
                                        <tr><td>Sat Fat (g)</td><td class="k10-recipe-modal__td_val">4.2</td></tr>
                                        <tr><td>Salt (g)</td><td class="k10-recipe-modal__td_val">0.8</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="k10-recipe-modal__nutrients">
                            <div class="k10-recipe-modal__caption k10-recipe-modal__nutrients-caption">
                                Nutrition (per portion)
                            </div>
                            <div class="k10-recipe-modal__section k10-recipe-modal__nutrients-section">
                                <table class="k10-recipe-modal__nutrients-table k10-table">
                                    <tbody>
                                        <tr><td>Energy (kCal)</td><td class="k10-recipe-modal__td_val">304</td></tr>
                                        <tr><td>Protein (g)</td><td class="k10-recipe-modal__td_val">11.2</td></tr>
                                        <tr><td>Carb (g)</td><td class="k10-recipe-modal__td_val">14.7</td></tr>
                                        <tr><td>of which Sugars (g)</td><td class="k10-recipe-modal__td_val">7.4</td></tr>
                                        <tr><td>Fat (g)</td><td class="k10-recipe-modal__td_val">21.7</td></tr>
                                        <tr><td>Sat Fat (g)</td><td class="k10-recipe-modal__td_val">9.7</td></tr>
                                        <tr><td>Salt (g)</td><td class="k10-recipe-modal__td_val">1.9</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div></div>
        </div>
    </div>
    """
