"""
Fooditude -> Lose It! weekly pipeline.

Subcommands:
    python pipeline.py scrape                                # scrape menu to CSVs
    python pipeline.py create --day tuesday                  # create foods for one day
    python pipeline.py create --day wednesday,thursday       # multiple days
    python pipeline.py create --day tuesday --categories mains-extras
    python pipeline.py create --categories mains             # mains only, all days
    python pipeline.py run                                   # scrape + create all
    python pipeline.py run --headed --day wednesday --categories mains
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from scrape_food import scrape_and_export
from loseit_automation import run_create, store_credentials, log

VALID_DAYS = ["tuesday", "wednesday", "thursday"]
VALID_CATEGORIES = ["all", "mains", "mains-extras"]


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add flags shared by 'create' and 'run' subcommands."""
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    parser.add_argument("--csv-dir", type=Path, default=Path("output"),
                        help="Directory with menu CSVs (default: output/)")
    parser.add_argument("--date", type=str, default=None,
                        help="Date label for food names, e.g. 25/02/2026")
    parser.add_argument("--day", type=str, default="all",
                        help="Comma-separated days: tuesday,wednesday,thursday or all (default: all)")
    parser.add_argument("--categories", type=str, default="all",
                        choices=VALID_CATEGORIES,
                        help="Category filter: all, mains, mains-extras (default: all)")


def _resolve_days(day_arg: str) -> list[str] | None:
    """Convert the --day CLI arg to a list of day keys, or None for all."""
    if day_arg == "all":
        return None
    days = [d.strip().lower() for d in day_arg.split(",")]
    invalid = [d for d in days if d not in VALID_DAYS]
    if invalid:
        raise SystemExit(
            f"error: invalid day(s): {', '.join(invalid)} "
            f"(choose from {', '.join(VALID_DAYS)}, all)"
        )
    return days


def cmd_scrape(args: argparse.Namespace) -> None:
    log.info("=" * 60)
    log.info("Scraping Fooditude menu")
    log.info("=" * 60)
    try:
        paths = scrape_and_export(output_dir=args.csv_dir)
        log.info("Scraped %d CSV files", len(paths))
    except Exception as e:
        log.error("Scraping failed: %s", e)
        sys.exit(1)


def cmd_create(args: argparse.Namespace) -> None:
    date_label = args.date  # None → auto-compute actual date per day
    days = _resolve_days(args.day)

    log.info("=" * 60)
    log.info("Creating foods in Lose It!")
    log.info("=" * 60)
    asyncio.run(run_create(
        csv_dir=args.csv_dir,
        headless=not args.headed,
        date_label=date_label,
        days=days,
        categories=args.categories,
    ))


def cmd_run(args: argparse.Namespace) -> None:
    cmd_scrape(args)
    cmd_create(args)
    log.info("Pipeline complete.")


def cmd_setup() -> None:
    import getpass
    print("Store Lose It! credentials in macOS Keychain")
    print("(This avoids putting your password in the .env file)\n")
    email = input("Lose It email: ").strip()
    password = getpass.getpass("Lose It password: ")
    store_credentials(email, password)
    print("\nCredentials saved. You can now remove LOSEIT_PASSWORD from .env.")


def main():
    parser = argparse.ArgumentParser(
        description="Fooditude -> Lose It! weekly pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subs = parser.add_subparsers(dest="command", required=True)

    # --- scrape ---
    p_scrape = subs.add_parser("scrape", help="Scrape Fooditude menu to CSVs")
    p_scrape.add_argument("--csv-dir", type=Path, default=Path("output"),
                          help="Output directory (default: output/)")

    # --- create ---
    p_create = subs.add_parser("create", help="Create foods in Lose It from existing CSVs")
    _add_common_args(p_create)

    # --- run ---
    p_run = subs.add_parser("run", help="Scrape + create (full pipeline)")
    _add_common_args(p_run)

    # --- setup ---
    subs.add_parser("setup", help="Store Lose It credentials in macOS Keychain")

    args = parser.parse_args()

    if args.command == "scrape":
        cmd_scrape(args)
    elif args.command == "create":
        cmd_create(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "setup":
        cmd_setup()


if __name__ == "__main__":
    main()
