# Pipeline run 2026-10-11_073621

Steps chosen: 2, 3, 4  
Result: **STOPPED ON FAILURE**

| step | name | result | seconds | last line |
|---|---|---|---:|---|
| 2 | clean | PASS | 2.1 | clean: orders 169,491, products 377, inventory 4,599 -> data/clean |
| 3 | mart | PASS | 1.7 | mart: dim_date 730, dim_product 377, dim_country 6, dim_channel 3, fact_sales 169,491, fact_inventory 4,599 |
| 4 | quality | FAIL | 2.1 | quality: 37/41 passed |

Published to reports/: nothing - staged reports stay in this run folder
