# Profile of data/raw
Run: 2026-10-11 13:13  
Files: orders.csv, products.csv, inventory.csv

## Data quality findings

| id | severity | finding |
|---|---|---|
| O-01 | high | Mixed date formats in CRTD_DT: `99/99/9999` 80,742, `9999-99-99` 80,079. The slash form is DD/MM/YYYY (day values above 12 appear in first position). |
| O-03 | high | CTRY mixes ISO codes and full names: 1,642 rows use names (Austria, France, Germany, Italy, Netherlands, Spain). |
| O-05 | high | 3,997 rows are exact copies of another row (2.49% of lines). They would double count revenue. |
| P-01 | high | brand is written in 16 spellings for 6 real values (mixed casing), e.g. KAIVO/Kaivo/kaivo; KOVA/Kova. |
| P-01 | high | category is written in 15 spellings for 5 real values (mixed casing), e.g. ACCESSORIES/Accessories/accessories; AUDIO/Audio/audio. |
| I-01 | med | 6 stock months written without the leading zero (2025-4, 2025-6, 2025-7, 2025-9). |
| O-04 | med | Countries in the data that the company overview does not list as markets: AT, ES. A documentation gap or new markets: ask the business. |
| P-02 | med | UNIT_PRC differs from catalogue list_price on 72,652 lines (45%). Use UNIT_PRC (price actually paid); list_price is reference only. |
| I-02 | low | Column reserved_qty is empty on all 4,222 rows. |
| I-04 | info | 72 article-months with zero stock (possible stock-outs). |
| I-06 | info | 2 catalogue articles never stocked: KO-27064, NO-78001. |
| O-09 | info | CUST_REF is empty on app 6%, marketplace 76%, web 11%. Expected for marketplace (the platform owns the customer); not a defect. |
| O-11 | info | Column names differ from the source dictionary (ORD_NO vs order_ref, CRTD_DT vs order_date, ART_NO vs article_no) and CHNL, CUST_REF, DISC_PCT are not documented. |
| P-04 | info | 2 catalogue articles never ordered: KO-27064, NO-78001. |

## orders
160,821 rows, 9 columns, 101,142 distinct orders

| column | empty | distinct | examples |
|---|---:|---:|---|
| ORD_NO | 0 | 101,142 | SO443307, SO443308, SO443316, SO443317 |
| CRTD_DT | 0 | 730 | 01/01/2025, 2025-01-01, 31/03/2025, 22/04/2025 |
| CHNL | 0 | 3 | app, marketplace, web |
| CTRY | 0 | 12 | ES, IT, DE, FR |
| CUST_REF | 32,426 | 48,213 | C200416, C132675, C217431, C232615 |
| ART_NO | 0 | 375 | ON-46867, NO-69608, NO-69827, NO-68535 |
| QTY | 0 | 8 | 1, 3, 2, 4 |
| UNIT_PRC | 0 | 339 | 319.99, 36.55, 83.99, 96.99 |
| DISC_PCT | 0 | 11 | 0.0, 0.1, 0.15, 0.2 |

Order dates run from 2025-01-01 to 2025-12-31.

- QTY: min 1, max 8, non-numeric 0
- UNIT_PRC: min 8.99, max 2214.99, non-numeric 0
- DISC_PCT: min 0.0, max 0.5, non-numeric 0

Lines per month:

| month | lines |
|---|---:|
| 2025-01 | 12,532 |
| 2025-02 | 11,422 |
| 2025-03 | 12,358 |
| 2025-04 | 11,895 |
| 2025-05 | 12,955 |
| 2025-06 | 9,869 |
| 2025-07 | 12,340 |
| 2025-08 | 12,756 |
| 2025-09 | 13,890 |
| 2025-10 | 15,344 |
| 2025-11 | 16,105 |
| 2025-12 | 19,355 |

## products
377 rows, 5 columns

| column | empty | distinct | examples |
|---|---:|---:|---|
| sku | 0 | 377 | KA-10999, KA-11490, KA-12729, KA-12730 |
| product_name | 0 | 377 | Kaivo Tab 12 128GB, Kaivo Buds Pro 1, Kaivo X 14 128GB, Kaivo One 13 256GB |
| brand | 0 | 16 | Kaivo, KAIVO, kaivo, Kova |
| category | 0 | 15 | Phones & Tablets, Audio, PHONES & TABLETS, phones & tablets |
| list_price | 0 | 273 | 571.99, 161.95, 1127.99, 619.99 |

## inventory
4,222 rows, 4 columns

| column | empty | distinct | examples |
|---|---:|---:|---|
| art_no | 0 | 375 | KA-10999, KA-11490, KA-12729, KA-12730 |
| stk_month | 0 | 16 | 2025-01, 2025-02, 2025-03, 2025-04 |
| qty_hand | 0 | 499 | 43, 30, 31, 32 |
| reserved_qty | 4,222 | 1 |  |
