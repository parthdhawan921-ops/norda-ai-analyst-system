"""Profile the raw shop export in data/raw.

What it does (in plain words):
  1. Loads every orders*/products*/inventory* CSV in data/raw as text,
     so nothing is silently converted.
  2. Describes every column: empty cells, distinct values, examples.
  3. Hunts for the known kinds of problems: mixed date formats, country
     names mixed with codes, mixed casing, duplicate rows, bad month
     formats, empty columns, prices that differ from the catalogue.
  4. Writes the findings to runs/<run>/profile.md and the table
     descriptions to knowledge/metadata.md.

Run:  python .claude/skills/profile/profile.py   [--run-dir runs/xyz]
"""
import argparse, datetime as dt, glob, os, re
from pathlib import Path
import pandas as pd


def project_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    raise SystemExit("Could not find the project root (CLAUDE.md)")


ROOT = project_root()
RAW = ROOT / "data" / "raw"
OFFICIAL_MARKETS = {"DE", "FR", "IT", "NL"}          # knowledge/company.md
COUNTRY_NAMES = {"Germany": "DE", "France": "FR", "Italy": "IT",
                 "Netherlands": "NL", "Spain": "ES", "Austria": "AT"}

# Column descriptions: source dictionary (shop-export-dictionary.pdf) + what the profile showed
DESCRIPTIONS = {
    "orders": {
        "ORD_NO": "Order number. Repeats on every line of the same order. (dictionary: order_ref, renamed)",
        "CRTD_DT": "Day the customer placed the order. Two formats mixed: YYYY-MM-DD and DD/MM/YYYY. (dictionary: order_date, renamed)",
        "CHNL": "Sales channel: web, app, marketplace. Not in the dictionary.",
        "CTRY": "Delivery country. Mix of ISO codes (DE) and full names (Germany). (dictionary: country)",
        "CUST_REF": "Customer id. Often empty, mostly on marketplace orders. Not in the dictionary.",
        "ART_NO": "Article number, joins to products.sku. (dictionary: article_no, renamed)",
        "QTY": "Units of the article on this line. (dictionary: quantity)",
        "UNIT_PRC": "Price of one unit at order time, in EUR, BEFORE discount. (dictionary: unit_price)",
        "DISC_PCT": "Discount as a fraction (0.15 = 15%), not yet subtracted from the price. Not in the dictionary.",
    },
    "products": {
        "sku": "Article number. One row per article.",
        "product_name": "Display name of the article.",
        "brand": "Brand. 6 real brands written in mixed casing.",
        "category": "Category. 5 real categories written in mixed casing.",
        "list_price": "Catalogue price in EUR. Undated snapshot, often differs from the price actually paid.",
    },
    "inventory": {
        "art_no": "Article number, joins to products.sku.",
        "stk_month": "Month of the stock count, YYYY-MM (a few rows use YYYY-M).",
        "qty_hand": "Units in the warehouse at month end.",
        "reserved_qty": "Reserved units. Empty on every row.",
    },
}


def load(kind):
    files = sorted(glob.glob(str(RAW / f"{kind}*.csv")))
    if not files:
        return None, []
    frames = [pd.read_csv(f, dtype=str, keep_default_na=False) for f in files]
    return pd.concat(frames, ignore_index=True), [Path(f).name for f in files]


def date_pattern(v):
    return re.sub(r"\d", "9", v)


def parse_dates(s):
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    iso = s.str.match(r"^\d{4}-\d{2}-\d{2}$")
    eu = s.str.match(r"^\d{2}/\d{2}/\d{4}$")
    out[iso] = pd.to_datetime(s[iso], format="%Y-%m-%d", errors="coerce")
    out[eu] = pd.to_datetime(s[eu], format="%d/%m/%Y", errors="coerce")
    return out


def column_table(df):
    rows = ["| column | empty | distinct | examples |", "|---|---:|---:|---|"]
    for c in df.columns:
        ex = ", ".join(df[c][df[c] != ""].astype(str).drop_duplicates().head(4))
        rows.append(f"| {c} | {(df[c] == '').sum():,} | {df[c].nunique():,} | {ex} |")
    return "\n".join(rows)


