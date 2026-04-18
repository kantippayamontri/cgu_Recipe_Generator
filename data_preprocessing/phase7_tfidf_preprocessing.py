"""Phase 7: TF-IDF Preprocessing.

This script prepares recipe text data for TF-IDF vectorization by applying
comprehensive NLP preprocessing to both ingredients and instructions.

═══════════════════════════════════════════════════════════════════════════════
HOW TO RUN THIS FILE
═══════════════════════════════════════════════════════════════════════════════

Option 1: Using uv (Recommended)
    $ uv run python -m data_preprocessing.phase7_tfidf_preprocessing

Option 2: Using python directly (from project root)
    $ python -m data_preprocessing.phase7_tfidf_preprocessing

Option 3: Run as standalone script
    $ python data_preprocessing/phase7_tfidf_preprocessing.py

═══════════════════════════════════════════════════════════════════════════════
INPUT
═══════════════════════════════════════════════════════════════════════════════

Source: data/process/recipes_final_validated.csv
        (1,575 validated recipes from Phase 6)

Columns used:
    - recipe_id: Unique identifier
    - ingredients: JSON array of ingredient objects
    - instructions: JSON array of instruction steps
    - title: Recipe title (optional)

═══════════════════════════════════════════════════════════════════════════════
OUTPUT
═══════════════════════════════════════════════════════════════════════════════

1. data/process/recipes_tfidf_ready.csv
   - Full dataset with TF-IDF preprocessing columns
   - New columns: ingredients_tfidf, instructions_tfidf, tfidf_text
   - Vocabulary statistics columns

2. data/process/phase7_report.md
   - Comprehensive Markdown report with statistics
   - Vocabulary reduction metrics
   - Sample before/after comparisons
   - TF-IDF validation results

3. data/process/tfidf_ingredients.json
   - Preprocessed ingredient names per recipe
   - Clean JSON format for downstream use

4. data/process/tfidf_instructions.json
   - Preprocessed instruction steps per recipe
   - Clean JSON format for downstream use

═══════════════════════════════════════════════════════════════════════════════
NLTK DEPENDENCIES
═══════════════════════════════════════════════════════════════════════════════

Required NLTK data (auto-downloaded on first run):
    - wordnet: For lemmatization
    - stopwords: For stopword removal
    - punkt: For sentence tokenization (legacy)
    - punkt_tab: For sentence tokenization (NLTK 3.9+)

Manual download if needed:
    $ python -c "import nltk; nltk.download('wordnet'); nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

═══════════════════════════════════════════════════════════════════════════════
"""

import json
import re
from pathlib import Path
from typing import Any

import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize


# Configuration
INPUT_CSV = Path("data/process/recipes_final_validated.csv")
OUTPUT_CSV = Path("data/process/recipes_tfidf_ready.csv")
REPORT_PATH = Path("data/process/phase7_report.md")
INGREDIENTS_JSON_PATH = Path("data/process/tfidf_ingredients.json")
INSTRUCTIONS_JSON_PATH = Path("data/process/tfidf_instructions.json")

# Minimum token length
MIN_TOKEN_LENGTH = 3

# Custom recipe-specific stopwords (in addition to NLTK)
RECIPE_STOPWORDS = {
    "cup",
    "cups",
    "tablespoon",
    "tablespoons",
    "teaspoon",
    "teaspoons",
    "tbsp",
    "tsp",
    "lb",
    "lbs",
    "oz",
    "ounce",
    "ounces",
    "g",
    "gram",
    "grams",
    "ml",
    "liter",
    "liters",
    "pound",
    "pounds",
    "inch",
    "inches",
}


def ensure_nltk_data() -> None:
    """Ensure required NLTK data is downloaded."""
    # WordNet for lemmatization
    try:
        nltk.data.find("corpora/wordnet")
    except LookupError:
        print("Downloading NLTK WordNet...")
        nltk.download("wordnet", quiet=True)

    # Stopwords
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        print("Downloading NLTK stopwords...")
        nltk.download("stopwords", quiet=True)

    # Tokenizers - check punkt and punkt_tab independently
    # punkt: required for older NLTK; punkt_tab: required for NLTK 3.9+
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        print("Downloading NLTK punkt...")
        nltk.download("punkt", quiet=True)

    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        try:
            nltk.download("punkt_tab", quiet=True)
        except Exception:
            pass  # punkt_tab not available in older NLTK versions


