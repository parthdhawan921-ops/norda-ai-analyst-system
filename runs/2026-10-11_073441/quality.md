# Quality gate
Run: 2026-10-11 07:35  
Result: **PASS** (41/41 checks)

| rule | checks | passed |
|---|---:|---:|
| 1 Code computes | 14 | 14 |
| 2 Two roads | 12 | 12 |
| 3 Trace orders | 11 | 11 |
| 4 Always true | 4 | 4 |

## Key numbers (computed in code)

- Revenue: EUR 33,506,864.27 (before returns)
- Orders: 101,142
- Units sold: 205,473
- Stock on hand 2025-12: 41,307 units

## All checks

| rule | check | result | detail |
|---|---|---|---|
| 1 Code computes | gross_revenue = quantity x unit_price on every line | PASS |  |
| 1 Code computes | net_revenue = qty x price x (1 - discount) on every line (metrics.md) | PASS |  |
| 1 Code computes | discount_amount = gross - net on every line | PASS |  |
| 1 Code computes | cent rounding per line moves the year by < 0.001% of revenue | PASS | revenue unrounded 33,506,875.93 vs stored 33,506,864.27; discount literal 738,919.26 vs stored 738,930.92 |
| 1 Code computes | quantity is a whole number >= 1 | PASS |  |
| 1 Code computes | discount_rate between 0 and 0.5 | PASS |  |
| 1 Code computes | unit_price > 0 | PASS |  |
| 1 Code computes | stock never negative | PASS |  |
| 1 Code computes | every fact key finds its dimension | PASS |  |
| 1 Code computes | dimension keys unique | PASS |  |
| 1 Code computes | inventory: one snapshot per article per month | PASS |  |
| 1 Code computes | raw lines = clean lines + removed lines | PASS | raw 160,821, clean 156,824 |
| 1 Code computes | clean lines = fact_sales lines | PASS | 156,824 |
| 1 Code computes | clean inventory = fact_inventory rows | PASS | 4,222 |
| 2 Two roads | Revenue: sum of mart net_revenue vs recomputed from clean columns | PASS | 33,506,864.27 vs 33,506,864.27 |
| 2 Two roads | Revenue: mart vs straight from raw (own dedupe) | PASS | 33,506,864.27 vs 33,506,864.27 |
| 2 Two roads | Orders: distinct count vs group-by count vs raw | PASS | 101,142 / 101,142 / 101,142 |
| 2 Two roads | Units: sum in mart vs sum in raw (deduped) | PASS | 205,473 |
| 2 Two roads | Revenue: sum of months = total | PASS |  |
| 2 Two roads | Revenue: sum of countries = total | PASS |  |
| 2 Two roads | Revenue: sum of channels = total | PASS |  |
| 2 Two roads | Revenue: sum of categories = total | PASS |  |
| 2 Two roads | Revenue per month: mart (via dim_date) vs raw (via parsed dates) | PASS | max gap 0.0000 |
| 2 Two roads | Stock on hand 2025-12: mart vs clean vs raw | PASS | 41,307 / 41,307 / 41,307 |
| 2 Two roads | Best-selling product: mart vs clean agree | PASS | KO-49107 |
| 2 Two roads | Products out of stock at 2025-12: mart vs clean agree | PASS | 11 products |
| 3 Trace orders | order SO487615: raw -> clean -> mart match | PASS | 1 lines, 1 units, EUR 16.95, DE |
| 3 Trace orders | order SO449964: raw -> clean -> mart match | PASS | 2 lines, 2 units, EUR 219.95, DE |
| 3 Trace orders | order SO525657: raw -> clean -> mart match | PASS | 2 lines, 2 units, EUR 78.98, DE |
| 3 Trace orders | order SO553414: raw -> clean -> mart match | PASS | 2 lines, 2 units, EUR 630.56, NL |
| 3 Trace orders | order SO537866: raw -> clean -> mart match | PASS | 2 lines, 3 units, EUR 29.99, FR |
| 3 Trace orders | order SO459813: raw -> clean -> mart match | PASS | 1 lines, 1 units, EUR 188.06, DE |
| 3 Trace orders | order SO467621: raw -> clean -> mart match | PASS | 2 lines, 2 units, EUR 302.98, ES |
| 3 Trace orders | order SO480087: raw -> clean -> mart match | PASS | 2 lines, 2 units, EUR 270.90, DE |
| 3 Trace orders | order SO472738: raw -> clean -> mart match | PASS | 1 lines, 1 units, EUR 39.94, NL |
| 3 Trace orders | order SO450385: raw -> clean -> mart match | PASS | 1 lines, 1 units, EUR 652.95, NL |
| 3 Trace orders | sample seed recorded (rerun with --seed to repeat) | PASS | seed 864105 |
| 4 Always true | every month has sales | PASS | 12 months |
| 4 Always true | no empty files in clean or mart | PASS | 9 files |
| 4 Always true | no revenue is negative | PASS |  |
| 4 Always true | December is the biggest month of 2025 by revenue | PASS | biggest 2025-12 EUR 3,417,243.75 |
