# NORDA - company knowledge
Source: knowledge/inbox/norda-overview.pdf. Updated by Claude as we learn more.

## Business
- European consumer electronics retailer. Buys from suppliers, holds stock in ONE warehouse, sells direct to consumers.
- Small range on purpose: 6 brands, 5 categories.
- All markets are eurozone, so every price is in EUR. There is no currency column.
- Returns and refunds live in a separate system. Every row in the export is a sale that left the warehouse (figures are before returns).

## Markets
- Official markets: Germany (home and largest), France, Italy, Netherlands.
- The data ALSO contains Spain and Austria. Open question for the business (see metadata.md).

## Channels
- web: own online shop
- app: NORDA mobile app
- marketplace: third-party platforms. Customers belong to the platform, so these orders usually have no customer reference.

## Categories
| Category | Notes |
|---|---|
| Computers | laptops and desktops, highest value |
| Phones & Tablets | highest volume |
| Monitors | home and office displays |
| Audio | headphones, speakers, sound bars |
| Accessories | cables, cases, chargers, keyboards |

## Brands
| Brand | Range |
|---|---|
| Kova | premium computers, a few monitors. Most expensive |
| Kaivo | mid/upper phones and tablets, a few audio |
| Pavo | budget phones and tablets |
| Visna | monitors |
| Ondia | audio only |
| Nodo | accessories only. Widest range, lowest prices |

## The shop system export
- Monthly, first working day: orders (one row per order line), products (catalogue), inventory (stock at month end).
- Straight dump from operational tables. Not validated or cleaned. Format changed over the years.

## Who uses the reports
- Commercial and purchasing teams. They plan buying and review categories.
- They ask business questions, not data requests.
