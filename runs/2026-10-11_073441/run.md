# Pipeline run 2026-10-11_073441

Steps chosen: 1, 2, 3, 4, 5, 6, 7  
Result: **PASS**

| step | name | result | seconds | last line |
|---|---|---|---:|---|
| 1 | profile | PASS | 3.3 | check: 25/25 passed |
| 2 | clean | PASS | 6.6 | clean: orders 156,824, products 377, inventory 4,222 -> data/clean |
| 3 | mart | PASS | 5.7 | mart: dim_date 365, dim_product 377, dim_country 6, dim_channel 3, fact_sales 156,824, fact_inventory 4,222 |
| 4 | quality | PASS | 3.9 | quality: 41/41 passed |
| 5 | dashboard | PASS | 1.9 | dashboard: 156,824 lines, 101,142 orders, 12 months -> /sessions/rcw-01qubeanwabvcrfbqhhv67qd/mnt/claude linkedin/runs/2026-10-11_073441/reports/dashboard.html (3.0 MB) |
| 6 | slides | PASS | 1.8 | slides: 2025-12 revenue €3,417,243.75; ran out 11 (big 3); lost €274,438-€441,953; reorder list 15 -> /sessions/rcw-01qubeanwabvcrfbqhhv67qd/mnt/claude linkedin/runs/2026-10-11_073441/reports/december-review.pptx |
| 7 | powerbi | PASS | 1.0 | powerbi: 6 tables, 36 columns described, 6 relationships, 5 measures -> reports/powerbi/ai-analysis.SemanticModel (CSV path D:\Data Analytics\Baraa\Claude\claude linkedin\data\mart) |

Published to reports/: reports/html/dashboard.html, reports/slides/december-review.pptx
