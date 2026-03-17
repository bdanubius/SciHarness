# Conventions for AI Agent Sessions

These conventions apply to all paper/analysis projects. Project-specific
details (data paths, Python env, figure list) live in each project's own
`.cursor/rules/project.md`.

---

## Entering a Panel

When working on a figure:
1. Read PAPER.md for overall context and this figure's role
2. Read the panel's SPEC.md for requirements
3. Read STATUS.md for current phase and pinned direction
4. Read DECISIONS.md for past choices (respect them, don't redo)
5. Read existing code in code/ as starting point
6. Only THEN start working

## Exploration Phase (STATUS = EXPLORING)

- Create explore/task_NNN.md files, each containing:
  - The question/hypothesis being tested
  - The approach/code
  - The output (save images to explore/)
  - Assessment: promising / neutral / dead end
- Generate multiple diverse approaches — divergent thinking
- Do NOT update STATUS.md or DECISIONS.md (User does that through pinning, but you can recommend what to pin)

## Pinning (User triggers, agent executes)

When told "pin task N" or "go with approach X":
- Update STATUS.md: set phase to PINNED, record what was pinned
- Add decision entry to DECISIONS.md
- Copy/adapt relevant code to code/generate.py

## Iteration Phase (STATUS = ITERATING)

- Work in code/generate.py
- Save main output to output/
- Save diagnostic/alternative plots to output/diagnostic/
- Log non-trivial choices in DECISIONS.md

## Polishing (STATUS = POLISHED)

- Ensure code/generate.py runs cleanly end-to-end
- Output goes to output/final.png (and final.pdf)
- Verify all SPEC.md requirements are met
- Update STATUS.md to POLISHED

---

## Checkpoint System

A **checkpoint** captures the current state of the project at a presentation
moment. It lets you later ask "what's changed since checkpoint X?" and get a
summary HTML diff.

### When to use

Tell the agent: `"checkpoint — [name/date]"` (e.g. `"checkpoint — lab meeting 2026-02-24"`).
The agent will execute the full checkpoint procedure below.

### What a checkpoint does

1. **Creates a directory:** `paper-project/checkpoints/YYYY-MM-DD_<slug>/`
   - `slug` is a short kebab-case version of the name

2. **Copies current HTML reports** into the checkpoint directory.
   These are the snapshots — they never change after checkpointing.

3. **Writes `checkpoint.md`** inside the checkpoint directory with:
   - Date and name
   - One-paragraph summary of what's in each HTML report at this moment
   - Any meeting notes provided by User (see below)
   - TODO list for the coming week

4. **Updates `paper-project/checkpoints/INDEX.md`** — an append-only log:
   ```
   | 2026-02-24 | lab-meeting | Fig2 Panel C complete | checkpoints/2026-02-24_lab-meeting/ |
   ```

5. **Updates `SESSION_HANDOFF.md`** to reflect the checkpoint was taken.

### Meeting notes

You can paste meeting notes directly:
```
checkpoint — lab meeting 2026-02-24

Notes:
- COLLABORATOR wants to see the module heatmap as the main Panel C
- Need to add Fig3 before next presentation
- TODO: run precedent query for novelty check
```
The agent will incorporate these into `checkpoint.md` and extract actionable TODOs.

### "What's changed since checkpoint X?" — the diff report

When you say `"diff since [checkpoint name/date]"`, the agent will:
1. Read `checkpoints/INDEX.md` to find the checkpoint
2. Compare `SESSION_HANDOFF.md` (and STATUS.md files) to the checkpoint's `checkpoint.md`
3. Generate a `diff_report.html` in the checkpoint directory
4. Open the diff report in the browser

### Directory structure

```
paper-project/checkpoints/
├── INDEX.md                              ← append-only log
├── 2026-02-24_lab-meeting/
│   ├── checkpoint.md                     ← state summary + meeting notes + TODOs
│   ├── fig1_report.html                  ← frozen snapshot
│   └── diff_report.html                  ← generated later when requested
```

### Notes

- Checkpoint HTML files are large. Add `paper-project/checkpoints/**/*.html` to `.gitignore`.
- `checkpoint.md` and `INDEX.md` ARE committed — they are the lightweight record.
- If a report doesn't exist yet, skip it silently and note the omission.

---

## General Rules

- Use shared/style.mplstyle for all plots (once created)
- Never modify shared/data/ (read-only)
- Git commit messages: "fig2: [what changed]"
- When uncertain between options, present them to User — don't guess
- When asked for status overview, scan all STATUS.md files and summarize

---

## Analysis Reports — Self-Contained HTML

For each figure directory, produce a **self-contained HTML report** alongside
the markdown source.

### How to generate
1. Write the analysis report as `<figure_dir>/report.md` with **absolute
   image paths** so pandoc can find the PNGs:
   ```markdown
   ![Plot title](/absolute/path/to/plot.png)
   ```
2. Convert to self-contained HTML:
   ```bash
   pandoc report.md --standalone --embed-resources --toc \
     --metadata title="Figure N — Title" \
     -o report.html
   ```
   The `--embed-resources` flag base64-encodes all images — no external dependencies.
3. The resulting `.html` file opens in any browser and can be shared as-is.

### What goes in the report
- All generated figures (embedded as images)
- Figure design notes (what each panel shows, color coding, statistical methods)
- Narrative interpretation of findings
- Missing data / blocked analyses
- Open follow-up questions
- Scripts reference table
- Literature references

---

## NanoBanana: Schematic Diagram Generation

NanoBanana generates publication-quality schematic figures by writing detailed
spatial descriptions that get fed to an image generation model.
**Do not generate figures unless User explicitly says to.**

### Infrastructure
- Script: `paper-project/scripts/nanobanana.py`
- Figure registry: `paper-project/scripts/figures.yaml`
- Output: `paper-project/figures/<figure>/schematics/`

### Workflow
1. **Discuss** — agree on which schematic is needed and what it should show
2. **Draft description** — add/update entry in `figures.yaml`
3. **Generate prompt** — `python3.12 paper-project/scripts/nanobanana.py --id <id> --save`
4. **Feed to Visualizer** — paste the saved `_prompt.txt` into NanoBanana
5. **Critique** — check output against the critique checklist; refine (up to 3 rounds)
6. **Save image** — place final PNG in `schematics/`

### Commands
```bash
# List all registered schematics (✓ = PNG already generated):
python3.12 paper-project/scripts/nanobanana.py --list

# Print prompt for a single figure:
python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design

# Save prompt to file only (no API call):
python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design --save

# Generate image via Gemini API (saves PNG + prompt):
python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design --generate

# Generate with Pro model:
python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design --generate --pro

# Generate all figures for one paper figure:
python3.12 paper-project/scripts/nanobanana.py --figure fig2_cfos --generate

# Generate all figures:
python3.12 paper-project/scripts/nanobanana.py --all --generate

# Force re-generate even if PNG exists:
python3.12 paper-project/scripts/nanobanana.py --id fig1_study_design --generate --force
```

### How to write a diagram description (figures.yaml entry)
Each entry has:
- `id` — short identifier, used for output filename
- `figure` — paper figure directory (e.g. `fig1_behavior`, `fig2_cfos`)
- `type` — `schematic` | `flowchart` | `summary_plot`
- `caption` — intended caption (context only; never embedded in image)
- `description` — the full spatial/aesthetic prompt; must be exhaustively specific

**Description rules:**
- State the overall layout first: orientation, flow direction, background color
- Every element needs: shape, color (hex), position, label text, connections
- Every arrow needs: source, destination, style (solid/dashed/curved), label if any
- Use LaTeX notation for math: `$S$`, `$\mathcal{R}$`, `$\beta_1$`
- Never include figure caption text in the description

### NeurIPS aesthetic defaults (use unless there's a reason not to)
- Background: white `#FFFFFF`; group regions: 10–15% opacity pastels
- Module fills: medium-saturation (blue/orange, green/purple, teal/pink)
- Shapes: rounded rectangles (r=8px) for process; sharp rectangles for data; cylinders for databases
- Lines: solid black/gray for main flow; dashed gray for secondary
- Typography: sans-serif (Arial) for labels; serif italic for math
- Aspect ratio: **21:9** | Resolution: **2K** | Temperature: **1**

### Adding a new schematic
Append an entry to `figures.yaml`:
```yaml
- id: figN_my_schematic
  figure: figN_name
  type: schematic
  caption: >
    One-sentence caption for the figure panel.
  description: >
    The figure is a wide, horizontal flowchart illustrating [X].
    Layout flows left-to-right on a white (#FFFFFF) background. Aspect ratio 21:9.
    [... full spatial description ...]
```
Then run `python3.12 paper-project/scripts/nanobanana.py --id figN_my_schematic --save`.

---

## Edison Client: Literature Search

Edison finds citations and supporting literature for claims.
**Do not fire Edison jobs unless User explicitly says to.**

### Infrastructure
- Script: `paper-project/scripts/lit_search.py`
- Queries: `paper-project/scripts/queries.yaml`
- Output: `paper-project/literature/<category>/<id>.md`
- API key in `.env` as `EDISON_API_KEY=...` (never commit)

### Workflow
1. **Discuss** — agree on queries
2. **Add queries** to `queries.yaml`
3. **Fire jobs** — `python3.12 paper-project/scripts/lit_search.py --category <name>`
4. **Add todo** — "Check Edison results for [section]"
5. **Check results** — read output `.md` files, incorporate citations

### Job types
- `LITERATURE_HIGH` — deep reasoning, 5–15 min per query
- `LITERATURE` — faster, lighter
- `PRECEDENT` — novelty/originality checks (was HasAnyone)
- `ANALYSIS` — turn biological datasets into detailed analyses

### Commands
```bash
# Dry run (print queries without sending):
python3.12 paper-project/scripts/lit_search.py --dry-run

# Single query:
python3.12 paper-project/scripts/lit_search.py --id <id>

# Full category:
python3.12 paper-project/scripts/lit_search.py --category <category>

# Re-run completed query:
python3.12 paper-project/scripts/lit_search.py --id <id> --force
```

---

## SESSION_HANDOFF.md

Each project has one `SESSION_HANDOFF.md` in its `paper-project/` directory.
Each session **overwrites** this file (it is a latest-state snapshot, not a
log). There is always exactly one current handoff — no dated versions.

If you need a historical log, append to `paper-project/SESSION_LOG.md` with
a timestamped entry before overwriting the handoff.
