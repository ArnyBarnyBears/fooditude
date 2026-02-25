# Fooditude -> Lose It! Pipeline

Scrapes the weekly lunch menu from [Fooditude](https://menus.tenkites.com/fooditude/tradedesk) and automatically creates custom foods in your [Lose It!](https://www.loseit.com) account with full nutritional data.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

Create a `.env` file with your Lose It credentials:

```
LOSEIT_EMAIL=your@email.com
LOSEIT_PASSWORD=your_password
```

## Usage

### Scrape the menu

```bash
python pipeline.py scrape
```

Saves per-day CSVs to `output/` (tuesday_menu.csv, wednesday_menu.csv, thursday_menu.csv).

### Create foods in Lose It

```bash
# All days, all categories
python pipeline.py create

# Single day
python pipeline.py create --day tuesday

# Just mains + extras for Thursday (most common use case)
python pipeline.py create --day thursday --categories mains-extras

# Just mains
python pipeline.py create --day wednesday --categories mains

# Watch the browser while it works
python pipeline.py create --day tuesday --categories mains-extras --headed
```

### Full pipeline (scrape + create)

```bash
# Scrape fresh menu then create all foods
python pipeline.py run

# Scrape + create Thursday mains with visible browser
python pipeline.py run --headed --day thursday --categories mains-extras
```

### Options

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--day` | tuesday, wednesday, thursday, all | all | Which day to process |
| `--categories` | all, mains, mains-extras | all | Filter by menu category |
| `--headed` | - | headless | Show the browser window |
| `--date` | e.g. 25/02/2026 | today | Override the date label on food names |

### Debug / test

```bash
# Test login only
python loseit_debug.py --login-only --headed

# Test creating one dummy food
python loseit_debug.py --test-one-food --headed
```

### Run tests

```bash
python -m pytest tests/ -v
```

## How it works

1. **Scraper** (`scrape_food.py`) fetches the Fooditude menu HTML and parses food items with BeautifulSoup, extracting name, category, allergens, ingredients, and nutrition per 100g / per portion.

2. **Lose It automation** (`loseit_automation.py`) uses Playwright to log into the Lose It GWT web app, navigate to Add Food -> Lunch -> Create Food, fill the nutrition form, and submit.

3. **Pipeline** (`pipeline.py`) orchestrates both steps with CLI filtering by day and category.

See [DEVELOPMENT.md](DEVELOPMENT.md) for architecture details, GWT selector reference, and debugging guide.