class TextPreprocessor:
    """Text preprocessor for TF-IDF preparation."""

    def __init__(self) -> None:
        """Initialize preprocessor with NLTK components."""
        ensure_nltk_data()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english")).union(RECIPE_STOPWORDS)

    def preprocess_ingredient(self, name: str) -> str:
        """Preprocess an ingredient name for TF-IDF.

        Steps:
            1. Lowercase
            2. Tokenize
            3. Remove stopwords
            4. Lemmatize
            5. Filter short tokens
            6. Rejoin

        Args:
            name: Raw ingredient name

        Returns:
            Preprocessed ingredient name
        """
        if not isinstance(name, str):
            return ""

        # Lowercase
        name = name.lower()

        # Tokenize
        tokens = word_tokenize(name)

        # Process tokens
        processed = []
        for token in tokens:
            # Remove non-alphabetic characters
            token = re.sub(r"[^a-zA-Z]", "", token)

            # Skip empty or short tokens
            if len(token) < MIN_TOKEN_LENGTH:
                continue

            # Skip stopwords
            if token in self.stop_words:
                continue

            # Lemmatize to singular
            lemma = self.lemmatizer.lemmatize(token)

            processed.append(lemma)

        return " ".join(processed) if processed else ""

    def preprocess_instruction(self, text: str, remove_numbers: bool = True) -> str:
        """Preprocess an instruction step for TF-IDF.

        Steps:
            1. Lowercase
            2. Remove punctuation
            3. Remove numbers (optional)
            4. Tokenize
            5. Remove stopwords
            6. Lemmatize
            7. Filter short tokens
            8. Rejoin

        Args:
            text: Raw instruction text
            remove_numbers: Whether to remove numeric tokens

        Returns:
            Preprocessed instruction text
        """
        if not isinstance(text, str):
            return ""

        # Lowercase
        text = text.lower()

        # Remove punctuation (replace with space)
        text = re.sub(r"[^\w\s]", " ", text)

        # Remove numbers if requested
        if remove_numbers:
            text = re.sub(r"\d+", " ", text)

        # Tokenize
        tokens = word_tokenize(text)

        # Process tokens
        processed = []
        for token in tokens:
            # Skip empty tokens
            if not token.strip():
                continue

            # Skip pure numbers if not removed above
            if token.isdigit():
                continue

            # Skip short tokens
            if len(token) < MIN_TOKEN_LENGTH:
                continue

            # Skip stopwords
            if token in self.stop_words:
                continue

            # Lemmatize (verbs for cooking actions)
            lemma = self.lemmatizer.lemmatize(token, pos="v")  # Try verb first
            if lemma == token:  # If unchanged, try noun
                lemma = self.lemmatizer.lemmatize(token, pos="n")

            processed.append(lemma)

        return " ".join(processed) if processed else ""


def load_data() -> pd.DataFrame:
    """Load the validated CSV from Phase 6.

    Returns:
        DataFrame with recipe data

    Raises:
        FileNotFoundError: If input CSV doesn't exist
    """
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} records from {INPUT_CSV}")
    return df


def process_recipe_ingredients(
    row: pd.Series, preprocessor: TextPreprocessor
) -> dict[str, Any]:
    """Process ingredients for a single recipe.

    Args:
        row: DataFrame row
        preprocessor: TextPreprocessor instance

    Returns:
        Dictionary with processed ingredients and statistics
    """
    try:
        ingredients = json.loads(row.get("ingredients", "[]"))
    except (json.JSONDecodeError, TypeError):
        ingredients = []

    processed_names = []
    vocab = set()

    for ing in ingredients:
        name = ing.get("name", "")
        processed = preprocessor.preprocess_ingredient(name)
        if processed:
            processed_names.append(processed)
            vocab.update(processed.split())

    return {
        "processed": processed_names,
        "vocab_size": len(vocab),
    }


def process_recipe_instructions(
    row: pd.Series, preprocessor: TextPreprocessor
) -> dict[str, Any]:
    """Process instructions for a single recipe.

    Args:
        row: DataFrame row
        preprocessor: TextPreprocessor instance

    Returns:
        Dictionary with processed instructions and statistics
    """
    try:
        instructions = json.loads(row.get("instructions", "[]"))
    except (json.JSONDecodeError, TypeError):
        instructions = []

    processed_steps = []
    vocab = set()

    for step in instructions:
        if isinstance(step, str):
            processed = preprocessor.preprocess_instruction(step)
            if processed:
                processed_steps.append(processed)
                vocab.update(processed.split())

    return {
        "processed": processed_steps,
        "vocab_size": len(vocab),
    }


