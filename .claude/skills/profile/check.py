"""Pass/fail gate for new raw data in data/raw. Run it every time new files arrive.

Each check prints PASS or FAIL. Exit code 1 if anything fails, so the
pipeline stops before cleaning bad data.
Expected values live in baseline.json next to this file.

Run:  python .claude/skills/profile/check.py   [--run-dir runs/xyz]
"""
import argparse, datetime as dt, glob, json, os
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").exists())
RAW = ROOT / "data" / "raw"
BASE = json.loads((HERE / "baseline.json").read_text(encoding="utf-8"))


def load(kind):
    files = sorted(glob.glob(str(RAW / f"{kind}*.csv")))
    frames = [pd.read_csv(f, dtype=str, keep_default_na=False) for f in files]
    return (pd.concat(frames, ignore_index=True) if frames else None), files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=os.environ.get("RUN_DIR"))
    args = ap.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else ROOT / "runs" / dt.date.today().isoformat()
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    data = {}
    for kind in ["orders", "products", "inventory"]:
        df, files = load(kind)
        check(f"{kind}: file present", df is not None, ", ".join(Path(f).name for f in files))
        if df is None:
            continue
        check(f"{kind}: not empty", len(df) > 0, f"{len(df):,} rows")
        # every file of this kind must have the expected columns
        for f in files:
            cols = list(pd.read_csv(f, nrows=0).columns)
            exp = BASE["columns"][kind]
            check(f"{kind}: columns as expected ({Path(f).name})", cols == exp,
                  "" if cols == exp else f"got {cols}")
        data[kind] = df

    o, p, i = data.get("orders"), data.get("products"), data.get("inventory")
    if o is not None:
        iso = o["CRTD_DT"].str.match(r"^\d{4}-\d{2}-\d{2}$")
        eu = o["CRTD_DT"].str.match(r"^\d{2}/\d{2}/\d{4}$")
        d = pd.Series(pd.NaT, index=o.index, dtype="datetime64[ns]")
        d[iso] = pd.to_datetime(o["CRTD_DT"][iso], format="%Y-%m-%d", errors="coerce")
        d[eu] = pd.to_datetime(o["CRTD_DT"][eu], format="%d/%m/%Y", errors="coerce")
        check("orders: every date parses (YYYY-MM-DD or DD/MM/YYYY)", d.notna().all(), f"{d.isna().sum()} bad")
        codes = o["CTRY"].replace(BASE["country_names"])
        new = sorted(set(codes) - set(BASE["known_countries"]))
        check("orders: no unknown country", not new, ", ".join(new))
        newch = sorted(set(o["CHNL"].str.lower()) - set(BASE["known_channels"]))
        check("orders: no unknown channel", not newch, ", ".join(newch))
        q = pd.to_numeric(o["QTY"], errors="coerce")
        check("orders: quantity is a whole number > 0", (q > 0).all() and (q % 1 == 0).all())
        pr = pd.to_numeric(o["UNIT_PRC"], errors="coerce")
        check("orders: unit price is a number > 0", (pr > 0).all())
        dc = pd.to_numeric(o["DISC_PCT"], errors="coerce")
        check("orders: discount between 0 and max", dc.between(0, BASE["max_discount"]).all(),
              f"max seen {dc.max()}")
        check("orders: order number never empty", (o["ORD_NO"] != "").all())
        if p is not None:
            miss = ~o["ART_NO"].isin(p["sku"])
            check("orders: every article exists in the catalogue", not miss.any(), f"{miss.sum()} missing")
        # volume drop: latest month vs median of earlier months
        lines = d.dt.to_period("M").value_counts().sort_index()
        if len(lines) > 1:
            latest, earlier = lines.iloc[-1], lines.iloc[:-1].median()
            ratio = latest / earlier
            check("orders: no volume drop in latest month", ratio >= BASE["volume_drop_threshold"],
                  f"{lines.index[-1]}: {latest:,} lines = {ratio:.0%} of usual {earlier:,.0f}")
    if p is not None:
        check("products: sku unique", not p["sku"].duplicated().any())
        nb = sorted(set(p["brand"].str.title()) - set(BASE["brands"]))
        check("products: brands known (any casing)", not nb, ", ".join(nb))
        cats = {c.lower() for c in BASE["categories"]}
        nc = sorted(set(p["category"].str.lower()) - cats)
        check("products: categories known (any casing)", not nc, ", ".join(nc))
        lp = pd.to_numeric(p["list_price"], errors="coerce")
        check("products: list price is a number > 0", (lp > 0).all())
    if i is not None:
        check("inventory: month looks like YYYY-MM or YYYY-M", i["stk_month"].str.match(r"^\d{4}-\d{1,2}$").all())
        qh = pd.to_numeric(i["qty_hand"], errors="coerce")
        check("inventory: stock is a number >= 0", (qh >= 0).all())
        if p is not None:
            check("inventory: every article exists in the catalogue", i["art_no"].isin(p["sku"]).all())

    failed = [r for r in results if not r[1]]
    lines = [f"# Raw data check", f"Run: {dt.datetime.now():%Y-%m-%d %H:%M}  ",
             f"Result: **{'PASS' if not failed else 'FAIL'}** ({len(results) - len(failed)}/{len(results)} passed)", "",
             "| check | result | detail |", "|---|---|---|"] + \
            [f"| {n} | {'PASS' if ok else 'FAIL'} | {det} |" for n, ok, det in results]
    (run_dir / "check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for n, ok, det in results:
        print(f"{'PASS' if ok else 'FAIL'}  {n}  {det}")
    print(f"check: {len(results) - len(failed)}/{len(results)} passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
