---
name: mart
description: Build the star schema data mart (4 dimensions, 2 facts) in data/mart from data/clean, validate it, and test it with a SQL business question. Use after /clean or when asked to rebuild the data model.
---

# Mart (data modelling)

## The model (see reports/html/data-model.html)
- `fact_sales` (one row per order line) -> dim_date, dim_product, dim_country, dim_channel
- `fact_inventory` (one row per article per month end) -> dim_date, dim_product
- One-to-many only. No relationship between the two facts.
- Revenue, discount and orders follow `knowledge/metrics.md`. Never invent a calculation:
  if a requirement needs a metric that is not in metrics.md, ask the user to define it.

## Steps
1. Run folder: `runs/<YYYY-MM-DD>` unless the pipeline gave one (env `RUN_DIR`).
2. Run `python .claude/skills/mart/build_mart.py --run-dir <run folder>`
3. Exit code 1 = a model check failed (orphan keys, row or revenue mismatch). Stop and report.
4. Report short: row count per table, check result, and the top-10 products answer
   with the SQL from `<run folder>/mart.md`.

## Rules
- Read only from data/clean. Write only to data/mart.
- Keys come from sorted business keys, so a rebuild gives the same keys.
- If the model changes, update the diagram in reports/html/data-model.html and the
  Power BI model (/powerbi).
