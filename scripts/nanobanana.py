#!/usr/bin/env python3
"""
NanoBanana schematic/diagram description generator + Gemini image generator.

Reads figure descriptions from figures.yaml, produces prompts, and optionally
calls the Gemini image generation API to produce PNGs directly.

Usage:
    # List all available figures:
    python3.12 paper-project/scripts/nanobanana.py --list

    # Print prompt for a single figure:
    python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design

    # Save prompt to file:
    python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design --save

    # Generate image via Gemini API (saves PNG + prompt):
    python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design --generate

    # Generate with pro model:
    python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design --generate --pro

    # Generate all figures in a paper figure:
    python3.12 paper-project/scripts/nanobanana.py --figure fig2_cfos --generate

    # Generate all figures:
    python3.12 paper-project/scripts/nanobanana.py --all --generate

    # Force re-generate even if PNG already exists:
    python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design --generate --force

API key:
    Set GEMINI_API_KEY in environment or in .env at repo root.
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
PROJECT_DIR = SCRIPT_DIR.parent                        # paper-project/
FIGURES_YAML = SCRIPT_DIR / "figures.yaml"
FIGURES_DIR = PROJECT_DIR / "figures"
ENV_FILE = PROJECT_DIR / ".env"                        # repo root .env

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

MODEL_FLASH = "gemini-2.5-flash-image"    # fast, default
MODEL_PRO   = "gemini-3-pro-image-preview"  # higher quality, slower

# NanoBanana generation parameters appended to every prompt
GENERATION_PARAMS = """\
Generation parameters:
  aspect_ratio : 21:9
  resolution   : 2K
  temperature  : 1
  style        : NeurIPS publication figure, vector-clean, white background
