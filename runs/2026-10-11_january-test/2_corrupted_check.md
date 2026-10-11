# Raw data check
Run: 2026-10-11 07:36  
Result: **FAIL** (24/27 passed)

| check | result | detail |
|---|---|---|
| orders: file present | PASS | orders.csv, orders_january.csv |
| orders: not empty | PASS | 173,808 rows |
| orders: columns as expected (orders.csv) | PASS |  |
| orders: columns as expected (orders_january.csv) | PASS |  |
| products: file present | PASS | products.csv |
| products: not empty | PASS | 377 rows |
| products: columns as expected (products.csv) | PASS |  |
| inventory: file present | PASS | inventory.csv, inventory_january.csv |
| inventory: not empty | PASS | 4,599 rows |
| inventory: columns as expected (inventory.csv) | PASS |  |
| inventory: columns as expected (inventory_january.csv) | PASS |  |
| orders: every date parses (YYYY-MM-DD or DD/MM/YYYY) | PASS | 0 bad |
| orders: no unknown country | FAIL | PL |
| orders: no unknown channel | PASS |  |
| orders: quantity is a whole number > 0 | FAIL |  |
| orders: unit price is a number > 0 | PASS |  |
| orders: discount between 0 and max | PASS | max seen 0.5 |
| orders: order number never empty | PASS |  |
| orders: every article exists in the catalogue | FAIL | 1 missing |
| orders: no volume drop in latest month | PASS | 2026-01: 12,987 lines = 103% of usual 12,644 |
| products: sku unique | PASS |  |
| products: brands known (any casing) | PASS |  |
| products: categories known (any casing) | PASS |  |
| products: list price is a number > 0 | PASS |  |
| inventory: month looks like YYYY-MM or YYYY-M | PASS |  |
| inventory: stock is a number >= 0 | PASS |  |
| inventory: every article exists in the catalogue | PASS |  |
