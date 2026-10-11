"""Write the Power BI semantic model (TMDL) for the mart, as code.

Does what the course's Power BI lesson asks, every time the same way:
  - one table per mart CSV, loaded from data/mart (Power Query)
  - relationships exactly like the mart: dimension 1 -> fact many, facts never linked
  - a description on every table, column and measure
  - keys hidden (plus month_num, which only sorts month_name)
  - one DAX measure per metric in knowledge/metrics.md, description says which line
  - euro format on money, whole numbers on counts, all measures in folder 'metrics'
The report pages are NOT built here: you build those in Power BI Desktop,
using reports/html/dashboard.html as the mock-up.

Run:  python .claude/skills/powerbi/build_pbi.py
Then open reports/powerbi/ai-analysis.pbip in Power BI Desktop and click Refresh.
"""
import json, os, uuid
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").exists())
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
MODEL = ROOT / CFG["project"]
MART = ROOT / "data" / "mart"
MART_PATH = str(MART) if os.name == "nt" else CFG["mart_path_windows"]
EURO = r"\€#,0.00;-\€#,0.00;\€#,0.00"
NS = uuid.UUID("6f0d2a9e-3b1c-4c55-9d0e-7a1b2c3d4e5f")
tag = lambda *parts: str(uuid.uuid5(NS, "/".join(parts)))

TABLES = {
    "dim_date": ("DIMENSION. One row per calendar day. Both facts join here, so one date or month slicer "
                 "drives sales and stock together. Use year_month for the month slicer: stock exists only on month ends.", {
        "date_key": "Surrogate key YYYYMMDD, e.g. 20251231. Joins to both facts.",
        "date": "The calendar day. The model is marked as a date table on this column.",
        "year": "Calendar year.", "quarter": "Calendar quarter 1-4.",
        "month_num": "Month number 1-12. Only sorts month_name.",
        "month_name": "Month name, sorted by month_num so the axis reads January to December.",
        "year_month": "Month as YYYY-MM. Use this as the month slicer.",
        "day_of_month": "Day of the month 1-31.",
        "is_month_end": "1 on the last day of each month (the only days with stock), else 0."}),
    "dim_product": ("DIMENSION. One row per article in the whole catalogue (also articles never sold). "
                    "Brand and category are cleaned to 6 brands and 5 categories (knowledge/company.md).", {
        "product_key": "Surrogate key from the sorted sku, stable across rebuilds. Joins to both facts.",
        "sku": "Article number, e.g. KA-10999. Same as ART_NO in the raw export.",
        "product_name": "Display name of the article.",
        "brand": "Brand: Kaivo, Kova, Nodo, Ondia, Pavo, Visna.",
        "category": "Category: Accessories, Audio, Computers, Monitors, Phones & Tablets.",
        "list_price": "REFERENCE ONLY. Undated catalogue price; differs from the price paid on many orders. Use fact_sales[unit_price]."}),
    "dim_country": ("DIMENSION. One row per delivery country. Spain and Austria are in the orders but not in the company overview.", {
        "country_key": "Surrogate key. Joins to fact_sales.",
        "country_code": "ISO code. Cleaned: the raw export mixed codes (DE) and names (Germany).",
        "country_name": "Country name. Use on slicers and axes.",
        "in_company_overview": "Yes if norda-overview.pdf lists the country as a market (DE, FR, IT, NL), else No."}),
    "dim_channel": ("DIMENSION. One row per sales channel: web, app, marketplace.", {
        "channel_key": "Surrogate key. Joins to fact_sales.",
        "channel_name": "web = own shop, app = NORDA app, marketplace = third-party platforms (no customer details)."}),
    "fact_sales": ("FACT. One row per order line (one article on one order), before returns. "
                   "Count orders with the Orders measure, never with a row count. Duplicates were removed in data/clean.", {
        "order_date_key": "Key to dim_date: the day the order was placed.",
        "product_key": "Key to dim_product.", "country_key": "Key to dim_country (delivery country).",
        "channel_key": "Key to dim_channel.",
        "order_id": "Order number. Repeats on every line of the same order.",
        "quantity": "Units of this article on this line.",
        "unit_price": "Price of one unit at order time, before discount. The price actually charged.",
        "discount_rate": "Discount as a fraction (0.15 = 15%). Not yet taken off unit_price.",
        "gross_revenue": "quantity x unit_price, before discount. Reference only.",
        "discount_amount": "gross_revenue - net_revenue, so gross = net + discount on every line.",
        "net_revenue": "quantity x unit_price x (1 - discount_rate), rounded to the cent. What Revenue sums."}),
    "fact_inventory": ("FACT. One row per article per month end: units in the one warehouse. SEMI-ADDITIVE: adds across "
                       "articles, never across months; use the Stock on Hand measure. No country or channel: stock does not move with those filters.", {
        "snapshot_date_key": "Key to dim_date: always the last day of the month.",
        "product_key": "Key to dim_product.",
        "stock_month": "The month of the count, YYYY-MM. Slice by dim_date[year_month] instead.",
        "quantity_on_hand": "Units in the warehouse at month end. Do not sum across months."}),
}
MONEY = {"unit_price", "gross_revenue", "discount_amount", "net_revenue", "list_price"}
COUNTS_SUM = {"quantity", "quantity_on_hand"}
RELATIONSHIPS = [("fact_sales", "order_date_key", "dim_date", "date_key"),
                 ("fact_sales", "product_key", "dim_product", "product_key"),
                 ("fact_sales", "country_key", "dim_country", "country_key"),
                 ("fact_sales", "channel_key", "dim_channel", "channel_key"),
                 ("fact_inventory", "snapshot_date_key", "dim_date", "date_key"),
                 ("fact_inventory", "product_key", "dim_product", "product_key")]