"""

# ---------------------------------------------------------------------------
# Helpers — prompts
# ---------------------------------------------------------------------------

def load_figures(path: Path) -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    if isinstance(data, dict) and "figures" in data:
        return data["figures"]
    return data


def build_image_prompt(entry: dict) -> str:
    """Build the terse prompt sent to the image model (description only)."""
    return (
        f"Create a publication-quality academic diagram. "
        f"Style: NeurIPS paper figure, vector-clean, white background, "
        f"aspect ratio 21:9, 2K resolution. "
        f"Do NOT embed any figure caption text in the image.\n\n"
        f"{entry['description'].strip()}"
    )


def format_full_prompt(entry: dict) -> str:
    """Format the human-readable prompt file (description + checklist)."""
    lines = [
        f"# NanoBanana Prompt — {entry['id']}",
        f"# Figure: {entry['figure']} | Type: {entry['type']}",
        "",
        "## Caption (context only — do NOT embed in image)",
        entry["caption"].strip(),
        "",
        "## Diagram Description",
        entry["description"].strip(),
        "",
        GENERATION_PARAMS,
        "## Critique Checklist (post-generation)",
        "- [ ] All method components represented — no omissions, no hallucinations",
        "- [ ] Arrow directions match described data flow",
        "- [ ] All text labels correct, no typos, no gibberish",
        "- [ ] Math notation renders correctly",
        "- [ ] Caption text NOT embedded in image",
        "- [ ] No text overlapping arrows or other text",
        "- [ ] No spaghetti arrow routing",
        "- [ ] Font sizes legible and consistent",
        "- [ ] Good contrast (no light text on light background)",
        "- [ ] Compact rectangular layout — no wasted whitespace",
        "- [ ] No black background",
        "- [ ] No redundant color-coding legend text blocks",
    ]
    return "\n".join(lines)


def save_prompt(entry: dict, prompt: str) -> Path:
    """Save prompt to paper-project/figures/<figure>/schematics/<id>_prompt.txt."""
    out_dir = FIGURES_DIR / entry["figure"] / "schematics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{entry['id']}_prompt.txt"
    out_path.write_text(prompt)
    return out_path


def png_path(entry: dict) -> Path:
    return FIGURES_DIR / entry["figure"] / "schematics" / f"{entry['id']}.png"


def already_generated(entry: dict) -> bool:
    return png_path(entry).exists()


# ---------------------------------------------------------------------------
# Helpers — API key
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("ERROR: GEMINI_API_KEY not found.")
    print(f"  Set it as an env var or add GEMINI_API_KEY=... to {ENV_FILE}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers — generation
# ---------------------------------------------------------------------------

def generate_image(entry: dict, model: str, api_key: str) -> Path:
    """Call Gemini image generation API and save PNG. Returns output path."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    image_prompt = build_image_prompt(entry)
    out_path = png_path(entry)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Calling Gemini ({model})...")
    response = client.models.generate_content(
        model=model,
        contents=image_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )

    image_saved = False
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            # Save raw bytes directly
            image_bytes = part.inline_data.data
            out_path.write_bytes(image_bytes)
            image_saved = True
            break
        elif hasattr(part, "text") and part.text:
            print(f"  Model note: {part.text[:200]}")

    if not image_saved:
        raise RuntimeError("No image returned in API response.")

    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate NanoBanana prompts and images from figures.yaml"
    )
    parser.add_argument("--id",     help="Target a single figure by id")
    parser.add_argument("--figure", help="Target all figures in this paper figure directory")
    parser.add_argument("--all",    action="store_true", help="Target all figures")
    parser.add_argument("--list",   action="store_true", help="List all available figure ids")
    parser.add_argument("--save",   action="store_true",
                        help="Save prompt txt files to schematics/")
    parser.add_argument("--generate", action="store_true",
                        help="Call Gemini API to generate PNG images (also saves prompts)")
    parser.add_argument("--pro",    action="store_true",
                        help="Use Pro model instead of Flash (--generate only)")
    parser.add_argument("--force",  action="store_true",
                        help="Re-generate even if PNG already exists")
    args = parser.parse_args()

    figures = load_figures(FIGURES_YAML)

    # -- list -----------------------------------------------------------------
    if args.list:
        print(f"{'ID':<35} {'FIGURE':<25} {'TYPE':<12} PNG")
        print("-" * 80)
        for f in figures:
            exists = "✓" if png_path(f).exists() else "·"
            print(f"{f['id']:<35} {f['figure']:<25} {f['type']:<12} {exists}")
        return

    # -- select ---------------------------------------------------------------
    if args.id:
        selected = [f for f in figures if f["id"] == args.id]
        if not selected:
            print(f"ERROR: No figure with id '{args.id}'")
            sys.exit(1)
    elif args.figure:
        selected = [f for f in figures if f["figure"] == args.figure]
        if not selected:
            print(f"ERROR: No figures for paper figure '{args.figure}'")
            sys.exit(1)
    elif args.all:
        selected = figures
    else:
        parser.print_help()
        sys.exit(0)

    # -- prompt only (no generate) --------------------------------------------
    if not args.generate:
        for entry in selected:
            prompt = format_full_prompt(entry)
            if args.save:
                out_path = save_prompt(entry, prompt)
                print(f"[SAVED] {entry['id']} -> {out_path.relative_to(PROJECT_DIR.parent)}")
            else:
                print("=" * 70)
                print(prompt)
                print()
        if args.save:
            print(f"\nDone. {len(selected)} prompt(s) saved.")
        return

    # -- generate via API -----------------------------------------------------
    model = MODEL_PRO if args.pro else MODEL_FLASH
    api_key = get_api_key()

    print(f"Model: {model}")
    print(f"Figures: {len(selected)}\n")

    results = []
    for i, entry in enumerate(selected, 1):
        print(f"[{i}/{len(selected)}] {entry['id']}")

        if already_generated(entry) and not args.force:
            print(f"  Skipping — PNG exists (use --force to re-generate)")
            results.append((entry["id"], "SKIPPED", png_path(entry)))
            continue

        # Always save prompt alongside the image
        prompt = format_full_prompt(entry)
        save_prompt(entry, prompt)

        try:
            out_path = generate_image(entry, model, api_key)
            print(f"  Saved -> {out_path.relative_to(PROJECT_DIR.parent)}")
            results.append((entry["id"], "OK", out_path))
        except Exception as e:
            print(f"  FAILED: {e}")
            results.append((entry["id"], f"FAILED: {e}", None))

    # summary
    print("\n" + "=" * 60)
    ok      = sum(1 for _, s, _ in results if s == "OK")
    skipped = sum(1 for _, s, _ in results if s == "SKIPPED")
    failed  = sum(1 for _, s, _ in results if s.startswith("FAILED"))
    print(f"Done: {ok} generated, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
