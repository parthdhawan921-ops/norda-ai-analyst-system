"""Quality gate: turns knowledge/quality-rules.md into automatic checks.

Rule 1  Code computes, Claude understands  -> every stored number is recomputed in code
Rule 2  Two roads, one number              -> each dashboard number computed two different ways
Rule 3  Trace orders                       -> 10 random orders followed raw -> clean -> mart
Rule 4  What must always be true           -> the business facts in the rules file

Writes runs/<run>/quality.md. Exit code 1 if any check fails.
Run:  python .claude/skills/quality-gate/quality.py  [--run-dir runs/xyz] [--seed 7]
"""
import argparse, datetime as dt, glob, os, random
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").exists())
RAW, CLEAN, MART = (ROOT / "data" / x for x in ("raw", "clean", "mart"))
COUNTRY = {"Germany": "DE", "France": "FR", "Italy": "IT", "Netherlands": "NL", "Spain": "ES", "Austria": "AT"}
CENT = 0.01


def to_cent(x):
    """Same half-up rounding to the cent as the clean layer, done independently here."""
    import numpy as np
    return np.floor(x * 100 + 0.5 + 1e-7) / 100


def close(a, b, tol=CENT):
    return abs(float(a) - float(b)) <= tol


def load():
    raw = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False)
                     for f in sorted(glob.glob(str(RAW / "orders*.csv")))], ignore_index=True)
    rawinv = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False)
                        for f in sorted(glob.glob(str(RAW / "inventory*.csv")))], ignore_index=True)
    co = pd.read_csv(CLEAN / "orders.csv", dtype={"order_id": str, "customer_id": str})
    ci = pd.read_csv(CLEAN / "inventory.csv", dtype={"stock_month": str})
    cp = pd.read_csv(CLEAN / "products.csv")
    m = {n: pd.read_csv(MART / f"{n}.csv", dtype={"order_id": str, "stock_month": str, "year_month": str})
         for n in ["dim_date", "dim_product", "dim_country", "dim_channel", "fact_sales", "fact_inventory"]}
    return raw, rawinv, co, ci, cp, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=os.environ.get("RUN_DIR"))
    ap.add_argument("--seed", type=int, default=None, help="fix the random order sample")
    args = ap.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else ROOT / "runs" / dt.date.today().isoformat()
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    raw, rawinv, co, ci, cp, m = load()
    fs, fi, dd, dp, dc, dch = (m[k] for k in ["fact_sales", "fact_inventory", "dim_date", "dim_product",
                                               "dim_country", "dim_channel"])
    sales = fs.merge(dd[["date_key", "year", "year_month"]], left_on="order_date_key", right_on="date_key") \
              .merge(dp[["product_key", "sku", "category"]], on="product_key") \
              .merge(dc[["country_key", "country_code"]], on="country_key") \
              .merge(dch, on="channel_key")
    results = []

    def check(rule, name, ok, detail=""):
        results.append((rule, name, bool(ok), detail))

    # ---------------- Rule 1: code computes ----------------
    R = "1 Code computes"
    gross = fs["quantity"] * fs["unit_price"]
    check(R, "gross_revenue = quantity x unit_price on every line", ((gross - fs["gross_revenue"]).abs() <= CENT).all())
    net = gross * (1 - fs["discount_rate"])
    check(R, "net_revenue = qty x price x (1 - discount) on every line (metrics.md)",
          ((net - fs["net_revenue"]).abs() <= CENT).all())
    check(R, "discount_amount = gross - net on every line",
          ((fs["gross_revenue"] - fs["net_revenue"] - fs["discount_amount"]).abs() <= CENT).all())
    lit = (fs["quantity"] * fs["unit_price"] * fs["discount_rate"]).sum()
    unrounded = net.sum()
    drift = abs(unrounded - fs["net_revenue"].sum()) + abs(lit - fs["discount_amount"].sum())
    check(R, "cent rounding per line moves the year by < 0.001% of revenue",
          drift < 0.00001 * fs["net_revenue"].sum(),
          f"revenue unrounded {unrounded:,.2f} vs stored {fs['net_revenue'].sum():,.2f}; "
          f"discount literal {lit:,.2f} vs stored {fs['discount_amount'].sum():,.2f}")
    check(R, "quantity is a whole number >= 1", (fs["quantity"] >= 1).all() and (fs["quantity"] % 1 == 0).all())
    check(R, "discount_rate between 0 and 0.5", fs["discount_rate"].between(0, 0.5).all())
    check(R, "unit_price > 0", (fs["unit_price"] > 0).all())
    check(R, "stock never negative", (fi["quantity_on_hand"] >= 0).all())
    check(R, "every fact key finds its dimension",
          fs["order_date_key"].isin(dd["date_key"]).all() and fs["product_key"].isin(dp["product_key"]).all()
          and fs["country_key"].isin(dc["country_key"]).all() and fs["channel_key"].isin(dch["channel_key"]).all()
          and fi["snapshot_date_key"].isin(dd["date_key"]).all() and fi["product_key"].isin(dp["product_key"]).all())
    check(R, "dimension keys unique", all(d[k].is_unique for d, k in
          [(dd, "date_key"), (dp, "product_key"), (dc, "country_key"), (dch, "channel_key")]))
    check(R, "inventory: one snapshot per article per month", not fi.duplicated(["product_key", "stock_month"]).any())
    check(R, "raw lines = clean lines + removed lines",
          len(raw) == len(co) + sum(len(pd.read_csv(f)) for f in (CLEAN / "removed").glob("orders_*.csv")
                                    if os.path.getsize(f) > 0),
          f"raw {len(raw):,}, clean {len(co):,}")
    check(R, "clean lines = fact_sales lines", len(co) == len(fs), f"{len(fs):,}")
    check(R, "clean inventory = fact_inventory rows", len(ci) == len(fi), f"{len(fi):,}")

    # ---------------- Rule 2: two roads, one number ----------------
    R = "2 Two roads"
    rev_a = fs["net_revenue"].sum()
    rev_b = to_cent(co["quantity"] * co["unit_price"] * (1 - co["discount_rate"])).sum()
    check(R, "Revenue: sum of mart net_revenue vs recomputed from clean columns", close(rev_a, rev_b),
          f"{rev_a:,.2f} vs {rev_b:,.2f}")
    # independent road from RAW: dedupe raw, fix countries/dates in a different way, recompute
    r = raw.copy()
    r["d"] = pd.to_datetime(r["CRTD_DT"].where(r["CRTD_DT"].str.contains("-"),
                            r["CRTD_DT"].str[6:10] + "-" + r["CRTD_DT"].str[3:5] + "-" + r["CRTD_DT"].str[0:2]))
    r["c"] = r["CTRY"].map(lambda x: COUNTRY.get(x, x))
    r = r.drop(columns=["CRTD_DT", "CTRY"]).drop_duplicates()
    r_rev = to_cent(r["QTY"].astype(float) * r["UNIT_PRC"].astype(float) * (1 - r["DISC_PCT"].astype(float)))
    check(R, "Revenue: mart vs straight from raw (own dedupe)", close(rev_a, r_rev.sum()),
          f"{rev_a:,.2f} vs {r_rev.sum():,.2f}")
    ord_a = fs["order_id"].nunique()
    ord_b = len(co.groupby("order_id").size())
    ord_c = r["ORD_NO"].nunique()
    check(R, "Orders: distinct count vs group-by count vs raw", ord_a == ord_b == ord_c, f"{ord_a:,} / {ord_b:,} / {ord_c:,}")
    check(R, "Units: sum in mart vs sum in raw (deduped)", fs["quantity"].sum() == r["QTY"].astype(int).sum(),
          f"{fs['quantity'].sum():,}")
    by_month = sales.groupby("year_month")["net_revenue"].sum()
    check(R, "Revenue: sum of months = total", close(by_month.sum(), rev_a), "")
    check(R, "Revenue: sum of countries = total", close(sales.groupby("country_code")["net_revenue"].sum().sum(), rev_a))
    check(R, "Revenue: sum of channels = total", close(sales.groupby("channel_name")["net_revenue"].sum().sum(), rev_a))
    check(R, "Revenue: sum of categories = total", close(sales.groupby("category")["net_revenue"].sum().sum(), rev_a))
    m_raw = r.assign(rev=r_rev).groupby(r["d"].dt.strftime("%Y-%m"))["rev"].sum()
    worst = (by_month - m_raw.reindex(by_month.index)).abs().max()
    check(R, "Revenue per month: mart (via dim_date) vs raw (via parsed dates)", worst <= CENT, f"max gap {worst:,.4f}")
    last_m = fi["stock_month"].max()
    s_a = fi.loc[fi["stock_month"] == last_m, "quantity_on_hand"].sum()
    s_b = ci.loc[ci["stock_month"] == last_m, "quantity_on_hand"].sum()
    rim = rawinv["stk_month"].str.replace(r"^(\d{4})-(\d)$", r"\g<1>-0\2", regex=True)
    s_c = rawinv.loc[rim == last_m, "qty_hand"].astype(int).sum()
    check(R, f"Stock on hand {last_m}: mart vs clean vs raw", s_a == s_b == s_c, f"{s_a:,} / {s_b:,} / {s_c:,}")
    top_a = sales.groupby("sku")["net_revenue"].sum().idxmax()
    top_b = co.assign(v=co["quantity"] * co["unit_price"] * (1 - co["discount_rate"])).groupby("sku")["v"].sum().idxmax()
    check(R, "Best-selling product: mart vs clean agree", top_a == top_b, top_a)
    zero_a = set(fi.loc[(fi["stock_month"] == last_m) & (fi["quantity_on_hand"] == 0), "product_key"].map(
        dp.set_index("product_key")["sku"]))
    zero_b = set(ci.loc[(ci["stock_month"] == last_m) & (ci["quantity_on_hand"] == 0), "sku"])
    check(R, f"Products out of stock at {last_m}: mart vs clean agree", zero_a == zero_b, f"{len(zero_a)} products")

    # ---------------- Rule 3: trace 10 random orders ----------------
    R = "3 Trace orders"
    seed = args.seed if args.seed is not None else random.randrange(10**6)
    sample = random.Random(seed).sample(sorted(fs["order_id"].unique()), 10)
    for oid in sample:
        rl = r[r["ORD_NO"] == oid]
        cl = co[co["order_id"] == oid]
        ml = sales[sales["order_id"] == oid]
        ok = (len(rl) == len(cl) == len(ml)
              and sorted(rl["ART_NO"]) == sorted(cl["sku"]) == sorted(ml["sku"])
              and rl["QTY"].astype(int).sum() == cl["quantity"].sum() == ml["quantity"].sum()
              and close(to_cent(rl["QTY"].astype(float) * rl["UNIT_PRC"].astype(float)
                                * (1 - rl["DISC_PCT"].astype(float))).sum(), ml["net_revenue"].sum())
              and set(rl["c"]) == set(cl["country_code"]) == set(ml["country_code"])
              and set(rl["d"].dt.strftime("%Y-%m-%d")) == set(cl["order_date"]))
        check(R, f"order {oid}: raw -> clean -> mart match", ok,
              f"{len(ml)} lines, {ml['quantity'].sum()} units, EUR {ml['net_revenue'].sum():,.2f}, "
              f"{', '.join(sorted(set(ml['country_code'])))}")
    check(R, "sample seed recorded (rerun with --seed to repeat)", True, f"seed {seed}")

    # ---------------- Rule 4: what must always be true ----------------
    R = "4 Always true"
    months_all = pd.period_range(sales["year_month"].min(), sales["year_month"].max(), freq="M").astype(str)
    empty = [mth for mth in months_all if by_month.get(mth, 0) <= 0]
    check(R, "every month has sales", not empty, ", ".join(empty) or f"{len(months_all)} months")
    files = list(CLEAN.glob("*.csv")) + list(MART.glob("*.csv"))
    empties = [f.name for f in files if len(pd.read_csv(f)) == 0]
    check(R, "no empty files in clean or mart", not empties, ", ".join(empties) or f"{len(files)} files")
    check(R, "no revenue is negative", (fs["net_revenue"] >= 0).all())
    y25 = sales[sales["year"] == 2025].groupby("year_month")["net_revenue"].sum()
    check(R, "December is the biggest month of 2025 by revenue", y25.idxmax() == "2025-12",
          f"biggest {y25.idxmax()} EUR {y25.max():,.2f}")

    # ---------------- report ----------------
    failed = [x for x in results if not x[2]]
    md = ["# Quality gate", f"Run: {dt.datetime.now():%Y-%m-%d %H:%M}  ",
          f"Result: **{'PASS' if not failed else 'FAIL'}** ({len(results) - len(failed)}/{len(results)} checks)", "",
          "| rule | checks | passed |", "|---|---:|---:|"]
    for rule in sorted({x[0] for x in results}):
        rs = [x for x in results if x[0] == rule]
        md.append(f"| {rule} | {len(rs)} | {sum(x[2] for x in rs)} |")
    md += ["", "## Key numbers (computed in code)", "",
           f"- Revenue: EUR {rev_a:,.2f} (before returns)", f"- Orders: {ord_a:,}",
           f"- Units sold: {fs['quantity'].sum():,}", f"- Stock on hand {last_m}: {s_a:,} units", "",
           "## All checks", "", "| rule | check | result | detail |", "|---|---|---|---|"] + \
          [f"| {a} | {b} | {'PASS' if c else 'FAIL'} | {d} |" for a, b, c, d in results]
    (run_dir / "quality.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for a, b, c, d in results:
        print(f"{'PASS' if c else 'FAIL'}  [{a}] {b}  {d}")
    print(f"quality: {len(results) - len(failed)}/{len(results)} passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