# measure name -> (metric heading in metrics.md, DAX, format, extra note)
MEASURES = [
    ("Revenue", "Revenue", "SUM(fact_sales[net_revenue])", EURO,
     "Sums the per-line net_revenue. Before returns: returns are in a separate system."),
    ("Discount Amount", "Discount amount", "SUM(fact_sales[discount_amount])", EURO,
     "Sums per-line discount_amount (gross - net), so Revenue + Discount Amount = gross to the cent."),
    ("Orders", "Orders", "DISTINCTCOUNT(fact_sales[order_id])", "#,0",
     "The fact is at order-LINE grain, so a row count would answer a different question."),
    ("Units Sold", "Units sold", "SUM(fact_sales[quantity])", "#,0", ""),
    ("Stock on Hand", "Stock on hand", "CALCULATE(SUM(fact_inventory[quantity_on_hand]), LASTDATE(dim_date[date]))", "#,0",
     "Stock is a month-end snapshot: LASTDATE takes the latest day in the filter, so a month or the year shows the "
     "last month end, never twelve month ends added up. Blank if the filter holds no month end."),
]


def doc(text, indent):
    """TMDL description: /// lines, wrapped at about 100 characters."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 96:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    return "".join(f"{indent}/// {l}\n" for l in lines)


def col_type(name, series):
    if name == "date":
        return "dateTime", "type date"
    if pd.api.types.is_integer_dtype(series):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(series):
        return "double", "type number"
    return "string", "type text"


def metric_lines():
    lines = (ROOT / "knowledge" / "metrics.md").read_text(encoding="utf-8").splitlines()
    found = {}
    for i, l in enumerate(lines):
        if l.strip() and i + 1 < len(lines) and lines[i + 1].strip():
            found.setdefault(l.strip().lower(), (i + 2, lines[i + 1].strip()))   # 1-based line of the definition
    return found


def table_tmdl(name):
    desc, cols = TABLES[name]
    df = pd.read_csv(MART / f"{name}.csv", nrows=200)
    if list(df.columns) != list(cols):
        raise SystemExit(f"powerbi: {name} columns changed in the mart: {list(df.columns)}. Update TABLES first.")
    out = doc(desc, "") + f"table {name}\n"
    if name == "dim_date":
        out += "\tdataCategory: Time\n"
    out += f"\tlineageTag: {tag(name)}\n\n"
    m_types = []
    for c in df.columns:
        dtype, mtype = col_type(c, df[c])
        m_types.append(f'{{"{c}", {mtype}}}')
        hidden = c.endswith("_key") or c == "month_num"
        fmt = EURO if c in MONEY else ("0%" if c == "discount_rate" else
              ("yyyy-mm-dd" if c == "date" else ("#,0" if c in COUNTS_SUM else ("0" if dtype == "int64" else None))))
        out += doc(cols[c] + (" Hidden: plumbing." if hidden and c.endswith("_key") else (" Hidden." if hidden else "")), "\t")
        out += f"\tcolumn {c}\n\t\tdataType: {dtype}\n"
        if hidden:
            out += "\t\tisHidden\n"
        if c == "date":
            out += "\t\tisKey\n"
        if fmt:
            out += f"\t\tformatString: {fmt}\n"
        out += f"\t\tlineageTag: {tag(name, c)}\n"
        out += f"\t\tsummarizeBy: {'sum' if c in COUNTS_SUM or c in {'gross_revenue', 'discount_amount', 'net_revenue'} else 'none'}\n"
        if c == "month_name":
            out += "\t\tsortByColumn: month_num\n"
        out += f"\t\tsourceColumn: {c}\n\n\t\tannotation SummarizationSetBy = User\n\n"
    if name == "fact_sales":
        ml = metric_lines()
        for mname, heading, dax, fmt, note in MEASURES:
            line, definition = ml[heading.lower()]
            out += doc(f"knowledge/metrics.md line {line}: {definition}", "\t")
            if note:
                out += doc(note, "\t")
            out += f"\tmeasure '{mname}' = {dax}\n\t\tformatString: {fmt}\n\t\tlineageTag: {tag('measure', mname)}\n\t\tdisplayFolder: metrics\n\n"
    path = MART_PATH.rstrip("\\") + "\\" + f"{name}.csv"
    out += (f"\tpartition {name} = m\n\t\tmode: import\n\t\tsource =\n"
            f"\t\t\t\tlet\n"
            f"\t\t\t\t    Source = Csv.Document(File.Contents(\"{path}\"),[Delimiter=\",\", Columns={len(df.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n"
            f"\t\t\t\t    #\"Promoted Headers\" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n"
            f"\t\t\t\t    #\"Changed Type\" = Table.TransformColumnTypes(#\"Promoted Headers\",{{{', '.join(m_types)}}})\n"
            f"\t\t\t\tin\n\t\t\t\t    #\"Changed Type\"\n\n")
    return out


def main():
    d = MODEL / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)
    for name in TABLES:
        (d / "tables" / f"{name}.tmdl").write_text(table_tmdl(name), encoding="utf-8")
    rel = ""
    for f, fc, t, tc in RELATIONSHIPS:
        rel += f"relationship {t}_to_{f}\n\tfromColumn: {f}.{fc}\n\ttoColumn: {t}.{tc}\n\n"
    (d / "relationships.tmdl").write_text(rel, encoding="utf-8")
    order = sorted(TABLES)
    model = ("model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n"
             "\tvalueFilterBehavior: independent\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"
             "annotation __PBI_TimeIntelligenceEnabled = 0\n\n"
             f"annotation NORDA_BuiltBy = .claude/skills/powerbi/build_pbi.py\n\n"
             f"annotation PBI_QueryOrder = {json.dumps(order)}\n\n"
             "annotation PBI_ProTooling = [\"DevMode\"]\n\n" +
             "".join(f"ref table {t}\n" for t in order) + "\nref cultureInfo en-US\n\n")
    (d / "model.tmdl").write_text(model, encoding="utf-8")
    # model view: facts in the middle, dimensions around them
    pos = {"dim_country": (0, 40), "dim_channel": (0, 420), "fact_sales": (320, 180), "dim_date": (640, 0),
           "dim_product": (640, 420), "fact_inventory": (960, 200)}
    nodes = [{"location": {"x": x, "y": y}, "nodeIndex": t, "nodeLineageTag": tag(t),
              "size": {"height": 300 if t in ("fact_sales", "dim_date") else 220, "width": 234}, "zIndex": i}
             for i, (t, (x, y)) in enumerate(pos.items())]
    layout = {"version": "1.1.0", "diagrams": [{"ordinal": 0, "scrollPosition": {"x": 0, "y": 0}, "nodes": nodes,
              "name": "All tables", "zoomValue": 100, "pinKeyFieldsToTop": False, "showExtraHeaderInfo": False,
              "hideKeyFieldsWhenCollapsed": False, "tablesLocked": False}],
              "selectedDiagram": "All tables", "defaultDiagram": "All tables"}
    (MODEL / "diagramLayout.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
    ncols = sum(len(c) for _, c in TABLES.values())
    print(f"powerbi: {len(TABLES)} tables, {ncols} columns described, {len(RELATIONSHIPS)} relationships, "
          f"{len(MEASURES)} measures -> {MODEL.relative_to(ROOT)} (CSV path {MART_PATH})")


if __name__ == "__main__":
    main()
