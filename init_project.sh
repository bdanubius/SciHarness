#!/usr/bin/env bash
# init_project.sh — set up a new paper-project in an existing repo
#
# Usage:
#   ./init_project.sh /path/to/your/project
#
# What it does:
#   1. Creates paper-project/ inside the target directory
#   2. Copies all template files into it
#   3. Copies .env.example → .env (if .env doesn't already exist)
#   4. Prints instructions for wiring CONVENTIONS.md into your AI tool
#
# Requirements: bash, cp, ln, mkdir
#
# AI tool wiring (done manually after this script — see README):
#   The script prints the path to CONVENTIONS.md. You then add it to
#   your tool's context once (e.g. symlink for Cursor, AGENTS.md for
#   Claude Code, system prompt file for others).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONVENTIONS_SRC="$SCRIPT_DIR/CONVENTIONS.md"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <project-root>"
  echo ""
  echo "  <project-root>   Path to the repo/folder where paper-project/ will be created."
  echo ""
  echo "Example:"
  echo "  $0 ~/projects/my-paper"
  exit 1
fi

PROJECT_ROOT="$(cd "$1" && pwd)"
PAPER_PROJECT="$PROJECT_ROOT/paper-project"

echo "Project root : $PROJECT_ROOT"
echo "paper-project: $PAPER_PROJECT"
echo ""

# ---------------------------------------------------------------------------
# Create paper-project/ structure
# ---------------------------------------------------------------------------

if [[ -d "$PAPER_PROJECT" ]]; then
  echo "WARNING: $PAPER_PROJECT already exists. Skipping copy (won't overwrite)."
else
  echo "Creating paper-project/..."
  mkdir -p "$PAPER_PROJECT/figures"
  mkdir -p "$PAPER_PROJECT/scripts"
  mkdir -p "$PAPER_PROJECT/literature"
  mkdir -p "$PAPER_PROJECT/checkpoints"

  # Core documents
  cp "$SCRIPT_DIR/PAPER.md"           "$PAPER_PROJECT/PAPER.md"
  cp "$SCRIPT_DIR/SESSION_HANDOFF.md" "$PAPER_PROJECT/SESSION_HANDOFF.md"

  # Figure template
  cp -r "$SCRIPT_DIR/figures/_template" "$PAPER_PROJECT/figures/_template"

  # Scripts
  cp "$SCRIPT_DIR/scripts/nanobanana.py"  "$PAPER_PROJECT/scripts/nanobanana.py"
  cp "$SCRIPT_DIR/scripts/lit_search.py"  "$PAPER_PROJECT/scripts/lit_search.py"
  cp "$SCRIPT_DIR/scripts/figures.yaml"   "$PAPER_PROJECT/scripts/figures.yaml"
  cp "$SCRIPT_DIR/scripts/queries.yaml"   "$PAPER_PROJECT/scripts/queries.yaml"

  # Checkpoints log
  cp "$SCRIPT_DIR/checkpoints/INDEX.md"   "$PAPER_PROJECT/checkpoints/INDEX.md"

  echo "  paper-project/ created."
fi

# ---------------------------------------------------------------------------
# .env
# ---------------------------------------------------------------------------

ENV_FILE="$PROJECT_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
  echo ".env already exists — skipping."
else
  cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
  echo ".env created from .env.example — fill in your API keys."
fi

# ---------------------------------------------------------------------------
# .gitignore reminder
# ---------------------------------------------------------------------------

GITIGNORE="$PROJECT_ROOT/.gitignore"
if [[ ! -f "$GITIGNORE" ]]; then
  echo ""
  echo "NOTE: No .gitignore found. Recommended entries (add manually):"
  echo "  .env"
  echo "  paper-project/checkpoints/**/*.html"
  echo "  __pycache__/"
  echo "  .DS_Store"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

echo ""
echo "Done. Next steps:"
echo "  1. Fill in paper-project/PAPER.md with your paper overview and figure list"
echo "  2. Add API keys to .env"
echo "  3. Copy figures/_template for each figure:"
echo "       cp -r paper-project/figures/_template paper-project/figures/fig1_name"
echo ""
echo "  4. Wire CONVENTIONS.md into your AI tool (one-time, per tool):"
echo "       CONVENTIONS.md is at: $CONVENTIONS_SRC"
echo ""
echo "       Cursor:      ln -s $CONVENTIONS_SRC $PROJECT_ROOT/.cursor/rules/conventions.md"
echo "       Claude Code: add 'include: $CONVENTIONS_SRC' to AGENTS.md"
echo "       Other:       paste contents into your tool's system prompt or rules file"
echo ""
echo "     See README.md → 'Wiring into your AI tool' for details."
