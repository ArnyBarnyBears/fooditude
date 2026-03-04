"""
Lose It! automation via Playwright.

Library module for logging into loseit.com and creating custom foods
from scraped Fooditude menu data. Used by pipeline.py and loseit_debug.py.
"""

from __future__ import annotations

import asyncio
import csv
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, TimeoutError as PwTimeout

load_dotenv()

LOG_FILE = Path("run_log.txt")
DEBUG_DIR = Path("debug")
LOSEIT_URL = "https://www.loseit.com"
LOSEIT_LOGIN_URL = "https://my.loseit.com/login?r=https%3A%2F%2Fwww.loseit.com%2F"

DAY_MAP = {"tuesday": "Tue", "wednesday": "Wed", "thursday": "Thu"}

CATEGORY_PRESETS: dict[str, set[str] | None] = {
    "all": None,
    "mains": {"Mains"},
    "mains-extras": {"Mains", "Extras"},
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger("loseit")


def _debug_path(name: str) -> str:
    """Return a path inside the debug/ directory for screenshots."""
    DEBUG_DIR.mkdir(exist_ok=True)
    return str(DEBUG_DIR / name)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@dataclass
class FoodEntry:
    name: str
    date_label: str
    calories: str
    protein: str
    carbs: str
    sugars: str
    fat: str
    sat_fat: str
    salt: str

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.date_label})"

    @property
    def sodium_mg(self) -> float:
        """Convert salt_g to sodium_mg: sodium = salt * 1000 * 0.4."""
        try:
            return round(float(self.salt) * 1000 * 0.4, 1)
        except (ValueError, TypeError):
            return 0.0


def load_foods_from_csv(
    csv_path: Path,
    date_label: str,
    categories: str = "all",
) -> list[FoodEntry]:
    """
    Load food entries from a scraped CSV, using per-100g nutrition.

    categories: one of "all", "mains", "mains-extras". Controls which
    menu categories are included based on the CSV's 'category' column.
    """
    allowed = CATEGORY_PRESETS.get(categories)
    foods: list[FoodEntry] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if allowed is not None and row.get("category", "") not in allowed:
                continue
            foods.append(FoodEntry(
                name=row["name"],
                date_label=date_label,
                calories=row.get("energy_kcal_per100g", "0"),
                protein=row.get("protein_per100g", "0"),
                carbs=row.get("carb_per100g", "0"),
                sugars=row.get("sugars_per100g", "0"),
                fat=row.get("fat_per100g", "0"),
                sat_fat=row.get("sat_fat_per100g", "0"),
                salt=row.get("salt_per100g", "0"),
            ))
    return foods


# ---------------------------------------------------------------------------
# Browser helpers
# ---------------------------------------------------------------------------

async def create_browser(headless: bool = True) -> tuple:
    """Launch Playwright chromium and return (playwright, browser, context, page)."""
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless, slow_mo=300)
    context = await browser.new_context(viewport={"width": 1280, "height": 900})
    page = await context.new_page()
    return pw, browser, context, page


async def close_browser(pw, browser):
    await browser.close()
    await pw.stop()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def _dismiss_cookie_popup(page: Page) -> None:
    """Dismiss the cookie consent popup if it appears."""
    try:
        accept_btn = page.locator('button:has-text("I Accept"), button:has-text("Reject All")')
        if await accept_btn.count() > 0:
            log.info("Dismissing cookie consent popup...")
            await accept_btn.first.click()
            await asyncio.sleep(1)
    except Exception:
        pass


async def login(page: Page, email: str, password: str) -> None:
    """Navigate to Lose It login page and log in. Raises on failure."""
    log.info("Navigating to %s ...", LOSEIT_LOGIN_URL)
    await page.goto(LOSEIT_LOGIN_URL, wait_until="domcontentloaded", timeout=15000)
    await asyncio.sleep(2)

    await page.screenshot(path=_debug_path("01_login_page.png"))

    await _dismiss_cookie_popup(page)

    email_sel = 'input[type="email"], input[name="email"], input[placeholder*="mail"], input[aria-label*="mail"], input[id*="email"]'
    password_sel = 'input[type="password"], input[name="password"], input[placeholder*="assword"], input[aria-label*="assword"], input[id*="password"]'

    log.info("Waiting for email input field...")
    try:
        await page.wait_for_selector(email_sel, timeout=10000)
    except PwTimeout:
        await page.screenshot(path=_debug_path("02_no_email_field.png"))
        raise RuntimeError(
            "Could not find email input field. Check debug/02_no_email_field.png"
        )

    log.info("Filling email: %s", email)
    await page.locator(email_sel).first.fill(email)

    log.info("Filling password...")
    await page.locator(password_sel).first.fill(password)

    submit_sel = 'button[type="submit"], button:has-text("Log In"), button:has-text("Sign In"), button:has-text("Continue")'
    log.info("Clicking submit button...")
    await page.locator(submit_sel).first.click()

    log.info("Waiting for redirect to loseit.com ...")
    await asyncio.sleep(3)

    try:
        await page.wait_for_url("**/www.loseit.com/**", timeout=20000)
    except PwTimeout:
        pass

    await page.screenshot(path=_debug_path("03_post_login.png"))

    current_url = page.url
    log.info("Current URL after login: %s", current_url)

    if "login" in current_url.lower() or "signin" in current_url.lower():
        await page.screenshot(path=_debug_path("03_login_failed.png"))
        raise RuntimeError(
            f"Login appears to have failed. Still on: {current_url}. "
            "Check debug/03_login_failed.png and your .env credentials."
        )

    log.info("Login successful! On: %s", current_url)


