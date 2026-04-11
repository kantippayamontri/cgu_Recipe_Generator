"""Fetch and extract recipe HTML.

Usage:
    # Fetch recipe HTML from URLs in the CSV
    python -m data_collection.preprocess_recipe fetch

    # Fetch with custom paths
    python -m data_collection.preprocess_recipe fetch \
        --csv data/backup_search/recipes_master.csv \
        --html-dir data/backup_search/instructions/

    # Extract structured data from saved .html files
    python -m data_collection.preprocess_recipe extract

    # Extract with custom paths
    python -m data_collection.preprocess_recipe extract \
        --html-dir data/backup_search/instructions/ \
        --extract-dir data/backup_search/instructions_extracted/
"""

import argparse
import asyncio
import json
import os

import aiohttp
import extruct
import pandas as pd
from tqdm import tqdm

# Default paths
DEFAULT_RECIPE_PATH = "data/backup_search/recipes_master.csv"
DEFAULT_HTML_FOLDER = "data/backup_search/instructions/"
DEFAULT_EXTRACT_FOLDER = "data/backup_search/instructions_extracted/"
CONCURRENCY = 10


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(description="Fetch and extract recipe HTML.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- fetch subcommand ---
    fetch_parser = subparsers.add_parser("fetch", help="Fetch recipe HTML from URLs")
    fetch_parser.add_argument(
        "--csv", default=DEFAULT_RECIPE_PATH, help="Path to recipes_master.csv"
    )
    fetch_parser.add_argument(
        "--html-dir", default=DEFAULT_HTML_FOLDER, help="Directory to save .html files"
    )

    # --- extract subcommand ---
    extract_parser = subparsers.add_parser(
        "extract", help="Extract structured data from .html files"
    )
    extract_parser.add_argument(
        "--html-dir", default=DEFAULT_HTML_FOLDER, help="Directory containing .html files"
    )
    extract_parser.add_argument(
        "--extract-dir",
        default=DEFAULT_EXTRACT_FOLDER,
        help="Directory to save extracted .json files",
    )

    return parser.parse_args()


async def fetch_recipe_html(
    session: aiohttp.ClientSession,
    url: str,
) -> tuple[int | None, str | None]:
    """Fetch a recipe URL and return the status code and HTML.

    Args:
        session: Shared aiohttp client session.
        url: URL pointing to a recipe web page.

    Returns:
        Tuple of (status_code, html_string). Status is None on
        connection/timeout errors.
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            return resp.status, await resp.text()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None, None


async def _fetch_and_save(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    recipe_id: int,
    url: str,
    save_path: str,
    pbar: tqdm,
    fail_count: list[int],
    not_found_count: list[int],
) -> None:
    """Fetch one recipe HTML and save to disk, respecting the semaphore.

    Args:
        session: Shared aiohttp client session.
        semaphore: Semaphore limiting concurrent requests.
        recipe_id: Recipe ID for logging.
        url: URL to fetch.
        save_path: File path to save the HTML.
        pbar: tqdm progress bar instance.
        fail_count: Mutable list tracking connection/timeout failures.
        not_found_count: Mutable list tracking 404 responses.
    """
    async with semaphore:
        status, html = await fetch_recipe_html(session, url)

        if status is not None and 200 <= status < 300:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(html)
        elif status is None:
            fail_count[0] += 1
        else:
            not_found_count[0] += 1

        pbar.set_postfix(failed=fail_count[0], not_found=not_found_count[0])
        pbar.update(1)


async def async_fetch_recipes(csv_path: str, html_folder: str) -> None:
    """Fetch recipe HTML from URLs in the CSV.

    Args:
        csv_path: Path to the recipes CSV file.
        html_folder: Directory to save downloaded .html files.
    """
    df = pd.read_csv(csv_path)

    os.makedirs(html_folder, exist_ok=True)

    semaphore = asyncio.Semaphore(CONCURRENCY)
    fail_count: list[int] = [0]
    not_found_count: list[int] = [0]

    skipped = 0
    tasks: list = []

    for _, row in df.iterrows():
        recipe_id = row["recipe_id"]
        url = row["instructions"]
        save_path = os.path.join(html_folder, f"{recipe_id}.html")

        if os.path.exists(save_path):
            skipped += 1
            continue

        tasks.append((recipe_id, url, save_path))

    total = len(tasks) + skipped
    print(f"\nTotal: {total} recipes | Skipped: {skipped} | To fetch: {len(tasks)}")

    if not tasks:
        print("All recipes already fetched.")
        return

    async with aiohttp.ClientSession() as session:
        pbar = tqdm(total=len(tasks), desc="Fetching recipes", unit="recipe")

        coros = [
            _fetch_and_save(
                session,
                semaphore,
                rid,
                url,
                path,
                pbar,
                fail_count,
                not_found_count,
            )
            for rid, url, path in tasks
        ]
        await asyncio.gather(*coros)
        pbar.close()

    saved = len(tasks) - fail_count[0] - not_found_count[0]
    print(
        f"\nDone. Saved: {saved} | Not Found (404/other): {not_found_count[0]} "
        f"| Failed (timeout/error): {fail_count[0]}"
    )


def extract_html(html_path: str) -> dict | None:
    """Extract structured data from a single HTML file.

    Args:
        html_path: Path to the HTML file.

    Returns:
        Dict with json-ld, microdata, opengraph keys, or None on error.
    """
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading {html_path}: {e}")
        return None

    try:
        return extruct.extract(html, syntaxes=["json-ld", "microdata", "opengraph"])
    except Exception as e:
        print(f"Error extracting {html_path}: {e}")
        return None


def extract_all(html_folder: str, extract_folder: str) -> None:
    """Loop through all .html files and save extracted JSON.

    Args:
        html_folder: Directory containing .html files.
        extract_folder: Directory to save extracted .json files.
    """
    os.makedirs(extract_folder, exist_ok=True)

    html_files = [f for f in os.listdir(html_folder) if f.endswith(".html")]
    print(f"Found {len(html_files)} HTML files to process.")

    success = 0
    fail = 0
    skipped = 0

    for filename in tqdm(html_files, desc="Extracting", unit="file"):
        recipe_id = filename.replace(".html", "")
        html_path = os.path.join(html_folder, filename)
        save_path = os.path.join(extract_folder, f"{recipe_id}.json")

        if os.path.exists(save_path):
            skipped += 1
            continue

        data = extract_html(html_path)
        if data:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            success += 1
        else:
            fail += 1

    print(
        f"\nDone. Extracted: {success} | Failed: {fail} | Skipped: {skipped}"
    )


def main() -> None:
    """CLI entry point."""
    args = parse_args()

    if args.command == "fetch":
        asyncio.run(async_fetch_recipes(args.csv, args.html_dir))
    elif args.command == "extract":
        extract_all(args.html_dir, args.extract_dir)


if __name__ == "__main__":
    main()