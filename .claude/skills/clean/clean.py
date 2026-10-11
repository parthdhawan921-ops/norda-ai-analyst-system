"""Clean data/raw into data/clean. data/raw is never changed.

orders    -> data/clean/orders.csv
products  -> data/clean/products.csv
inventory -> data/clean/inventory.csv
Every row taken out goes to data/clean/removed/ with a reason, so
raw rows = clean rows + removed rows always holds.

Fixes (from the profile findings):
  O-01 dates: DD/MM/YYYY and YYYY-MM-DD -> YYYY-MM-DD
  O-03 country names -> ISO codes (Germany -> DE)
  O-05 exact duplicate lines -> removed/orders_duplicates.csv
  P-01 brand / category casing -> one spelling each
  I-01 stock month 2025-4 -> 2025-04
  I-02 reserved_qty (always empty) dropped
  plus: friendly lowercase column names, numbers as numbers,
  revenue columns computed once here, per line, rounded to the cent.

Run:  python .claude/skills/clean/clean.py  [--run-dir runs/xyz]
"""
import argparse, datetime as dt, glob, os
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").exists())
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
REMOVED = CLEAN / "removed"

COUNTRY = {"Germany": "DE", "France": "FR", "Italy": "IT", "Netherlands": "NL", "Spain": "ES", "Austria": "AT"}
BRANDS = ["Kaivo", "Kova", "Nodo", "Ondia", "Pavo", "Visna"]
CATEGORIES = ["Accessories", "Audio", "Computers", "Monitors", "Phones & Tablets"]


def load(kind):
    files = sorted(glob.glob(str(RAW / f"{kind}*.csv")))
    if not files:
        raise SystemExit(f"clean: no {kind}*.csv in data/raw")
    return pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in files], ignore_index=True)


def parse_dates(s):
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    iso = s.str.match(r"^\d{4}-\d{2}-\d{2}$")
    eu = s.str.match(r"^\d{2}/\d{2}/\d{4}$")
    out[iso] = pd.to_datetime(s[iso], format="%Y-%m-%d", errors="coerce")
    out[eu] = pd.to_datetime(s[eu], format="%d/%m/%Y", errors="coerce")
    return out


def to_cent(x):
    """Round half-up to the cent. Plain round() rounds 0.005 down too often because of
    how computers store decimals, which made the yearly total drift by about EUR 17."""
    return np.floor(x * 100 + 0.5 + 1e-7) / 100


def canon(series, allowed):
    lookup = {a.lower(): a for a in allowed}
    return series.str.strip().str.lower().map(lookup)


def clean_products(log):
    raw = load("products")
    p = pd.DataFrame({
        "sku": raw["sku"].str.strip(),
        "product_name": raw["product_name"].str.strip(),
        "brand": canon(raw["brand"], BRANDS),
        "category": canon(raw["category"], CATEGORIES),
        "list_price": pd.to_numeric(raw["list_price"], errors="coerce"),
    })
    bad = p["brand"].isna() | p["category"].isna() | p["list_price"].isna() | p["sku"].duplicated()
    log["products"] = dict(raw=len(raw), clean=int((~bad).sum()), removed=int(bad.sum()),
                           brand_spellings=f"{raw['brand'].nunique()} -> {p['brand'].nunique()}",
                           category_spellings=f"{raw['category'].nunique()} -> {p['category'].nunique()}")
    if bad.any():
        raw[bad].assign(reason="unknown brand/category, bad price or duplicate sku") \
            .to_csv(REMOVED / "products_invalid.csv", index=False)
    return p[~bad].sort_values("sku").reset_index(drop=True)


def clean_orders(products, log):
    raw = load("orders")
    o = pd.DataFrame({
        "order_id": raw["ORD_NO"].str.strip(),
        "order_date": parse_dates(raw["CRTD_DT"].str.strip()),
        "channel": raw["CHNL"].str.strip().str.lower(),
        "country_code": raw["CTRY"].str.strip().replace(COUNTRY).str.upper(),
        "customer_id": raw["CUST_REF"].str.strip(),
        "sku": raw["ART_NO"].str.strip(),
        "quantity": pd.to_numeric(raw["QTY"], errors="coerce"),
        "unit_price": pd.to_numeric(raw["UNIT_PRC"], errors="coerce"),
        "discount_rate": pd.to_numeric(raw["DISC_PCT"], errors="coerce"),
    })
    reason = pd.Series("", index=o.index)
    reason[o["order_date"].isna()] = "date not parseable"
    reason[(reason == "") & ~(o["quantity"] > 0)] = "quantity missing or <= 0"
    reason[(reason == "") & ~(o["unit_price"] > 0)] = "unit price missing or <= 0"
    reason[(reason == "") & ~o["discount_rate"].between(0, 1)] = "discount outside 0-1"
    reason[(reason == "") & ~o["sku"].isin(products["sku"])] = "article not in catalogue"
    reason[(reason == "") & ~o["country_code"].isin(COUNTRY.values())] = "unknown country"
    invalid = reason != ""
    if invalid.any():
        raw[invalid].assign(reason=reason[invalid]).to_csv(REMOVED / "orders_invalid.csv", index=False)
    o = o[~invalid]
    # duplicates are judged AFTER standardising, so 01/01/2025 and 2025-01-01 copies are caught too
    dup = o.duplicated(keep="first")
    raw.loc[dup[dup].index].assign(reason="exact duplicate of an earlier line") \
        .to_csv(REMOVED / "orders_duplicates.csv", index=False)
    o = o[~dup].copy()
    o["quantity"] = o["quantity"].astype(int)
    o["order_date"] = o["order_date"].dt.strftime("%Y-%m-%d")
    # metrics.md: revenue = quantity x unit price x (1 - discount); computed per line, rounded to the cent
    gross = o["quantity"] * o["unit_price"]
    o["gross_revenue"] = to_cent(gross)
    o["net_revenue"] = to_cent(gross * (1 - o["discount_rate"]))
    o["discount_amount"] = (o["gross_revenue"] - o["net_revenue"]).round(2)
    log["orders"] = dict(raw=len(raw), clean=len(o), removed_duplicates=int(dup.sum()),
                         removed_invalid=int(invalid.sum()),
                         country_names_fixed=int(raw["CTRY"].isin(COUNTRY).sum()),
                         dates_reformatted=int(raw["CRTD_DT"].str.contains("/").sum()))
    return o.sort_values(["order_date", "order_id", "sku"]).reset_index(drop=True)


