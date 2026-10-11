---
name: powerbi
description: Write the Power BI semantic model (relationships, descriptions, hidden keys, DAX measures from knowledge/metrics.md, formats) as TMDL code in reports/powerbi. Use after /mart when the model or metrics change.
---

# Power BI model

## Steps
1. Run `python .claude/skills/powerbi/build_pbi.py`
2. Open `reports/powerbi/ai-analysis.pbip` in Power BI Desktop and click **Refresh**.
3. Check in Model view: facts in the middle, only one-to-many lines, no line between facts.
4. Build the report page yourself, using `reports/html/dashboard.html` as the mock-up.

## What the script does
- Relationships like the mart; keys hidden (and month_num, which only sorts month_name).
  Nothing else is hidden: tell the user before hiding more.
- One measure per metric in `knowledge/metrics.md`, in display folder `metrics`; each
  description quotes the metrics.md line it comes from.
- Money in euro format, counts as whole numbers, discount as %.
- CSV path: on Windows it uses this project's data/mart; otherwise `config.json`.

## Rules
- Never write DAX for a metric that is not in metrics.md. Ask the user to define it first.
- If a mart table gets a new column, add its description to `TABLES` or the script stops.
- Close Power BI Desktop before running the script, then reopen.