# ---------------------------------------------------------------------------
# Add Food → Lunch → Create Food tab
# ---------------------------------------------------------------------------

async def open_create_food_form(page: Page) -> None:
    """From the dashboard, click Add Food -> pick Snacks to open the food modal."""
    log.info("Opening Add Food flow...")

    add_food_sel = '.addFoodButton, [role="button"]:has-text("Add Food"), div:has-text("Add Food")[role="button"]'
    try:
        await page.locator(add_food_sel).first.click(timeout=8000)
        await asyncio.sleep(1)
    except PwTimeout:
        await page.screenshot(path=_debug_path("04_no_add_food.png"))
        raise RuntimeError("Could not find 'Add Food' button on dashboard")

    try:
        await page.get_by_text("Snacks", exact=True).click(timeout=5000)
        await asyncio.sleep(2)
    except PwTimeout:
        log.info("No 'Snacks' option found, trying to proceed anyway...")

    await page.screenshot(path=_debug_path("05_meal_selected.png"))
    log.info("Meal selected. URL: %s", page.url)


async def _fill_gwt_input(locator, value: str, label: str) -> bool:
    """Fill a single GWT input locator and log the result."""
    try:
        await locator.fill(value, timeout=3000)
        log.info("  Filled '%s' = %s", label, value)
        return True
    except Exception as e:
        log.warning("  Could not fill '%s': %s", label, e)
        return False


async def create_single_food(page: Page, food: FoodEntry) -> str:
    """
    Create a single custom food entry via the GWT form.
    Assumes open_create_food_form() has already been called.
    Returns 'created', 'skipped', or 'failed'.
    """
    display = food.display_name
    log.info("Creating: %s ...", display)

    try:
        # Click the "Create Food" tab (last image in the rightmost td)
        try:
            create_tab = page.locator('td[align="right"] img.gwt-Image').last
            await create_tab.click(timeout=8000)
            await asyncio.sleep(2)
        except PwTimeout:
            log.error("Could not find 'Create Food' tab image")
            await page.screenshot(path=_debug_path("06_no_create_tab.png"))
            return "failed"

        # GWT form: inputs identified by class and DOM order.
        # gwt-SuggestBox: 0=Restaurant/Brand (skip), 1=Food Name
        # gwt-TextBox (9 total):
        #   0=Calories, 1=Fat, 2=Sat Fat, 3=Cholesterol (skip),
        #   4=Sodium, 5=Carbs, 6=Fiber (skip), 7=Sugars, 8=Protein
        form = page.locator('table:has(.addFoodToLog)')
        suggest = form.locator('input.gwt-SuggestBox')
        text = form.locator('input.gwt-TextBox')

        await _fill_gwt_input(suggest.nth(1), display, "Food Name")

        serving_input = form.locator('input.noGlowWebKitTextbox').first
        await _fill_gwt_input(serving_input, "100", "Serving amount")
        try:
            # 2 dropdown arrows (gwt-PushButton with 23x25 img): 0=Icon, 1=Unit
            unit_btn = form.locator('.gwt-PushButton:has(img[width="23"][height="25"])').nth(1)
            await unit_btn.click(timeout=3000)
            await asyncio.sleep(1)
            await page.get_by_text("Gram", exact=True).click(timeout=3000)
            await asyncio.sleep(1)
            log.info("  Set serving unit to Gram")
        except Exception as e:
            log.warning("  Could not set serving unit: %s", e)

        await _fill_gwt_input(text.nth(0), food.calories, "Calories")
        await _fill_gwt_input(text.nth(1), food.fat, "Fat")
        await _fill_gwt_input(text.nth(2), food.sat_fat, "Saturated Fat")
        await _fill_gwt_input(text.nth(4), str(food.sodium_mg), "Sodium")
        await _fill_gwt_input(text.nth(5), food.carbs, "Carbohydrates")
        await _fill_gwt_input(text.nth(7), food.sugars, "Sugars")
        await _fill_gwt_input(text.nth(8), food.protein, "Protein")

        await page.screenshot(path=_debug_path("07_form_filled.png"))

        try:
            await page.locator('.addFoodToLog').first.click(timeout=5000)
            await asyncio.sleep(2)
        except PwTimeout:
            log.error("Could not find addFoodToLog button")
            await page.screenshot(path=_debug_path("08_no_save_btn.png"))
            return "failed"

        await page.screenshot(path=_debug_path("09_food_saved.png"))
        log.info("CREATED: %s", display)
        return "created"

    except Exception as e:
        log.error("FAILED to create %s: %s", display, e)
        await page.screenshot(path=_debug_path(f"error_{food.name[:20].replace(' ', '_')}.png"))
        return "failed"


