"""Build the interactive sales dashboard from data/mart (and only from data/mart).

Output: one self-contained HTML file (no internet, no libraries) with the
order lines packed inside it, so every filter gives exact numbers:
distinct orders stay distinct, stock stays a month-end snapshot.

Requirements: knowledge/inbox/dashboard-requirements.pdf
Metrics:      knowledge/metrics.md

Run:  python .claude/skills/dashboard/dashboard.py  [--out reports/html/dashboard.html]
"""
import argparse, base64, datetime as dt, json, os
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").exists())
MART = ROOT / "data" / "mart"


def b64(arr):
    return base64.b64encode(np.ascontiguousarray(arr).tobytes()).decode("ascii")


def build_payload():
    fs = pd.read_csv(MART / "fact_sales.csv", dtype={"order_id": str})
    fi = pd.read_csv(MART / "fact_inventory.csv", dtype={"stock_month": str})
    dd = pd.read_csv(MART / "dim_date.csv", dtype={"year_month": str})
    dp = pd.read_csv(MART / "dim_product.csv")
    dc = pd.read_csv(MART / "dim_country.csv")
    dch = pd.read_csv(MART / "dim_channel.csv")

    ym = dd.set_index("date_key")["year_month"]
    fs["ym"] = fs["order_date_key"].map(ym)
    months = sorted(set(fs["ym"]) | set(fi["stock_month"]))
    m_idx = {m: i for i, m in enumerate(months)}
    p_idx = {k: i for i, k in enumerate(dp["product_key"])}
    c_idx = {k: i for i, k in enumerate(dc["country_key"])}
    ch_idx = {k: i for i, k in enumerate(dch["channel_key"])}
    cats = sorted(dp["category"].unique())

    orders = fs.drop_duplicates("order_id")[["order_id", "ym", "country_key", "channel_key"]].reset_index(drop=True)
    o_idx = pd.Series(range(len(orders)), index=orders["order_id"])
    stock = np.full((len(dp), len(months)), -1, dtype=np.int32)   # -1 = no count that month
    for r in fi.itertuples(index=False):
        stock[p_idx[r.product_key], m_idx[r.stock_month]] = r.quantity_on_hand

    return {
        "built": f"{dt.datetime.now():%Y-%m-%d %H:%M}",
        "months": months,
        "categories": cats,
        "products": [[r.product_name, cats.index(r.category), r.brand, r.sku] for r in dp.itertuples(index=False)],
        "countries": [[r.country_name, r.country_code, r.in_company_overview == "Yes"] for r in dc.itertuples(index=False)],
        "channels": list(dch["channel_name"]),
        "nOrders": len(orders), "nLines": len(fs),
        "o_month": b64(orders["ym"].map(m_idx).to_numpy(np.uint8)),
        "o_country": b64(orders["country_key"].map(c_idx).to_numpy(np.uint8)),
        "o_channel": b64(orders["channel_key"].map(ch_idx).to_numpy(np.uint8)),
        "l_order": b64(fs["order_id"].map(o_idx).to_numpy(np.uint32)),
        "l_product": b64(fs["product_key"].map(p_idx).to_numpy(np.uint16)),
        "l_qty": b64(fs["quantity"].to_numpy(np.uint16)),
        "l_rev": b64(np.rint(fs["net_revenue"].to_numpy() * 100).astype(np.uint32)),   # cents
        "stock": b64(stock.ravel()),
        "check": {"revenue_cents": int(np.rint(fs["net_revenue"].to_numpy() * 100).sum()),
                  "orders": int(fs["order_id"].nunique()), "units": int(fs["quantity"].sum())},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.environ.get("DASHBOARD_OUT", str(ROOT / "reports" / "html" / "dashboard.html")))
    args = ap.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    html = (HERE / "template.html").read_text(encoding="utf-8").replace("__DATA__", json.dumps(payload))
    out.write_text(html, encoding="utf-8")
    print(f"dashboard: {payload['nLines']:,} lines, {payload['nOrders']:,} orders, "
          f"{len(payload['months'])} months -> {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
