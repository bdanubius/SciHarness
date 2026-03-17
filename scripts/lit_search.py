#!/usr/bin/env python3
"""
Edison Client literature search runner.
Submits all queries in parallel, then polls until all are done.

Usage:
    # Run ALL queries:
    python3.12 paper-project/scripts/lit_search.py

    # Run a single query by id:
    python3.12 paper-project/scripts/lit_search.py --id behav_si_hyperactivity

    # Run all queries in a category:
    python3.12 paper-project/scripts/lit_search.py --category fig1_behavior

    # Dry-run (print queries without sending):
    python3.12 paper-project/scripts/lit_search.py --dry-run

    # Re-run even if output already exists:
    python3.12 paper-project/scripts/lit_search.py --category fig1_behavior --force
"""

import argparse
import os
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent                      # paper-project/
QUERIES_FILE = SCRIPT_DIR / "queries.yaml"
OUTPUT_DIR = PROJECT_DIR / "literature"
ENV_FILE = PROJECT_DIR.parent / ".env"               # repo root .env

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_queries(path: Path) -> list[dict]:
    with open(path) as f:
        return yaml.safe_load(f)


def get_api_key() -> str:
    """Read EDISON_API_KEY from environment or .env file at repo root."""
    key = os.environ.get("EDISON_API_KEY")
    if key:
        return key

    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("EDISON_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    print("ERROR: EDISON_API_KEY not found.")
    print(f"  Set it as an env var, or add it to {ENV_FILE}")
    sys.exit(1)


def already_done(query_entry: dict) -> bool:
    """Return True if output file already exists (skip re-running)."""
    out_path = OUTPUT_DIR / query_entry["category"] / f"{query_entry['id']}.md"
    return out_path.exists()


def build_task_data(query_entry: dict) -> dict:
    """Build the task dict to send to Edison."""
    from edison_client import JobNames

    job_map = {
        "LITERATURE": JobNames.LITERATURE,
        "LITERATURE_HIGH": JobNames.LITERATURE_HIGH,
        "PRECEDENT": JobNames.PRECEDENT,
    }
    return {
        "name": job_map[query_entry["job"]],
        "query": query_entry["query"].strip(),
    }


def save_result(query_entry: dict, response) -> Path:
    """Save a response to literature/<category>/<id>.md and return the path."""
    category_dir = OUTPUT_DIR / query_entry["category"]
    category_dir.mkdir(parents=True, exist_ok=True)

    out_path = category_dir / f"{query_entry['id']}.md"

    answer = getattr(response, "formatted_answer", None) or getattr(response, "answer", str(response))

    content = f"""# {query_entry['id']}

**Category:** {query_entry['category']}
**Job:** {query_entry['job']}

## Query

{query_entry['query'].strip()}

## Answer

{answer}
"""
    out_path.write_text(content)
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run Edison literature searches (parallel)")
    parser.add_argument("--id", help="Run only this query id")
    parser.add_argument("--category", help="Run only queries in this category")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even if output file already exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print queries without sending to Edison")
    args = parser.parse_args()

    queries = load_queries(QUERIES_FILE)
    print(f"Loaded {len(queries)} queries from {QUERIES_FILE.name}")

    # Filter by id or category
    if args.id:
        queries = [q for q in queries if q["id"] == args.id]
    elif args.category:
        queries = [q for q in queries if q["category"] == args.category]

    if not queries:
        print("No queries matched the filter. Exiting.")
        sys.exit(1)

    # Skip already-done unless --force
    if not args.force and not args.dry_run:
        pending = [q for q in queries if not already_done(q)]
        skipped = len(queries) - len(pending)
        if skipped:
            print(f"Skipping {skipped} already-completed queries (use --force to re-run).")
        queries = pending

    if not queries:
        print("All queries already done.")
        return

    print(f"Will submit {len(queries)} queries in parallel.\n")

    # Dry run
    if args.dry_run:
        for q in queries:
            done = " [DONE]" if already_done(q) else ""
            print(f"[{q['id']}] ({q['job']}) — {q['category']}{done}")
            print(f"  {q['query'].strip()[:120]}...")
            print()
        return

    # Initialize client
    from edison_client import EdisonClient
    api_key = get_api_key()
    client = EdisonClient(api_key=api_key)
    print("Edison client initialized.")

    # Build all task dicts
    task_dicts = [build_task_data(q) for q in queries]

    # Submit all at once and poll in parallel
    print(f"Submitting all {len(task_dicts)} tasks simultaneously...")
    responses = client.run_tasks_until_done(task_dicts, progress_bar=True)
    print("All tasks complete.\n")

    # Save results
    results = []
    for q, response in zip(queries, responses):
        try:
            out_path = save_result(q, response)
            results.append((q["id"], "OK", out_path))
            print(f"  [OK] {q['id']} -> {out_path.relative_to(PROJECT_DIR.parent)}")
        except Exception as e:
            results.append((q["id"], f"FAILED: {e}", None))
            print(f"  [FAIL] {q['id']}: {e}")

    # Summary
    print("\n" + "=" * 60)
    ok = sum(1 for _, s, _ in results if s == "OK")
    print(f"DONE: {ok}/{len(results)} queries saved successfully.")


if __name__ == "__main__":
    main()
