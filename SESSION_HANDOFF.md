# Session Handoff

## Project Overview
<!-- Fill in for this project -->

## Repository Layout
```
/path/to/project/
└── paper-project/
    ├── CONVENTIONS.md         ← AI session rules, checkpoint system, tools
    ├── PAPER.md               ← Overall paper outline
    ├── SESSION_HANDOFF.md     ← This file (always current state)
    ├── scripts/
    │   ├── nanobanana.py      ← Schematic generation (Gemini API)
    │   ├── lit_search.py      ← Literature search (Edison API)
    │   ├── queries.yaml       ← Edison query registry
    │   └── figures.yaml       ← NanoBanana figure registry
    ├── figures/
    │   ├── _template/         ← Copy for each new figure
    │   └── figN_name/
    │       ├── STATUS.md
    │       ├── SPEC.md
    │       ├── DECISIONS.md
    │       ├── notes.md
    │       └── <name>_report.html
    ├── literature/            ← Edison query outputs
    ├── checkpoints/
    │   └── INDEX.md
    └── data/                  ← master_dataset.csv if applicable
```

## Python Environment
```
# Use python3.12 or higher
# Key packages: matplotlib, pandas, scipy, openpyxl, seaborn, statsmodels
```

## Current TODO List
<!-- Fill in -->

## Critical Technical Details
<!-- Fill in project-specific join keys, ID formats, data quirks -->
