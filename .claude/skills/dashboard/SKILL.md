---
name: dashboard
description: Rebuild the interactive HTML sales dashboard (KPIs, revenue per month, country, top products, stock vs sales, cross-filtering) from data/mart. Use after the quality gate passes or when asked for the dashboard.
---

# Dashboard

## Steps
1. Make sure the quality gate passed for the current mart. If not, stop.
2. Run `python .claude/skills/dashboard/dashboard.py`
   (pipeline passes `--out <run folder>/reports/dashboard.html` to stage it first)
3. Open `reports/html/dashboard.html` in a browser (right-click -> Copy Path).
4. Report short: file path, size, and the headline KPIs it shows.

## Design (locked style)
- Dark mode, calm blue for data, orange only to highlight the best/selected item,
  red/amber/green only for stock status (always with a text label).
- Requirements -> visual: KPIs = big number + sparkline; per month = line chart;
  top products and countries = horizontal bars; stock vs sales = status table.
- BI dashboard, not a story: every chart filters the whole page on click
  (click again to clear), hover shows a detail card, filters in one row on top.
- Self-contained: no internet, no libraries. Data comes ONLY from data/mart.

## Files
- `dashboard.py` packs the mart into the page; `template.html` is the page itself.
  Change the look in template.html, the data in dashboard.py.

## Rules
- Read only from data/mart. Never compute a metric that is not in knowledge/metrics.md.
- Keep it one self-contained file: no CDN, no internet.
- Keep the locked style unless the user asks to change it.