def clean_inventory(products, log):
    raw = load("inventory")
    month = raw["stk_month"].str.strip().str.replace(r"^(\d{4})-(\d)$", r"\g<1>-0\2", regex=True)
    i = pd.DataFrame({"sku": raw["art_no"].str.strip(), "stock_month": month,
                      "quantity_on_hand": pd.to_numeric(raw["qty_hand"], errors="coerce")})
    bad = ~i["stock_month"].str.match(r"^\d{4}-\d{2}$") | ~(i["quantity_on_hand"] >= 0) | \
          ~i["sku"].isin(products["sku"]) | i.duplicated(["sku", "stock_month"])
    if bad.any():
        raw[bad].assign(reason="bad month, bad stock, unknown article or duplicate count") \
            .to_csv(REMOVED / "inventory_invalid.csv", index=False)
    i = i[~bad].copy()
    i["quantity_on_hand"] = i["quantity_on_hand"].astype(int)
    log["inventory"] = dict(raw=len(raw), clean=len(i), removed=int(bad.sum()),
                            months_fixed=int((month != raw["stk_month"]).sum()),
                            dropped_columns="reserved_qty (empty on every row)")
    return i.sort_values(["sku", "stock_month"]).reset_index(drop=True)


def validate(o, p, i, log):
    """Checks on the clean output. Each returns (name, passed, detail)."""
    r = []
    r.append(("orders: no duplicate lines", not o.duplicated().any(), ""))
    r.append(("orders: dates are YYYY-MM-DD", o["order_date"].str.match(r"^\d{4}-\d{2}-\d{2}$").all(), ""))
    r.append(("orders: countries are 2-letter codes", o["country_code"].str.match(r"^[A-Z]{2}$").all(),
              ", ".join(sorted(o["country_code"].unique()))))
    r.append(("orders: channels lowercase, 3 known", set(o["channel"]) <= {"web", "app", "marketplace"}, ""))
    r.append(("orders: every sku in products", o["sku"].isin(p["sku"]).all(), ""))
    r.append(("orders: net + discount = gross on every line",
              (abs(o["net_revenue"] + o["discount_amount"] - o["gross_revenue"]) < 0.005).all(), ""))
    r.append(("orders: no negative revenue", (o["net_revenue"] >= 0).all(), ""))
    lo = log["orders"]
    r.append(("orders: raw = clean + removed",
              lo["raw"] == lo["clean"] + lo["removed_duplicates"] + lo["removed_invalid"],
              f"{lo['raw']:,} = {lo['clean']:,} + {lo['removed_duplicates']:,} + {lo['removed_invalid']:,}"))
    r.append(("products: 6 brands, 5 categories", p["brand"].nunique() == 6 and p["category"].nunique() == 5, ""))
    r.append(("products: sku unique", p["sku"].is_unique, ""))
    r.append(("inventory: months are YYYY-MM", i["stock_month"].str.match(r"^\d{4}-\d{2}$").all(), ""))
    r.append(("inventory: one count per article per month", not i.duplicated(["sku", "stock_month"]).any(), ""))
    li = log["inventory"]
    r.append(("inventory: raw = clean + removed", li["raw"] == li["clean"] + li["removed"], ""))
    r.append(("all columns lowercase", all(c == c.lower() for df in (o, p, i) for c in df.columns), ""))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=os.environ.get("RUN_DIR"))
    args = ap.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else ROOT / "runs" / dt.date.today().isoformat()
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    REMOVED.mkdir(parents=True, exist_ok=True)
    for old in REMOVED.glob("*.csv"):        # removed/ always reflects the latest run
        old.write_text("", encoding="utf-8")

    log = {}
    p = clean_products(log)
    o = clean_orders(p, log)
    i = clean_inventory(p, log)
    p.to_csv(CLEAN / "products.csv", index=False)
    o.to_csv(CLEAN / "orders.csv", index=False)
    i.to_csv(CLEAN / "inventory.csv", index=False)

    checks = validate(o, p, i, log)
    failed = [c for c in checks if not c[1]]
    md = [f"# Clean run", f"Run: {dt.datetime.now():%Y-%m-%d %H:%M}  ",
          f"Checks: **{'PASS' if not failed else 'FAIL'}** ({len(checks) - len(failed)}/{len(checks)})", "",
          "## What changed", ""]
    for kind, d in log.items():
        md.append(f"- **{kind}**: " + "; ".join(f"{k.replace('_', ' ')} {v:,}" if isinstance(v, int)
                                                else f"{k.replace('_', ' ')} {v}" for k, v in d.items()))
    md += ["", "Removed rows are kept in data/clean/removed/ with a reason column.", "",
           "## Checks on the clean data", "", "| check | result | detail |", "|---|---|---|"] + \
          [f"| {n} | {'PASS' if ok else 'FAIL'} | {d} |" for n, ok, d in checks]
    (run_dir / "clean.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for n, ok, d in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {n}  {d}")
    print(f"clean: orders {len(o):,}, products {len(p)}, inventory {len(i):,} -> data/clean")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
