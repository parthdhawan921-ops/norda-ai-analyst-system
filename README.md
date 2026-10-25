# NORDA AI Analyst System

**Live dashboard:** https://parthdhawan921-ops.github.io/norda-ai-analyst-system/reports/html/dashboard.html  
**Data model diagram:** https://parthdhawan921-ops.github.io/norda-ai-analyst-system/reports/html/data-model.html

An AI-assisted analytics pipeline for a European electronics retailer (NORDA, practice
company from Baraa's *Claude for data analysts* course on LinkedIn Learning), built
with Claude Code. It turns a messy monthly shop export into checked numbers, an
interactive dashboard, a meeting deck and a Power BI model with **one command**.

**Headline:** 41/41 quality checks pass in under 30 seconds, and the pipeline found €274K to €442K of December sales lost to 3 stock-outs.

**Interactive case file:** [parthdhawan921-ops.github.io/Parth_Personal/#norda](https://parthdhawan921-ops.github.io/Parth_Personal/#norda)

```
data/raw ──/profile──> data/clean ──/mart──> data/mart ──/quality-gate──> reports
 (export)   check 25     (fixed)     star     (4 dims,     41 checks       dashboard · slides · Power BI
                                     schema    2 facts)
```

## Results on the 2025 export
| | |
|---|---|
| Raw order lines | 160,821 (3,997 exact duplicates removed and kept in `data/clean/removed/`) |
| Revenue 2025 | €33.51M before returns · 101,142 orders · 205,473 units |
| Quality gate | 41/41 checks pass: code computes, two roads, 10 traced orders, always-true facts |
| December finding | Best month (€3.42M, +10.5%), but Computers −13%: the 3 best Kova models sold out on 14 Nov and were never restocked, costing about **€274K–€442K** in December |

## Data problems found and fixed
Mixed date formats (`2025-01-01` and `01/01/2025`), country codes mixed with names
(`DE` / `Germany`), 16 spellings of 6 brands, 15 spellings of 5 categories, exact duplicate
lines, stock months without the leading zero, an always-empty column, and two markets
(Spain, Austria, 13% of revenue) missing from the company documentation.

## Data
The source data and PDFs are the exercise files of Baraa's LinkedIn Learning course, so they are
not in this repo. Put `orders.csv`, `products.csv`, `inventory.csv` in `data/raw/` and the four PDFs
in `knowledge/inbox/`, then run the pipeline: it rebuilds data/clean and data/mart.
The reports in `reports/` and the run history in `runs/` are included to show the results.

## How to run
```bash
pip install -r requirements.txt
python .claude/skills/pipeline/run_pipeline.py --steps all     # or 1-4, 3-, 5 ...
```
In Claude Code: type `/pipeline` and pick the steps. Each skill also runs on its own:
`/profile`, `/clean`, `/mart`, `/quality-gate`, `/dashboard`, `/slides`, `/powerbi`, `/cleanup`.

New month? Drop the new `orders_*.csv` / `inventory_*.csv` into `data/raw` and run `/pipeline`.

## Project map
| Path | What it is |
|---|---|
| `CLAUDE.md` | Context and behaviour rules Claude reads every session |
| `knowledge/` | company.md, metadata.md, **metrics.md** (semantic layer), **quality-rules.md**, inbox/ (source PDFs) |
| `data/raw → clean → mart` | The three data layers. Raw is never edited. |
| `runs/<date_time>/` | Every run's reports: profile, check, clean, mart (with SQL test), quality, run.md |
| `reports/html/dashboard.html` | Interactive dashboard: filters, click-to-filter on every chart, hover cards. No internet needed |
| `reports/html/data-model.html` | Star schema diagram |
| `reports/slides/december-review.pptx` | December review deck: one slide per question |
| `reports/powerbi/ai-analysis.pbip` | Power BI project: relationships, descriptions, hidden keys, 5 DAX measures from metrics.md |
| `.claude/skills/` | 9 skills; each is a SKILL.md and its Python script |

## Principles
1. **Code computes, Claude explains.** No number is typed by hand; every one comes from a script.
2. **I own the definitions.** Metrics and quality rules are written by me in plain text; the AI must follow them.
3. **Trust layer before reports.** The pipeline stops on any failed check, and reports are staged so a bad run never overwrites a good dashboard.
4. **Repeat it? Make it a skill.**

## Power BI
Open `reports/powerbi/ai-analysis.pbip` in Power BI Desktop and click **Refresh**. If the project
folder moved, run `/powerbi` (or change `mart_path_windows` in `.claude/skills/powerbi/config.json`).
The report page is built by hand, using the HTML dashboard as the mock-up.
