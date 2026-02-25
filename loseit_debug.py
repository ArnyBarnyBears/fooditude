"""
Debug / test helpers for the Lose It automation.

Usage:
    python loseit_debug.py --login-only --headed
    python loseit_debug.py --test-one-food --headed
"""

from __future__ import annotations

import argparse
import asyncio

from loseit_automation import (
    FoodEntry,
    create_browser,
    close_browser,
    create_single_food,
    login,
    log,
    open_create_food_form,
    _get_credentials,
)


async def _test_login(headless: bool = True):
    """Quick test: login, screenshot, then exit."""
    email, password = _get_credentials()
    pw, browser, context, page = await create_browser(headless=headless)
    try:
        await login(page, email, password)
        log.info("Login test passed! Closing browser in 5 seconds...")
        await asyncio.sleep(5)
    finally:
        await close_browser(pw, browser)


async def _test_one_food(headless: bool = True):
    """Login, then try creating a single dummy food entry."""
    email, password = _get_credentials()

    test_food = FoodEntry(
        name="TEST Tofu curry",
        date_label="25/02/2026",
        calories="131",
        protein="4.8",
        carbs="6.3",
        sugars="3.2",
        fat="9.3",
        sat_fat="4.2",
        salt="0.8",
    )

    pw, browser, context, page = await create_browser(headless=headless)
    try:
        await login(page, email, password)
        await open_create_food_form(page)
        result = await create_single_food(page, test_food)
        log.info("Test food result: %s", result)
        log.info("Pausing 10 seconds so you can inspect the browser...")
        await asyncio.sleep(10)
    finally:
        await close_browser(pw, browser)


def main():
    parser = argparse.ArgumentParser(description="Debug helpers for Lose It automation")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--login-only", action="store_true", help="Test login flow only")
    group.add_argument("--test-one-food", action="store_true", help="Test creating one dummy food")
    args = parser.parse_args()

    if args.login_only:
        asyncio.run(_test_login(headless=not args.headed))
    elif args.test_one_food:
        asyncio.run(_test_one_food(headless=not args.headed))


if __name__ == "__main__":
    main()
