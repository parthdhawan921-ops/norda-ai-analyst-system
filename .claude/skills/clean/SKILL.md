---
name: clean
description: Clean the raw shop export from data/raw into data/clean, keep every removed row with a reason, and validate the result. Use after /profile passes or when asked to clean the data.
---

# Clean

## Steps
1. Run folder: `runs/<YYYY-MM-DD>` unless the pipeline gave one (env `RUN_DIR`).
2. Run `python .claude/skills/clean/clean.py --run-dir <run folder>`
3. Exit code 1 = a check on the clean data failed. Stop and show the failing check.
4. Report short: rows in, rows out, rows removed and why (from `<run folder>/clean.md`).

## What it fixes
- Mixed date formats -> YYYY-MM-DD
- Country names -> ISO codes; brand/category casing -> one spelling
- Exact duplicate lines -> `data/clean/removed/orders_duplicates.csv`
- Stock month `2025-4` -> `2025-04`; empty `reserved_qty` dropped
- Friendly lowercase column names; revenue columns per line (knowledge/metrics.md)

## Rules
- Never edit data/raw. Never delete removed rows: they go to data/clean/removed/.
- A new kind of problem in the profile = add a fix here AND a check in `validate()`.