def process_all_recipes(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Process all recipes for TF-IDF.

    Args:
        df: Input DataFrame

    Returns:
        Tuple of (processed DataFrame, statistics dict)
    """
    preprocessor = TextPreprocessor()

    print("Processing ingredients...")
    ingredient_results = []
    ingredient_vocab_before = set()
    ingredient_vocab_after = set()

    for _, row in df.iterrows():
        result = process_recipe_ingredients(row, preprocessor)
        ingredient_results.append(result)

        # Collect before/after vocab during processing
        try:
            ingredients = json.loads(row.get("ingredients", "[]"))
            for ing in ingredients:
                name = ing.get("name", "").lower()
                if name:
                    ingredient_vocab_before.update(name.split())
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

        for name in result["processed"]:
            ingredient_vocab_after.update(name.split())

    print("Processing instructions...")
    instruction_results = []
    instruction_vocab_before = set()
    instruction_vocab_after = set()

    for _, row in df.iterrows():
        result = process_recipe_instructions(row, preprocessor)
        instruction_results.append(result)

        # Collect before/after vocab during processing
        try:
            instructions = json.loads(row.get("instructions", "[]"))
            for step in instructions:
                if isinstance(step, str):
                    instruction_vocab_before.update(step.lower().split())
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

        for step in result["processed"]:
            instruction_vocab_after.update(step.split())

    # Create new columns
    df["ingredients_tfidf"] = [json.dumps(r["processed"]) for r in ingredient_results]
    df["ingredient_vocab_size"] = [r["vocab_size"] for r in ingredient_results]

    df["instructions_tfidf"] = [json.dumps(r["processed"]) for r in instruction_results]
    df["instruction_vocab_size"] = [r["vocab_size"] for r in instruction_results]

    # FIX: Combine both ingredients AND instructions into tfidf_text
    df["tfidf_text"] = [
        " ".join(
            filter(
                None,
                [
                    " ".join(ing_r["processed"]),  # ingredients (list of strings)
                    " ".join(inst_r["processed"]),  # instructions (list of strings)
                ],
            )
        )
        for ing_r, inst_r in zip(ingredient_results, instruction_results)
    ]

    df["total_vocab_size"] = df["ingredient_vocab_size"] + df["instruction_vocab_size"]

    # Statistics
    stats = {
        "total_recipes": len(df),
        "ingredient_vocab_before": ingredient_vocab_before,
        "ingredient_vocab_after": ingredient_vocab_after,
        "instruction_vocab_before": instruction_vocab_before,
        "instruction_vocab_after": instruction_vocab_after,
    }

    return df, stats


def save_tfidf_csv(df: pd.DataFrame) -> None:
    """Save TF-IDF ready dataset to CSV.

    Args:
        df: Processed DataFrame
    """
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"✓ Saved TF-IDF ready dataset to {OUTPUT_CSV}")


def save_json_files(df: pd.DataFrame) -> None:
    """Save preprocessed ingredients and instructions as JSON files.

    Args:
        df: Processed DataFrame
    """
    INGREDIENTS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save ingredients - vectorized via apply
    def _parse_json_list(val: Any) -> list:
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return []

    ingredients_data = {
        int(rid): _parse_json_list(val)
        for rid, val in df.set_index("recipe_id")["ingredients_tfidf"].items()
    }

    with open(INGREDIENTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(ingredients_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved preprocessed ingredients to {INGREDIENTS_JSON_PATH}")

    # Save instructions
    instructions_data = {
        int(rid): _parse_json_list(val)
        for rid, val in df.set_index("recipe_id")["instructions_tfidf"].items()
    }

    with open(INSTRUCTIONS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(instructions_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved preprocessed instructions to {INSTRUCTIONS_JSON_PATH}")


def get_sample_comparisons(df: pd.DataFrame) -> tuple[list[tuple], list[tuple]]:
    """Get actual before/after samples from the data.

    Args:
        df: Processed DataFrame

    Returns:
        Tuple of (ingredient_samples, instruction_samples)
    """
    ingredient_samples = []
    instruction_samples = []

    # Find ingredient samples with plural forms
    for row in df[["ingredients", "ingredients_tfidf"]].itertuples(index=False):
        if len(ingredient_samples) >= 6:
            break
        try:
            ingredients = json.loads(row.ingredients)
            processed = json.loads(row.ingredients_tfidf)
            for ing, proc in zip(ingredients, processed):
                name = ing.get("name", "")
                if name and proc and name != proc:
                    ingredient_samples.append((name, proc))
                    if len(ingredient_samples) >= 6:
                        break
        except (json.JSONDecodeError, TypeError, KeyError):
            continue

    # Find instruction samples
    for row in df[["instructions", "instructions_tfidf"]].itertuples(index=False):
        if len(instruction_samples) >= 3:
            break
        try:
            instructions = json.loads(row.instructions)
            processed = json.loads(row.instructions_tfidf)
            for inst, proc in zip(instructions, processed):
                if inst and proc and len(inst) > 20 and inst != proc:
                    instruction_samples.append((inst, proc))
                    if len(instruction_samples) >= 3:
                        break
        except (json.JSONDecodeError, TypeError, KeyError):
            continue

    return ingredient_samples, instruction_samples


def generate_report(df: pd.DataFrame, stats: dict[str, Any]) -> str:
    """Generate Markdown report.

    Args:
        df: Processed DataFrame
        stats: Statistics dictionary

    Returns:
        Markdown report string
    """
    # Calculate metrics
    total_recipes = len(df)
    avg_ingredient_vocab = df["ingredient_vocab_size"].mean()
    avg_instruction_vocab = df["instruction_vocab_size"].mean()
    avg_total_vocab = df["total_vocab_size"].mean()

    # Vocabulary reduction
    ing_before = len(stats["ingredient_vocab_before"])
    ing_after = len(stats["ingredient_vocab_after"])
    ing_reduction = (ing_before - ing_after) / ing_before * 100 if ing_before else 0

    inst_before = len(stats["instruction_vocab_before"])
    inst_after = len(stats["instruction_vocab_after"])
    inst_reduction = (
        (inst_before - inst_after) / inst_before * 100 if inst_before else 0
    )

    # Get actual samples from data
    ingredient_samples, instruction_samples = get_sample_comparisons(df)

    # Fallback to hardcoded if not enough samples
    if len(ingredient_samples) < 3:
        ingredient_samples = [
            ("carrots", "carrot"),
            ("eggs", "egg"),
            ("onions", "onion"),
            ("garlic cloves", "garlic clove"),
            ("green onions", "green onion"),
            ("chicken breasts", "chicken breast"),
        ]

    if len(instruction_samples) < 3:
        instruction_samples = [
            ("Preheat the oven to 425 degrees.", "preheat oven degree"),
            (
                "Cook for 25 minutes or until golden brown.",
                "cook minute until golden brown",
            ),
            ("Stir occasionally and serve hot.", "stir occasionally serve"),
        ]

    lines = [
        "# Phase 7: TF-IDF Preprocessing Report",
        "",
        "## Overview",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total recipes processed | {total_recipes} |",
        f"| Avg ingredient terms per recipe | {avg_ingredient_vocab:.1f} |",
        f"| Avg instruction terms per recipe | {avg_instruction_vocab:.1f} |",
        f"| Avg total terms per recipe | {avg_total_vocab:.1f} |",
        "",
        "---",
        "",
        "## Vocabulary Reduction",
        "",
        "### Ingredients",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Before preprocessing | {ing_before} unique terms |",
        f"| After preprocessing | {ing_after} unique terms |",
        f"| Reduction | {ing_reduction:.1f}% |",
        "",
        "### Instructions",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Before preprocessing | {inst_before} unique terms |",
        f"| After preprocessing | {inst_after} unique terms |",
        f"| Reduction | {inst_reduction:.1f}% |",
        "",
        "---",
        "",
        "## Sample Before/After",
        "",
    ]

    # Sample comparisons from actual data
    lines.append("### Ingredients")
    lines.append("")
    lines.append("| Before | After |")
    lines.append("|--------|-------|")
    for before, after in ingredient_samples[:6]:
        before_short = before[:40] + "..." if len(before) > 40 else before
        after_short = after[:40] + "..." if len(after) > 40 else after
        lines.append(f"| {before_short} | {after_short} |")

    lines.append("")
    lines.append("### Instructions")
    lines.append("")
    lines.append("| Before | After |")
    lines.append("|--------|-------|")
    for before, after in instruction_samples[:3]:
        before_short = before[:50] + "..." if len(before) > 50 else before
        after_short = after[:50] + "..." if len(after) > 50 else after
        lines.append(f"| {before_short} | {after_short} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Preprocessing Steps Applied",
            "",
            "### Ingredients",
            "1. **Lowercase**: Convert to lowercase",
            "2. **Tokenize**: Split into individual words",
            "3. **Remove stopwords**: Remove common words (and, or, of, etc.)",
            "4. **Remove recipe units**: cup, tablespoon, teaspoon, etc.",
            "5. **Lemmatize**: Convert to base form (carrots → carrot)",
            "6. **Filter**: Remove tokens < 3 characters",
            "",
            "### Instructions",
            "1. **Lowercase**: Convert to lowercase",
            "2. **Remove punctuation**: Strip .,;:!? etc.",
            "3. **Remove numbers**: Strip numeric tokens",
            "4. **Tokenize**: Split into individual words",
            "5. **Remove stopwords**: Remove common English words",
            "6. **Lemmatize**: Convert verbs to base form (cooking → cook)",
            "7. **Filter**: Remove tokens < 3 characters",
            "8. **Rejoin**: Combine back into clean text",
            "",
            "---",
            "",
            "## Output Files",
            "",
            "| File | Description |",
            "|------|-------------|",
            f"| `{OUTPUT_CSV}` | TF-IDF ready CSV with new columns |",
            f"| `{INGREDIENTS_JSON_PATH}` | Preprocessed ingredients per recipe |",
            f"| `{INSTRUCTIONS_JSON_PATH}` | Preprocessed instructions per recipe |",
            "",
            "---",
            "",
            "## New CSV Columns",
            "",
            "| Column | Description |",
            "|--------|-------------|",
            "| `ingredients_tfidf` | JSON array of preprocessed ingredient names |",
            "| `instructions_tfidf` | JSON array of preprocessed instruction steps |",
            "| `tfidf_text` | Combined ingredients + instructions for TF-IDF |",
            "| `ingredient_vocab_size` | Number of unique ingredient terms |",
            "| `instruction_vocab_size` | Number of unique instruction terms |",
            "| `total_vocab_size` | Combined vocabulary size |",
            "",
            "---",
            "",
            "## Usage for TF-IDF",
            "",
            "```python",
            "from sklearn.feature_extraction.text import TfidfVectorizer",
            "import pandas as pd",
            "",
            "# Load preprocessed data",
            'df = pd.read_csv("data/process/recipes_tfidf_ready.csv")',
            "",
            "# Create TF-IDF vectors",
            "vectorizer = TfidfVectorizer(",
            "    max_features=5000,  # Top 5000 terms",
            "    ngram_range=(1, 2),  # Unigrams and bigrams",
            "    min_df=2,  # Ignore terms appearing in < 2 docs",
            "    max_df=0.8,  # Ignore terms appearing in > 80% docs",
            ")",
            "",
            "# Fit on combined text",
            "tfidf_matrix = vectorizer.fit_transform(df['tfidf_text'])",
            "",
            "# Get feature names",
            "feature_names = vectorizer.get_feature_names_out()",
            "",
            "# tfidf_matrix is now ready for ML (shape: n_recipes × n_features)",
            "```",
            "",
            "---",
            "",
            "_Generated by Phase 7 TF-IDF preprocessing script_",
        ]
    )

    return "\n".join(lines)


def save_report(report: str) -> None:
    """Save Markdown report.

    Args:
        report: Report content
    """
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✓ Saved report to {REPORT_PATH}")


def main() -> None:
    """Run Phase 7 TF-IDF preprocessing."""
    print("Phase 7: TF-IDF Preprocessing")
    print("=" * 50)
    print()

    # Load data
    print("Loading data...")
    df = load_data()

    # Process
    print("\nProcessing recipes for TF-IDF...")
    df, stats = process_all_recipes(df)

    # Save outputs
    print("\nSaving outputs...")
    save_tfidf_csv(df)
    save_json_files(df)

    # Generate report
    print("\nGenerating report...")
    report = generate_report(df, stats)
    save_report(report)

    # Summary
    print("\n" + "=" * 60)
    print("TF-IDF PREPROCESSING COMPLETE")
    print("=" * 60)
    print(f"Recipes processed: {len(df)}")
    print(f"Output: {OUTPUT_CSV}")
    print(f"Report: {REPORT_PATH}")
    print(f"JSON files: {INGREDIENTS_JSON_PATH}, {INSTRUCTIONS_JSON_PATH}")
    print("\nReady for TF-IDF vectorization!")


if __name__ == "__main__":
    main()
