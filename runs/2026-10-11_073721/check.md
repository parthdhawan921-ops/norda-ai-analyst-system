# Raw data check
Run: 2026-10-11 07:37  
Result: **PASS** (25/25 passed)

| check | result | detail |
|---|---|---|
| orders: file present | PASS | orders.csv |
| orders: not empty | PASS | 160,821 rows |
| orders: columns as expected (orders.csv) | PASS |  |
| products: file present | PASS | products.csv |
| products: not empty | PASS | 377 rows |
| products: columns as expected (products.csv) | PASS |  |
| inventory: file present | PASS | inventory.csv |
| inventory: not empty | PASS | 4,222 rows |
| inventory: columns as expected (inventory.csv) | PASS |  |
| orders: every date parses (YYYY-MM-DD or DD/MM/YYYY) | PASS | 0 bad |
| orders: no unknown country | PASS |  |
| orders: no unknown channel | PASS |  |
| orders: quantity is a whole number > 0 | PASS |  |
| orders: unit price is a number > 0 | PASS |  |
| orders: discount between 0 and max | PASS | max seen 0.5 |
| orders: order number never empty | PASS |  |
| orders: every article exists in the catalogue | PASS | 0 missing |
| orders: no volume drop in latest month | PASS | 2025-12: 19,355 lines = 154% of usual 12,532 |
| products: sku unique | PASS |  |
| products: brands known (any casing) | PASS |  |
| products: categories known (any casing) | PASS |  |
| products: list price is a number > 0 | PASS |  |
| inventory: month looks like YYYY-MM or YYYY-M | PASS |  |
| inventory: stock is a number >= 0 | PASS |  |
| inventory: every article exists in the catalogue | PASS |  |
