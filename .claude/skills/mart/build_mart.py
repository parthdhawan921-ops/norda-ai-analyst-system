"""Build the star schema in data/mart from data/clean.

Dimensions                      Facts
  dim_date     one row per day    fact_sales      one row per order line
  dim_product  one row per sku    fact_inventory  one row per sku per month end
  dim_country  one row per country
  dim_channel  one row per channel

Rules: one-to-many only (dimension 1 -> fact many), no link between the
two facts, keys are stable across rebuilds (sorted business keys).
Revenue follows knowledge/metrics.md and is taken from the clean layer.

Run:  python .claude/skills/mart/build_mart.py  [--run-dir runs/xyz]
"""
import argparse, datetime as dt, os, sqlite3
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").exists())
CLEAN, MART = ROOT / "data" / "clean", ROOT / "data" / "mart"

COUNTRY_NAMES = {"DE": "Germany", "FR": "France", "IT": "Italy", "NL": "Netherlands",
                 "ES": "Spain", "AT": "Austria"}
OFFICIAL = {"DE", "FR", "IT", "NL"}          # knowledge/company.md
CHANNELS = ["web", "app", "marketplace"]


def build():
    o = pd.read_csv(CLEAN / "orders.csv", dtype={"customer_id": str, "order_id": str})
    p = pd.read_csv(CLEAN / "products.csv")
    i = pd.read_csv(CLEAN / "inventory.csv", dtype={"stock_month": str})

    # ---- dim_date: whole calendar years covering sales and stock
    first = min(pd.to_datetime(o["order_date"]).min(), pd.to_datetime(i["stock_month"] + "-01").min())
    last = max(pd.to_datetime(o["order_date"]).max(),
               pd.to_datetime(i["stock_month"] + "-01").max() + pd.offsets.MonthEnd(0))
    days = pd.date_range(f"{first.year}-01-01", f"{last.year}-12-31", freq="D")
    dim_date = pd.DataFrame({
        "date_key": days.strftime("%Y%m%d").astype(int),
        "date": days.strftime("%Y-%m-%d"),
        "year": days.year, "quarter": days.quarter, "month_num": days.month,
        "month_name": days.strftime("%B"), "year_month": days.strftime("%Y-%m"),
        "day_of_month": days.day, "is_month_end": days.is_month_end.astype(int),
    })

    # ---- dim_product: the whole catalogue, key from sorted sku
    dim_product = p.sort_values("sku").reset_index(drop=True)
    dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))
    dim_product = dim_product[["product_key", "sku", "product_name", "brand", "category", "list_price"]]

    # ---- dim_country / dim_channel
    codes = sorted(set(o["country_code"]) | OFFICIAL)
    dim_country = pd.DataFrame({"country_key": range(1, len(codes) + 1), "country_code": codes,
                                "country_name": [COUNTRY_NAMES.get(c, c) for c in codes],
                                "in_company_overview": ["Yes" if c in OFFICIAL else "No" for c in codes]})
    chans = CHANNELS + sorted(set(o["channel"]) - set(CHANNELS))
    dim_channel = pd.DataFrame({"channel_key": range(1, len(chans) + 1), "channel_name": chans})

    # ---- fact_sales
    f = o.merge(dim_product[["product_key", "sku"]], on="sku", how="left") \
         .merge(dim_country[["country_key", "country_code"]], on="country_code", how="left") \
         .merge(dim_channel, left_on="channel", right_on="channel_name", how="left")
    f["order_date_key"] = f["order_date"].str.replace("-", "").astype(int)
    fact_sales = f[["order_date_key", "product_key", "country_key", "channel_key", "order_id",
                    "quantity", "unit_price", "discount_rate", "gross_revenue", "discount_amount",
                    "net_revenue"]]

    # ---- fact_inventory: snapshot on the last day of the month
    inv = i.merge(dim_product[["product_key", "sku"]], on="sku", how="left")
    month_end = pd.to_datetime(inv["stock_month"] + "-01") + pd.offsets.MonthEnd(0)
    inv["snapshot_date_key"] = month_end.dt.strftime("%Y%m%d").astype(int)
    fact_inventory = inv[["snapshot_date_key", "product_key", "stock_month", "quantity_on_hand"]]

    tables = dict(dim_date=dim_date, dim_product=dim_product, dim_country=dim_country,
                  dim_channel=dim_channel, fact_sales=fact_sales, fact_inventory=fact_inventory)
    return tables, o, i