def casing_variants(s):
    groups = s.groupby(s.str.lower()).unique()
    return {k: sorted(v) for k, v in groups.items() if len(v) > 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=os.environ.get("RUN_DIR"))
    ap.add_argument("--no-metadata", action="store_true")
    args = ap.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else ROOT / "runs" / dt.date.today().isoformat()
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    orders, of = load("orders")
    products, pf = load("products")
    inventory, inf = load("inventory")
    findings = []   # (id, severity, text)

    def add(fid, sev, text):
        findings.append((fid, sev, text))

    out = [f"# Profile of data/raw", f"Run: {dt.datetime.now():%Y-%m-%d %H:%M}  ",
           f"Files: {', '.join(of + pf + inf)}", ""]

    # ---------- orders ----------
    if orders is not None:
        out += ["## orders", f"{len(orders):,} rows, {orders.shape[1]} columns, "
                f"{orders['ORD_NO'].nunique():,} distinct orders", "", column_table(orders), ""]
        pats = orders["CRTD_DT"].map(date_pattern).value_counts()
        if len(pats) > 1:
            add("O-01", "high", "Mixed date formats in CRTD_DT: " +
                ", ".join(f"`{p}` {n:,}" for p, n in pats.items()) +
                ". The slash form is DD/MM/YYYY (day values above 12 appear in first position).")
        d = parse_dates(orders["CRTD_DT"])
        if d.isna().any():
            add("O-02", "high", f"{d.isna().sum():,} order dates could not be parsed.")
        out += [f"Order dates run from {d.min():%Y-%m-%d} to {d.max():%Y-%m-%d}.", ""]
        names = orders["CTRY"][orders["CTRY"].isin(COUNTRY_NAMES)]
        if len(names):
            add("O-03", "high", f"CTRY mixes ISO codes and full names: {len(names):,} rows use names "
                f"({', '.join(sorted(names.unique()))}).")
        codes = set(orders["CTRY"].replace(COUNTRY_NAMES))
        extra = sorted(codes - OFFICIAL_MARKETS)
        if extra:
            add("O-04", "med", f"Countries in the data that the company overview does not list as markets: "
                f"{', '.join(extra)}. A documentation gap or new markets: ask the business.")
        dups = orders.duplicated()
        if dups.any():
            add("O-05", "high", f"{dups.sum():,} rows are exact copies of another row "
                f"({dups.sum() / len(orders):.2%} of lines). They would double count revenue.")
        for c in ["QTY", "UNIT_PRC", "DISC_PCT"]:
            n = pd.to_numeric(orders[c], errors="coerce")
            bad = n.isna().sum()
            out.append(f"- {c}: min {n.min()}, max {n.max()}, non-numeric {bad:,}")
            if bad:
                add("O-06", "high", f"{bad:,} non-numeric values in {c}.")
        q = pd.to_numeric(orders["QTY"], errors="coerce")
        if (q <= 0).any():
            add("O-07", "high", f"{(q <= 0).sum():,} lines with zero or negative quantity.")
        disc = pd.to_numeric(orders["DISC_PCT"], errors="coerce")
        if ((disc < 0) | (disc > 1)).any():
            add("O-08", "high", "Discounts outside 0-1.")
        out.append("")
        empty_cust = orders["CUST_REF"] == ""
        by_ch = empty_cust.groupby(orders["CHNL"]).mean()
        add("O-09", "info", "CUST_REF is empty on " + ", ".join(f"{k} {v:.0%}" for k, v in by_ch.items()) +
            ". Expected for marketplace (the platform owns the customer); not a defect.")
        if products is not None:
            missing = ~orders["ART_NO"].isin(products["sku"])
            if missing.any():
                add("O-10", "high", f"{missing.sum():,} order lines point to articles not in the catalogue.")
            m = orders.merge(products[["sku", "list_price"]], left_on="ART_NO", right_on="sku", how="left")
            diff = (pd.to_numeric(m["UNIT_PRC"]) - pd.to_numeric(m["list_price"])).abs() > 0.005
            add("P-02", "med", f"UNIT_PRC differs from catalogue list_price on {diff.sum():,} lines "
                f"({diff.mean():.0%}). Use UNIT_PRC (price actually paid); list_price is reference only.")
        add("O-11", "info", "Column names differ from the source dictionary (ORD_NO vs order_ref, CRTD_DT vs "
            "order_date, ART_NO vs article_no) and CHNL, CUST_REF, DISC_PCT are not documented.")
        months = d.dt.to_period("M").value_counts().sort_index()
        out += ["Lines per month:", "", "| month | lines |", "|---|---:|"] + \
               [f"| {k} | {v:,} |" for k, v in months.items()] + [""]

    # ---------- products ----------
    if products is not None:
        out += ["## products", f"{len(products):,} rows, {products.shape[1]} columns", "",
                column_table(products), ""]
        for c in ["brand", "category"]:
            v = casing_variants(products[c])
            if v:
                add("P-01", "high", f"{c} is written in {products[c].nunique()} spellings for "
                    f"{products[c].str.lower().nunique()} real values (mixed casing), e.g. "
                    + "; ".join("/".join(x) for x in list(v.values())[:2]) + ".")
        if products["sku"].duplicated().any():
            add("P-03", "high", f"{products['sku'].duplicated().sum()} duplicate skus in the catalogue.")
        if orders is not None:
            never = sorted(set(products["sku"]) - set(orders["ART_NO"]))
            if never:
                add("P-04", "info", f"{len(never)} catalogue articles never ordered: {', '.join(never)}.")

    # ---------- inventory ----------
    if inventory is not None:
        out += ["## inventory", f"{len(inventory):,} rows, {inventory.shape[1]} columns", "",
                column_table(inventory), ""]
        bad_month = ~inventory["stk_month"].str.match(r"^\d{4}-\d{2}$")
        if bad_month.any():
            add("I-01", "med", f"{bad_month.sum()} stock months written without the leading zero "
                f"({', '.join(sorted(inventory['stk_month'][bad_month].unique()))}).")
        for c in inventory.columns:
            if (inventory[c] == "").all():
                add("I-02", "low", f"Column {c} is empty on all {len(inventory):,} rows.")
        qh = pd.to_numeric(inventory["qty_hand"], errors="coerce")
        if (qh < 0).any():
            add("I-03", "high", f"{(qh < 0).sum()} negative stock counts.")
        add("I-04", "info", f"{(qh == 0).sum()} article-months with zero stock (possible stock-outs).")
        norm = inventory["stk_month"].str.replace(r"^(\d{4})-(\d)$", r"\g<1>-0\2", regex=True)
        if pd.DataFrame({"a": inventory["art_no"], "m": norm}).duplicated().any():
            add("I-05", "high", "Duplicate article-month stock counts after fixing month format.")
        if products is not None:
            nostock = sorted(set(products["sku"]) - set(inventory["art_no"]))
            if nostock:
                add("I-06", "info", f"{len(nostock)} catalogue articles never stocked: {', '.join(nostock)}.")

    order_ = {"high": 0, "med": 1, "low": 2, "info": 3}
    findings.sort(key=lambda f: (order_[f[1]], f[0]))
    head = ["## Data quality findings", "", "| id | severity | finding |", "|---|---|---|"] + \
           [f"| {i} | {s} | {t} |" for i, s, t in findings] + [""]
    report = out[:4] + head + out[4:]
    (run_dir / "profile.md").write_text("\n".join(report), encoding="utf-8")
    print(f"profile: {len(findings)} findings -> {run_dir / 'profile.md'}")

    if not args.no_metadata:
        write_metadata(orders, products, inventory, of, pf, inf)


