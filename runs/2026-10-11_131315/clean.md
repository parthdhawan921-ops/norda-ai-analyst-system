# Clean run
Run: 2026-10-11 13:13  
Checks: **PASS** (14/14)

## What changed

- **products**: raw 377; clean 377; removed 0; brand spellings 16 -> 6; category spellings 15 -> 5
- **orders**: raw 160,821; clean 156,824; removed duplicates 3,997; removed invalid 0; country names fixed 1,642; dates reformatted 80,742
- **inventory**: raw 4,222; clean 4,222; removed 0; months fixed 6; dropped columns reserved_qty (empty on every row)

Removed rows are kept in data/clean/removed/ with a reason column.

## Checks on the clean data

| check | result | detail |
|---|---|---|
| orders: no duplicate lines | PASS |  |
| orders: dates are YYYY-MM-DD | PASS |  |
| orders: countries are 2-letter codes | PASS | AT, DE, ES, FR, IT, NL |
| orders: channels lowercase, 3 known | PASS |  |
| orders: every sku in products | PASS |  |
| orders: net + discount = gross on every line | PASS |  |
| orders: no negative revenue | PASS |  |
| orders: raw = clean + removed | PASS | 160,821 = 156,824 + 3,997 + 0 |
| products: 6 brands, 5 categories | PASS |  |
| products: sku unique | PASS |  |
| inventory: months are YYYY-MM | PASS |  |
| inventory: one count per article per month | PASS |  |
| inventory: raw = clean + removed | PASS |  |
| all columns lowercase | PASS |  |
