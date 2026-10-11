# End-to-end test with new data (course lesson 4.1 exercise)

Done on a COPY of the project, so data/raw here stays 2025-only.

| # | Test | What we did | Result |
|---|---|---|---|
| 1 | New month arrives | Copied `orders_january.csv` + `inventory_january.csv` (from data/incoming) into data/raw, ran `/pipeline` all steps | **PASS 7/7**: check 27/27, 12,987 Jan lines (+316 duplicates removed), quality 41/41, dashboard 13 months (Jan 2025 – Jan 2026), Dec deck unchanged |
| 2 | Bad data arrives | Planted a new country (PL), a negative quantity and an unknown article in the January file | **Stopped at step 1**: check 24/27 named all 3 problems. Nothing published, dashboard untouched |
| 3 | Someone skips the check | Ran steps 2-4 on the bad file | Clean quarantined the 7 bad lines with a reason (`data/clean/removed/orders_invalid.csv`); quality gate **FAILED** 4 checks because mart and raw now differ by exactly the quarantined €3,013.84, so nothing is published until a human decides |

January had the same kinds of problems as 2025 (mixed dates, country names, duplicates) and nothing new.
Files: run summaries 1-3 in this folder, and `reports/dashboard_with_january.html`.