def write_metadata(orders, products, inventory, of, pf, inf):
    lines = ["# Metadata: the raw shop export",
             "Generated by .claude/skills/profile/profile.py from data/raw plus "
             "knowledge/inbox/shop-export-dictionary.pdf. Rerun /profile to refresh.", ""]
    for kind, df, files in [("orders", orders, of), ("products", products, pf), ("inventory", inventory, inf)]:
        if df is None:
            continue
        lines += [f"## {kind}", f"Files: {', '.join(files)}. {len(df):,} rows, {df.shape[1]} columns.", "",
                  "| raw column | clean name | type | description |", "|---|---|---|---|"]
        for c in df.columns:
            lines.append(f"| {c} | {CLEAN_NAMES[kind].get(c, '(dropped)')} | {TYPES[kind].get(c, 'text')} | "
                         f"{DESCRIPTIONS[kind].get(c, 'Not documented yet.')} |")
        lines.append("")
    lines += ["## Grain", "- orders: one row per order line (one article on one order).",
              "- products: one row per article.", "- inventory: one row per article per month-end count.", "",
              "## Open questions for the business",
              "- Spain (ES) and Austria (AT) are in the orders but not in the company overview. New markets?",
              "- Revenue is before returns: returns live in another system.", ""]
    (ROOT / "knowledge" / "metadata.md").write_text("\n".join(lines), encoding="utf-8")
    print("profile: knowledge/metadata.md written")


CLEAN_NAMES = {
    "orders": {"ORD_NO": "order_id", "CRTD_DT": "order_date", "CHNL": "channel", "CTRY": "country_code",
               "CUST_REF": "customer_id", "ART_NO": "sku", "QTY": "quantity", "UNIT_PRC": "unit_price",
               "DISC_PCT": "discount_rate"},
    "products": {"sku": "sku", "product_name": "product_name", "brand": "brand", "category": "category",
                 "list_price": "list_price"},
    "inventory": {"art_no": "sku", "stk_month": "stock_month", "qty_hand": "quantity_on_hand"},
}
TYPES = {
    "orders": {"CRTD_DT": "date", "QTY": "integer", "UNIT_PRC": "decimal (EUR)", "DISC_PCT": "decimal 0-1"},
    "products": {"list_price": "decimal (EUR)"},
    "inventory": {"stk_month": "year-month", "qty_hand": "integer", "reserved_qty": "integer (empty)"},
}

if __name__ == "__main__":
    main()
