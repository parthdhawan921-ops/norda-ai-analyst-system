# Mart build
Run: 2026-10-11 07:34  
Checks: **PASS** (15/15)

## Tables

| table | rows | columns |
|---|---:|---|
| dim_date | 365 | date_key, date, year, quarter, month_num, month_name, year_month, day_of_month, is_month_end |
| dim_product | 377 | product_key, sku, product_name, brand, category, list_price |
| dim_country | 6 | country_key, country_code, country_name, in_company_overview |
| dim_channel | 3 | channel_key, channel_name |
| fact_sales | 156,824 | order_date_key, product_key, country_key, channel_key, order_id, quantity, unit_price, discount_rate, gross_revenue, discount_amount, net_revenue |
| fact_inventory | 4,222 | snapshot_date_key, product_key, stock_month, quantity_on_hand |

Diagram: reports/html/data-model.html

## Checks

| check | result | detail |
|---|---|---|
| dim_date: date_key unique (the '1' side) | PASS | 365 rows |
| dim_product: product_key unique (the '1' side) | PASS | 377 rows |
| dim_country: country_key unique (the '1' side) | PASS | 6 rows |
| dim_channel: channel_key unique (the '1' side) | PASS | 3 rows |
| fact_sales.order_date_key -> dim_date: no orphans | PASS | 0 orphans |
| fact_sales.product_key -> dim_product: no orphans | PASS | 0 orphans |
| fact_sales.country_key -> dim_country: no orphans | PASS | 0 orphans |
| fact_sales.channel_key -> dim_channel: no orphans | PASS | 0 orphans |
| fact_inventory.snapshot_date_key -> dim_date: no orphans | PASS | 0 orphans |
| fact_inventory.product_key -> dim_product: no orphans | PASS | 0 orphans |
| fact_sales rows = clean orders rows | PASS | 156,824 vs 156,824 |
| fact_inventory rows = clean inventory rows | PASS | 4,222 vs 4,222 |
| revenue in fact = revenue in clean | PASS | 33,506,864.27 |
| snapshot dates are month ends | PASS |  |
| no link between the two facts | PASS |  |

## Test question: top 10 products by revenue

```sql
SELECT p.product_name, p.category,
       ROUND(SUM(f.net_revenue), 2)  AS revenue,
       COUNT(DISTINCT f.order_id)    AS orders
FROM fact_sales f
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;
```

| product_name | category | revenue | orders |
|---|---|---|---|
| Kova K7-2800 | Computers | 2,417,218.32 | 964 |
| Kaivo Pro X2 | Phones & Tablets | 1,931,052.00 | 1,917 |
| Kova K7-2200X | Computers | 1,508,210.36 | 764 |
| Kova K5-1900 | Computers | 985,522.52 | 650 |
| Kova K5-2000X | Computers | 875,505.75 | 522 |
| Kova K5-1500 | Computers | 702,822.22 | 667 |
| Kaivo X 12 512GB | Phones & Tablets | 549,189.59 | 489 |
| Kaivo Pro 12 256GB | Phones & Tablets | 498,280.95 | 527 |
| Pavo Max 2 128GB | Phones & Tablets | 494,248.99 | 1,375 |
| Kova K5-1600X | Computers | 492,741.96 | 444 |
