# Fooditude -> Lose It! Pipeline — Development Guide

## Architecture

```
pipeline.py            Main CLI entry point (scrape / create / run)
scrape_food.py         Fooditude menu scraper (requests + BeautifulSoup)
loseit_automation.py   Lose It! Playwright automation (library)
loseit_debug.py        Debug helpers (--login-only, --test-one-food)
tests/                 pytest test suite (86+ tests)
output/                Generated per-day CSV files
debug/                 Playwright screenshots from automation runs
```

### Data flow

```
Fooditude website ──(scrape_food.py)──> output/{day}_menu.csv
                                              │
                              ┌────────────────┘
                              ▼
                     load_foods_from_csv()
                       filter by --day
                       filter by --categories
                              │
                              ▼
                     loseit_automation.py
                       login()
                       open_create_food_form()
                       create_single_food()  ×N
                              │
                              ▼
                     Lose It! web app (GWT)
```

## CLI Quick Reference

```bash
# Activate venv first
source .venv/bin/activate

# Scrape only
python pipeline.py scrape

# Create foods for one day, mains + extras only
python pipeline.py create --day tuesday --categories mains-extras

# Create all foods for all days
python pipeline.py create

# Full pipeline (scrape then create), visible browser
python pipeline.py run --headed --day wednesday --categories mains

# Debug: test login
python loseit_debug.py --login-only --headed

# Debug: test creating one dummy food
python loseit_debug.py --test-one-food --headed

# Run tests
python -m pytest tests/ -v
```

## Scraper (scrape_food.py)

### Menu page structure

The Fooditude menu at `https://menus.tenkites.com/fooditude/tradedesk` serves
server-rendered HTML with all food data embedded (no JavaScript required).

Each day (Tuesday/Wednesday/Thursday) is a `<section class="k10-course_level_1">`.
Within each day, categories (Mains, Salads, Soup, All served with:) are
`<div class="k10-course_level_2">`. Some categories like Extras appear as
`<div class="k10-course_level_3">` nested inside Mains.

Each food item is a `<div class="k10-recipe-modal">` containing:
- Name: `.k10-recipe-modal__title_recipe-name`
- Allergens: `.k10-recipe-modal__allergens_suitable`, `_contains`, `_may`
- Ingredients: `.k10-w-recipe__ingredient`
- Nutrition per 100g and per portion: `<table>` rows inside `.k10-recipe-modal__nutrients`

### Key parsing detail

Level-3 sections (e.g. Extras nested inside Mains) require special handling.
The parser first collects all `data-recipe-id` values from level-3 children, then
excludes those when iterating level-2 recipes to avoid double-counting.

### Category values in CSV

The `category` column in generated CSVs contains these values:
- `Mains` — main dishes
- `Extras` — sides/condiments (nested under Mains in the HTML)
- `All served with:` — accompaniments (rice, pasta, veg)
- `Salads` — salad items
- `Soup` — soups and their garnishes

The `--categories` filter maps to:
- `mains` -> only `Mains`
- `mains-extras` -> `Mains` + `Extras`
- `all` -> no filter (everything)

## Lose It! Automation (loseit_automation.py)

### The web app is GWT

Lose It's web interface at `www.loseit.com` is built with **Google Web Toolkit (GWT)**.
This has major implications:

1. **Obfuscated class names** — CSS classes like `GPOEIKGK2C` are generated at
   compile time and can change between deploys. Never rely on them.

2. **No semantic HTML** — form inputs lack `name`, `id`, or `aria-label` attributes.
   Standard Playwright selectors (`input[name="calories"]`) do not work.

3. **Custom widgets** — dropdowns, buttons, and form controls are built from `<div>`
   and `<table>` elements, not native `<select>`/`<button>`.

### Login flow

1. Navigate to `https://my.loseit.com/login?r=https%3A%2F%2Fwww.loseit.com%2F`
   - The `?r=` parameter ensures redirect to the web app after login
2. Dismiss cookie consent popup (clicks "I Accept" or "Reject All")
3. Fill email/password and submit
4. After redirect, land on `www.loseit.com` dashboard

### Food creation flow

For each food item:

1. Navigate to `www.loseit.com` dashboard
2. Click **Add Food** button: `.addFoodButton` (a `<div>` with `role="button"`)
3. Select **Lunch** from dropdown: `page.get_by_text("Lunch", exact=True)` (exact
   match avoids hitting "Lunch: 0" in the page body)
4. Click **Create Food** tab: `td[align="right"] img.gwt-Image` (last image in
   the rightmost table cell — it's an icon with no text)
5. Fill the GWT form (see below)
6. Click submit: `.addFoodToLog` button

### GWT form field mapping

The form inputs must be targeted by **DOM order within the form**, not by labels.
The form is scoped via `table:has(.addFoodToLog)`.

**gwt-SuggestBox inputs** (2 total):
| Index | Field            | Action     |
|-------|------------------|------------|
| 0     | Restaurant/Brand | skip       |
| 1     | Food Name        | fill       |

**Serving size**: `input.noGlowWebKitTextbox` (first one in form) — fill with "100".
Then open the unit dropdown (second `gwt-PushButton` with a 23x25px image) and
select "Gram".

**gwt-TextBox inputs** (9 total, in DOM order):
| Index | Field          | Unit | Action     |
|-------|----------------|------|------------|
| 0     | Calories       | kcal | fill       |
| 1     | Fat            | g    | fill       |
| 2     | Saturated Fat  | g    | fill       |
| 3     | Cholesterol    | mg   | skip       |
| 4     | Sodium         | mg   | fill (converted from salt) |
| 5     | Carbohydrates  | g    | fill       |
| 6     | Fiber          | g    | skip       |
| 7     | Sugars         | g    | fill       |
| 8     | Protein        | g    | fill       |

### Selector cheat sheet

| Element                  | Selector                                                    |
|--------------------------|-------------------------------------------------------------|
| Add Food button          | `.addFoodButton`                                            |
| Lunch in dropdown        | `page.get_by_text("Lunch", exact=True)`                     |
| Create Food tab          | `td[align="right"] img.gwt-Image` (last)                   |
| Form scope               | `table:has(.addFoodToLog)`                                  |
| Food Name input          | `input.gwt-SuggestBox` nth(1)                               |
| Serving amount           | `input.noGlowWebKitTextbox` (first)                         |
| Serving unit dropdown    | `.gwt-PushButton:has(img[width="23"][height="25"])` nth(1)  |
| "Gram" option            | `page.get_by_text("Gram", exact=True)`                      |
| Nutrition inputs         | `input.gwt-TextBox` nth(0-8)                                |
| Submit button            | `.addFoodToLog`                                             |

### Sodium conversion

Lose It expects sodium in **milligrams**. The scraper provides salt in **grams**.
Conversion: `sodium_mg = salt_g * 1000 * 0.4` (salt is ~40% sodium by weight).

## Debugging

1. Run with `--headed` to watch the browser
2. All screenshots go to the `debug/` directory
3. Use `loseit_debug.py --test-one-food --headed` to test a single food creation
   without running the full pipeline
4. Check `run_log.txt` for timestamped logs of every action
5. If a GWT selector breaks after a Lose It deploy, inspect the page with DevTools
   and update the `nth()` indices or class selectors in `loseit_automation.py`

## Environment

Requires a `.env` file:
```
LOSEIT_EMAIL=your@email.com
LOSEIT_PASSWORD=your_password
```

Python 3.12+ with dependencies in `.venv/`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```
