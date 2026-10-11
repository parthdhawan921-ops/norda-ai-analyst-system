# Quality gate
Run: 2026-10-11 07:36  
Result: **FAIL** (37/41 checks)

| rule | checks | passed |
|---|---:|---:|
| 1 Code computes | 14 | 14 |
| 2 Two roads | 12 | 8 |
| 3 Trace orders | 11 | 11 |
| 4 Always true | 4 | 4 |

## Key numbers (computed in code)

- Revenue: EUR 36,483,872.59 (before returns)
- Orders: 109,207
- Units sold: 221,866
- Stock on hand 2026-01: 38,459 units

## All checks

| rule | check | result | detail |
|---|---|---|---|
| 1 Code computes | gross_revenue = quantity x unit_price on every line | PASS |  |
| 1 Code computes | net_revenue = qty x price x (1 - discount) on every line (metrics.md) | PASS |  |
| 1 Code computes | discount_amount = gross - net on every line | PASS |  |
| 1 Code computes | cent rounding per line moves the year by < 0.001% of revenue | PASS | revenue unrounded 36,483,884.90 vs stored 36,483,872.59; discount literal 796,436.76 vs stored 796,449.07 |
| 1 Code computes | quantity is a whole number >= 1 | PASS |  |
| 1 Code computes | discount_rate between 0 and 0.5 | PASS |  |
| 1 Code computes | unit_price > 0 | PASS |  |
| 1 Code computes | stock never negative | PASS |  |
| 1 Code computes | every fact key finds its dimension | PASS |  |
| 1 Code computes | dimension keys unique | PASS |  |
| 1 Code computes | inventory: one snapshot per article per month | PASS |  |
| 1 Code computes | raw lines = clean lines + removed lines | PASS | raw 173,808, clean 169,491 |
| 1 Code computes | clean lines = fact_sales lines | PASS | 169,491 |
| 1 Code computes | clean inventory = fact_inventory rows | PASS | 4,599 |
| 2 Two roads | Revenue: sum of mart net_revenue vs recomputed from clean columns | PASS | 36,483,872.59 vs 36,483,872.59 |
| 2 Two roads | Revenue: mart vs straight from raw (own dedupe) | FAIL | 36,483,872.59 vs 36,486,886.43 |
| 2 Two roads | Orders: distinct count vs group-by count vs raw | FAIL | 109,207 / 109,207 / 109,209 |
| 2 Two roads | Units: sum in mart vs sum in raw (deduped) | FAIL | 221,866 |
| 2 Two roads | Revenue: sum of months = total | PASS |  |
| 2 Two roads | Revenue: sum of countries = total | PASS |  |
| 2 Two roads | Revenue: sum of channels = total | PASS |  |
| 2 Two roads | Revenue: sum of categories = total | PASS |  |
| 2 Two roads | Revenue per month: mart (via dim_date) vs raw (via parsed dates) | FAIL | max gap 3,013.8400 |
| 2 Two roads | Stock on hand 2026-01: mart vs clean vs raw | PASS | 38,459 / 38,459 / 38,459 |
| 2 Two roads | Best-selling product: mart vs clean agree | PASS | KO-49107 |
| 2 Two roads | Products out of stock at 2026-01: mart vs clean agree | PASS | 15 products |
| 3 Trace orders | order SO533888: raw -> clean -> mart match | PASS | 2 lines, 3 units, EUR 115.97, DE |
| 3 Trace orders | order SO551405: raw -> clean -> mart match | PASS | 1 lines, 1 units, EUR 151.95, FR |
| 3 Trace orders | order SO478031: raw -> clean -> mart match | PASS | 1 lines, 2 units, EUR 41.74, IT |
| 3 Trace orders | order SO564901: raw -> clean -> mart match | PASS | 1 lines, 3 units, EUR 101.85, DE |
| 3 Trace orders | order SO472846: raw -> clean -> mart match | PASS | 1 lines, 4 units, EUR 759.96, DE |
| 3 Trace orders | order SO531227: raw -> clean -> mart match | PASS | 2 lines, 2 units, EUR 2,227.98, IT |
| 3 Trace orders | order SO452617: raw -> clean -> mart match | PASS | 2 lines, 2 units, EUR 303.99, FR |
| 3 Trace orders | order SO545176: raw -> clean -> mart match | PASS | 3 lines, 4 units, EUR 1,050.68, NL |
| 3 Trace orders | order SO546437: raw -> clean -> mart match | PASS | 2 lines, 2 units, EUR 70.94, DE |
| 3 Trace orders | order SO490787: raw -> clean -> mart match | PASS | 1 lines, 1 units, EUR 14.28, IT |
| 3 Trace orders | sample seed recorded (rerun with --seed to repeat) | PASS | seed 227015 |
| 4 Always true | every month has sales | PASS | 13 months |
| 4 Always true | no empty files in clean or mart | PASS | 9 files |
| 4 Always true | no revenue is negative | PASS |  |
| 4 Always true | December is the biggest month of 2025 by revenue | PASS | biggest 2025-12 EUR 3,417,243.75 |
