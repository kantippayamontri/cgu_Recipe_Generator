"""Extract structured data from saved HTML recipe files using extruct."""

import json
import os

import extruct
from tqdm import tqdm

save_instuction_folder = "/Users/kantip/Desktop/study/cgu_Recipe_Generator/data/backup_search/instructions/"
save_extract_data_folder = "/Users/kantip/Desktop/study/cgu_Recipe_Generator/data/backup_search/instructions_extracted/"


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


def extract_all() -> None:
    """Loop through all .html files and save extracted JSON."""
    os.makedirs(save_extract_data_folder, exist_ok=True)

    html_files = [
        f for f in os.listdir(save_instuction_folder) if f.endswith(".html")
    ]
    print(f"Found {len(html_files)} HTML files to process.")

    success = 0
    fail = 0
    skipped = 0

    for filename in tqdm(html_files, desc="Extracting", unit="file"):
        recipe_id = filename.replace(".html", "")
        html_path = os.path.join(save_instuction_folder, filename)
        save_path = os.path.join(save_extract_data_folder, f"{recipe_id}.json")

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


if __name__ == "__main__":
    extract_all()
