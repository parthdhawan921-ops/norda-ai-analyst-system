# Pipeline run 2026-10-11_073538

Steps chosen: 1, 2, 3, 4, 5, 6, 7  
Result: **PASS**

| step | name | result | seconds | last line |
|---|---|---|---:|---|
| 1 | profile | PASS | 2.8 | check: 27/27 passed |
| 2 | clean | PASS | 2.0 | clean: orders 169,495, products 377, inventory 4,599 -> data/clean |
| 3 | mart | PASS | 1.8 | mart: dim_date 730, dim_product 377, dim_country 6, dim_channel 3, fact_sales 169,495, fact_inventory 4,599 |
| 4 | quality | PASS | 2.4 | quality: 41/41 passed |
| 5 | dashboard | PASS | 0.9 | dashboard: 169,495 lines, 109,209 orders, 13 months -> /sessions/rcw-01qubeanwabvcrfbqhhv67qd/jan-test/runs/2026-10-11_073538/reports/dashboard.html (3.2 MB) |
| 6 | slides | PASS | 1.5 | slides: 2025-12 revenue €3,417,243.75; ran out 11 (big 3); lost €274,438-€441,953; reorder list 15 -> /sessions/rcw-01qubeanwabvcrfbqhhv67qd/jan-test/runs/2026-10-11_073538/reports/december-review.pptx |
| 7 | powerbi | PASS | 0.8 | powerbi: 6 tables, 36 columns described, 6 relationships, 5 measures -> reports/powerbi/ai-analysis.SemanticModel (CSV path D:\Data Analytics\Baraa\Claude\claude linkedin\data\mart) |

Published to reports/: reports/html/dashboard.html, reports/slides/december-review.pptx