def validate(t, o, i):
    r = []
    fs, fi = t["fact_sales"], t["fact_inventory"]
    for dim, key in [("dim_date", "date_key"), ("dim_product", "product_key"),
                     ("dim_country", "country_key"), ("dim_channel", "channel_key")]:
        r.append((f"{dim}: {key} unique (the '1' side)", t[dim][key].is_unique, f"{len(t[dim]):,} rows"))
    for col, dim, key in [("order_date_key", "dim_date", "date_key"), ("product_key", "dim_product", "product_key"),
                          ("country_key", "dim_country", "country_key"), ("channel_key", "dim_channel", "channel_key")]:
        miss = (~fs[col].isin(t[dim][key])) | fs[col].isna()
        r.append((f"fact_sales.{col} -> {dim}: no orphans", not miss.any(), f"{miss.sum()} orphans"))
    for col, dim, key in [("snapshot_date_key", "dim_date", "date_key"), ("product_key", "dim_product", "product_key")]:
        miss = (~fi[col].isin(t[dim][key])) | fi[col].isna()
        r.append((f"fact_inventory.{col} -> {dim}: no orphans", not miss.any(), f"{miss.sum()} orphans"))
    r.append(("fact_sales rows = clean orders rows", len(fs) == len(o), f"{len(fs):,} vs {len(o):,}"))
    r.append(("fact_inventory rows = clean inventory rows", len(fi) == len(i), f"{len(fi):,} vs {len(i):,}"))
    r.append(("revenue in fact = revenue in clean", abs(fs["net_revenue"].sum() - o["net_revenue"].sum()) < 0.01,
              f"{fs['net_revenue'].sum():,.2f}"))
    r.append(("snapshot dates are month ends",
              t["dim_date"].set_index("date_key").loc[fi["snapshot_date_key"], "is_month_end"].eq(1).all(), ""))
    r.append(("no link between the two facts", set(fs.columns) & set(fi.columns) <= {"product_key"}, ""))
    return r


def sql_test(t):
    """Business test from the course: top products by revenue, through SQL on the star schema."""
    con = sqlite3.connect(":memory:")
    for name, df in t.items():
        df.to_sql(name, con, index=False)
    sql = """SELECT p.product_name, p.category,
       ROUND(SUM(f.net_revenue), 2)  AS revenue,
       COUNT(DISTINCT f.order_id)    AS orders
FROM fact_sales f
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;"""
    res = pd.read_sql(sql, con)
    return sql, res


def table_md(df):
    """Markdown table without needing the optional 'tabulate' package."""
    fmt = lambda v: f"{v:,.2f}" if isinstance(v, float) else (f"{v:,}" if isinstance(v, int) else str(v))
    rows = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    rows += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=os.environ.get("RUN_DIR"))
    args = ap.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else ROOT / "runs" / dt.date.today().isoformat()
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    MART.mkdir(parents=True, exist_ok=True)

    t, o, i = build()
    for name, df in t.items():
        df.to_csv(MART / f"{name}.csv", index=False)
    checks = validate(t, o, i)
    sql, res = sql_test(t)
    failed = [c for c in checks if not c[1]]
    md = ["# Mart build", f"Run: {dt.datetime.now():%Y-%m-%d %H:%M}  ",
          f"Checks: **{'PASS' if not failed else 'FAIL'}** ({len(checks) - len(failed)}/{len(checks)})", "",
          "## Tables", "", "| table | rows | columns |", "|---|---:|---|"] + \
         [f"| {n} | {len(df):,} | {', '.join(df.columns)} |" for n, df in t.items()] + \
         ["", "Diagram: reports/html/data-model.html", "", "## Checks", "",
          "| check | result | detail |", "|---|---|---|"] + \
         [f"| {n} | {'PASS' if ok else 'FAIL'} | {d} |" for n, ok, d in checks] + \
         ["", "## Test question: top 10 products by revenue", "", "```sql", sql, "```", "",
          table_md(res)]
    (run_dir / "mart.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for n, ok, d in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {n}  {d}")
    print("mart: " + ", ".join(f"{n} {len(df):,}" for n, df in t.items()))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