# ---------------------------------------------------------------------------
# Batch creation
# ---------------------------------------------------------------------------

async def create_all_foods(page: Page, foods: list[FoodEntry], delay: float = 2.0) -> dict:
    """Create all food entries, returning a summary dict."""
    summary = {"created": 0, "skipped": 0, "failed": 0}

    for i, food in enumerate(foods, 1):
        log.info("[%d/%d] Processing: %s", i, len(foods), food.display_name)

        await page.goto(LOSEIT_URL, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(2)
        await open_create_food_form(page)

        result = await create_single_food(page, food)
        summary[result] += 1
        await asyncio.sleep(delay)

    return summary


# ---------------------------------------------------------------------------
# High-level runner
# ---------------------------------------------------------------------------

KEYRING_SERVICE = "fooditude-loseit"


def _get_credentials() -> tuple[str, str]:
    """
    Load Lose It credentials. Tries macOS Keychain first (via keyring),
    falls back to .env. Use `python pipeline.py setup` to store credentials
    securely in the keychain.
    """
    import keyring

    email = keyring.get_password(KEYRING_SERVICE, "email")
    password = keyring.get_password(KEYRING_SERVICE, "password")

    if email and password:
        return email, password

    email = os.getenv("LOSEIT_EMAIL", "")
    password = os.getenv("LOSEIT_PASSWORD", "")
    if not email or not password or email == "your_email@example.com":
        raise RuntimeError(
            "No credentials found. Run 'python pipeline.py setup' to store them "
            "securely in your keychain, or set LOSEIT_EMAIL and LOSEIT_PASSWORD in .env"
        )
    return email, password


def store_credentials(email: str, password: str) -> None:
    """Save Lose It credentials to macOS Keychain."""
    import keyring
    keyring.set_password(KEYRING_SERVICE, "email", email)
    keyring.set_password(KEYRING_SERVICE, "password", password)
    log.info("Credentials stored in keychain under service '%s'", KEYRING_SERVICE)


async def run_create(
    csv_dir: Path = Path("output"),
    headless: bool = True,
    date_label: str | None = None,
    days: list[str] | None = None,
    categories: str = "all",
) -> None:
    """
    Load CSVs, login, and create foods in Lose It.

    days: list of day names like ["tuesday"] or None for all.
    categories: "all", "mains", or "mains-extras".
    """
    if date_label is None:
        date_label = datetime.now().strftime("%d/%m/%Y")

    log.info("=" * 60)
    log.info("Lose It! Food Creation — %s", date_label)
    log.info("  Days: %s | Categories: %s", days or "all", categories)
    log.info("=" * 60)

    all_foods: list[FoodEntry] = []

    for csv_file in sorted(csv_dir.glob("*_menu.csv")):
        day_key = csv_file.stem.replace("_menu", "")
        if days and day_key not in days:
            continue
        day_short = DAY_MAP.get(day_key, day_key.title())
        label = f"{day_short} {date_label}"
        foods = load_foods_from_csv(csv_file, label, categories=categories)
        log.info("Loaded %d foods from %s (categories=%s)", len(foods), csv_file.name, categories)
        all_foods.extend(foods)

    if not all_foods:
        log.error("No food entries found in %s", csv_dir)
        return

    log.info("Total foods to create: %d", len(all_foods))

    email, password = _get_credentials()
    pw, browser, context, page = await create_browser(headless=headless)

    try:
        await login(page, email, password)
        summary = await create_all_foods(page, all_foods)

        log.info("=" * 60)
        log.info("SUMMARY")
        log.info("  Created: %d", summary["created"])
        log.info("  Skipped: %d", summary["skipped"])
        log.info("  Failed:  %d", summary["failed"])
        log.info("=" * 60)
    finally:
        await close_browser(pw, browser)
