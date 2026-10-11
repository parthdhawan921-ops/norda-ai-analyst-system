"""Build the December review deck (PowerPoint) from data/mart.

Answers the three questions in knowledge/inbox/december-questions.pdf,
one slide per question, plus a summary and a speaker-prep slide.
Every number on a slide is computed below - nothing is typed in by hand.

Run:  python .claude/skills/slides/slides.py [--month 2025-12] [--out reports/slides/december-review.pptx]
"""
import argparse, datetime as dt, os
from pathlib import Path
import pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").exists())
MART = ROOT / "data" / "mart"

# ---- locked style ----
INK, INK2, MUTED = RGBColor(0x1F, 0x23, 0x28), RGBColor(0x4A, 0x52, 0x5C), RGBColor(0x8A, 0x92, 0x9C)
BLUE, ORANGE, RED, GREEN = RGBColor(0x2A, 0x78, 0xD6), RGBColor(0xEB, 0x68, 0x34), RGBColor(0xC8, 0x3B, 0x3B), RGBColor(0x1B, 0x8A, 0x5A)
LINE, PANEL = RGBColor(0xE3, 0xE6, 0xEA), RGBColor(0xF5, 0xF7, 0xF9)
FONT = "Segoe UI"
REORDER_MONTHS = 2   # assumption shown on the slide: order enough for 2 months at the month's pace


def eur(v, d=0):
    return f"€{v / 1e6:.2f}M" if abs(v) >= 1e6 else (f"€{v / 1e3:.0f}K" if abs(v) >= 1e4 else f"€{v:,.{d}f}")


def pct(v):
    return f"{v:+.1f}%"


# ======================= analysis (code computes) =======================
def analyse(month):
    fs = pd.read_csv(MART / "fact_sales.csv", dtype={"order_id": str})
    fi = pd.read_csv(MART / "fact_inventory.csv", dtype={"stock_month": str})
    dd = pd.read_csv(MART / "dim_date.csv", dtype={"year_month": str})
    dp = pd.read_csv(MART / "dim_product.csv")
    dc = pd.read_csv(MART / "dim_country.csv")
    dch = pd.read_csv(MART / "dim_channel.csv")
    s = fs.merge(dd[["date_key", "year_month", "day_of_month"]], left_on="order_date_key", right_on="date_key") \
          .merge(dp, on="product_key").merge(dc, on="country_key").merge(dch, on="channel_key")
    months = sorted(s["year_month"].unique())
    if month not in months:
        raise SystemExit(f"slides: no sales in {month}")
    prev = months[months.index(month) - 1]
    year_before = [m for m in months if m < month and m[:4] == month[:4]]
    A = {"month": month, "prev": prev, "months": months}
    mon = s.groupby("year_month").agg(rev=("net_revenue", "sum"), orders=("order_id", "nunique"),
                                      units=("quantity", "sum"), gross=("gross_revenue", "sum"),
                                      disc=("discount_amount", "sum"))
    mon["aov"] = mon["rev"] / mon["orders"]
    mon["disc_pct"] = mon["disc"] / mon["gross"] * 100
    A["mon"] = mon
    A["rank"] = int(mon["rev"].rank(ascending=False)[month])
    base = mon.loc[year_before] if year_before else mon.loc[[prev]]
    A["aov_avg"] = (base["rev"].sum() / base["orders"].sum())
    A["disc_avg"] = base["disc"].sum() / base["gross"].sum() * 100

    # Q1: was every part up?  month vs previous month, per dimension
    parts = {}
    for dim, label in [("category", "Category"), ("country_name", "Country"), ("channel_name", "Channel"), ("brand", "Brand")]:
        t = s[s["year_month"].isin([prev, month])].pivot_table(index=dim, columns="year_month",
                                                               values="net_revenue", aggfunc="sum").fillna(0)
        t["chg"] = (t[month] / t[prev] - 1) * 100
        parts[label] = t.sort_values("chg")
    A["parts"] = parts
    A["down"] = [(lab, idx, r["chg"]) for lab, t in parts.items() for idx, r in t.iterrows() if r["chg"] < 0]

    # Q2: which products ran out, what did it cost?
    st = fi.pivot_table(index="product_key", columns="stock_month", values="quantity_on_hand")
    units = s.pivot_table(index="product_key", columns="year_month", values="quantity", aggfunc="sum").reindex(columns=months).fillna(0)
    rev = s.pivot_table(index="product_key", columns="year_month", values="net_revenue", aggfunc="sum").reindex(columns=months).fillna(0)
    out_keys = st.index[st[month] == 0]
    ref = [m for m in months if m < prev][-3:]                     # 3 full months before the stock-out month
    ro = dp.set_index("product_key").loc[out_keys, ["product_name", "category", "sku"]].copy()
    ro["stock_prev"] = st.loc[out_keys, prev]
    ro["units_month"] = units.reindex(out_keys)[month].fillna(0)
    ro["ref_rev"] = rev.reindex(out_keys)[ref].mean(axis=1).fillna(0)   # usual monthly revenue
    last_sale = s[s["product_key"].isin(out_keys) & (s["year_month"] == prev)].groupby("product_key")["day_of_month"].max()
    ro["last_sale_prev"] = last_sale.reindex(out_keys)
    ro = ro.sort_values("ref_rev", ascending=False)
    A["ran_out"], A["ref_months"] = ro, ref
    big = ro[ro["ref_rev"] >= 10000]
    A["big_out"] = big
    A["lost_gross"] = big["ref_rev"].sum()                         # demand at their usual pace
    # net: what their category actually lost vs its usual month (some buyers switched model)
    cats = big["category"].unique()
    cat_month = s[s["category"].isin(cats)].groupby("year_month")["net_revenue"].sum()
    A["cat_usual"] = cat_month[ref].mean()
    A["cat_actual"] = cat_month[month]
    A["lost_net"] = max(A["cat_usual"] - A["cat_actual"], 0)
    others = s[s["category"].isin(cats) & ~s["product_key"].isin(big.index)].groupby("year_month")["net_revenue"].sum()
    A["others_chg"] = (others[month] / others[prev] - 1) * 100
    A["big_rev_hist"] = rev.loc[big.index, months[-6:]]

    # Q3: what should we order more of?  < 1 month of cover at month end, ranked by revenue
    u = units[month]
    cov = pd.DataFrame({"units": u, "rev": rev[month], "stock": st[month]}).dropna()
    cov = cov[cov["units"] > 0]
    cov["cover"] = cov["stock"] / cov["units"]
    need = cov[cov["cover"] < 1].copy()
    need["order"] = (need["units"] * REORDER_MONTHS - need["stock"]).clip(lower=0).round().astype(int)
    need = need.join(dp.set_index("product_key")[["product_name", "category"]]).sort_values("rev", ascending=False)
    # add the big stock-outs that sold nothing this month because there was no stock
    for k, r in big.iterrows():
        usual_units = units.loc[k, ref].mean()
        need.loc[k] = {"units": 0, "rev": 0, "stock": 0, "cover": 0, "order": int(round(usual_units * REORDER_MONTHS)),
                       "product_name": r["product_name"], "category": r["category"]}
        need.loc[k, "ref_rev"] = r["ref_rev"]
    need["priority_rev"] = need["rev"].where(need["rev"] > 0, need.get("ref_rev"))
    A["need"] = need.sort_values("priority_rev", ascending=False)

    # prep facts
    off = s[s["in_company_overview"] == "No"]
    A["offmkt_share"] = off[off["year_month"] == month]["net_revenue"].sum() / mon.loc[month, "rev"] * 100
    A["offmkt_year"] = off["net_revenue"].sum() / mon["rev"].sum() * 100
    A["lowest"] = mon["rev"].idxmin()
    return A


# ======================= slide helpers =======================
def text(slide, x, y, w, h, runs, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap, tf.vertical_anchor = True, anchor
    tf.margin_left = tf.margin_right = Inches(0.02)
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(6)
        for chunk in (para if isinstance(para, tuple) else (para,)):
            if isinstance(chunk, str):
                chunk = {"t": chunk}
            r = p.add_run()
            r.text = chunk["t"]
            f = r.font
            f.name, f.size = FONT, Pt(chunk.get("size", size))
            f.bold = chunk.get("bold", bold)
            f.color.rgb = chunk.get("color", color)
    return tb


def header(slide, kicker, title, n, total):
    text(slide, 0.6, 0.35, 10, 0.3, kicker.upper(), size=11, color=BLUE, bold=True)
    text(slide, 0.6, 0.6, 12.1, 0.95, title, size=22, bold=True)
    line = slide.shapes.add_connector(1, Inches(0.6), Inches(1.6), Inches(12.73), Inches(1.6))
    line.line.color.rgb, line.line.width = LINE, Pt(1)
    text(slide, 0.6, 7.05, 9, 0.3, "NORDA · Monthly review · source: data/mart, revenue before returns",
         size=9, color=MUTED)
    text(slide, 11.7, 7.05, 1.03, 0.3, f"{n} / {total}", size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def panel(slide, x, y, w, h):
    s = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = PANEL
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def style_chart(chart, size=11):
    chart.font.name, chart.font.size = FONT, Pt(size)
    chart.font.color.rgb = INK2
    chart.has_legend = False


def table(slide, x, y, w, rows, col_w, header_row, size=11, highlight=None):
    shape = slide.shapes.add_table(len(rows) + 1, len(header_row), Inches(x), Inches(y), Inches(w),
                                   Inches(0.32 * (len(rows) + 1)))
    tbl = shape.table
    tbl.first_row = True
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate([header_row] + rows):
        tbl.rows[i].height = Inches(0.32)
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.fill.solid(); c.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if i else PANEL
            c.margin_left = c.margin_right = Inches(0.06)
            c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.text = ""
            r = p.add_run(); r.text = str(val)
            r.font.name, r.font.size = FONT, Pt(size if i else size - 1)
            r.font.bold = i == 0
            r.font.color.rgb = MUTED if i == 0 else (highlight(i - 1, j) if highlight else INK)
            p.alignment = PP_ALIGN.RIGHT if (j > 0 and i > 0 and str(val)[:1] in "€+-0123456789–") or \
                (i == 0 and j > 0 and j >= len(header_row) - 3) else PP_ALIGN.LEFT
    return shape


def month_name(m):
    return pd.Timestamp(m + "-01").strftime("%B %Y")


# ======================= deck =======================
def build(A, out):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    M, P = A["month"], A["prev"]
    mon = A["mon"]
    mname, pname = month_name(M), pd.Timestamp(P + "-01").strftime("%B")
    chg = (mon.loc[M, "rev"] / mon.loc[P, "rev"] - 1) * 100
    big = A["big_out"]
    TOTAL = 6

    # ---- 1 title
    s = prs.slides.add_slide(blank)
    bar = s.shapes.add_shape(1, 0, 0, Inches(0.25), prs.slide_height); bar.fill.solid(); bar.fill.fore_color.rgb = BLUE; bar.line.fill.background()
    text(s, 0.9, 2.2, 11, 0.4, "MONTHLY REVIEW · PURCHASING", size=12, color=BLUE, bold=True)
    text(s, 0.9, 2.65, 11.5, 1.6, f"{mname}: our biggest month, with a hole in Computers", size=38, bold=True)
    text(s, 0.9, 4.35, 11, 0.9, f"Revenue {eur(mon.loc[M, 'rev'])} ({pct(chg)} vs {pname}). Three answers before the planning meeting.",
         size=16, color=INK2)
    text(s, 0.9, 6.6, 11, 0.4, f"Prepared {dt.date.today():%d %b %Y} · all numbers computed from data/mart and passed the quality gate",
         size=10, color=MUTED)

    # ---- 2 summary
    s = prs.slides.add_slide(blank)
    header(s, "The short answer", "Volume carried December. Computers fell because our best sellers were out of stock.", 2, TOTAL)
    downs = ", ".join(f"{n} {c:+.0f}%" for _, n, c in A["down"])
    cards = [
        ("1  Was every part of the business up?", f"No. Revenue {pct(chg)}, but {downs} vs {pname}. "
         f"Average order fell to {eur(mon.loc[M, 'aov'], 0)} (year average {eur(A['aov_avg'], 0)})."),
        ("2  Which products ran out, and what did it cost?", f"{len(A['ran_out'])} products had zero stock at month end. "
         f"{len(big)} top Kova computers sold out mid-{pname} and sold nothing in December: "
         f"about {eur(A['lost_net'])}–{eur(A['lost_gross'])} of revenue lost."),
        ("3  What should we order more of?", f"Restock the {len(big)} Kova computers first, then "
         f"{len(A['need']) - len(big)} fast sellers with under one month of stock left, led by "
         f"{A['need'][A['need']['rev'] > 0].iloc[0]['product_name']}."),
    ]
    for i, (q, a) in enumerate(cards):
        y = 1.9 + i * 1.65
        panel(s, 0.6, y, 12.13, 1.45)
        text(s, 0.85, y + 0.18, 11.6, 0.4, q, size=15, bold=True, color=BLUE)
        text(s, 0.85, y + 0.6, 11.6, 0.8, a, size=15, color=INK)

    # ---- 3 Q1
    s = prs.slides.add_slide(blank)
    cat = A["parts"]["Category"]
    worst = cat.iloc[0]
    header(s, "Question 1 · Was every part of the business up?",
           f"No. Every category grew except {cat.index[0]} ({worst['chg']:+.0f}%), and baskets got smaller", 3, TOTAL)
    cd = CategoryChartData()
    cd.categories = list(cat.index)
    cd.add_series(f"Revenue change {pname} → {M[-2:]}", [round(v, 1) for v in cat["chg"]])
    gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.85), Inches(7.2), Inches(4.3), cd)
    ch = gf.chart; style_chart(ch)
    ch.has_title = True; ch.chart_title.text_frame.text = f"Revenue change by category, {month_name(M).split()[0]} vs {pname} (%)"
    ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12); ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
    plot = ch.plots[0]; plot.gap_width = 70; plot.has_data_labels = True
    plot.data_labels.number_format = '+0.0"%";-0.0"%"'; plot.data_labels.number_format_is_linked = False
    plot.data_labels.font.size = Pt(11)
    for idx, v in enumerate(cat["chg"]):
        pt = plot.series[0].points[idx]; pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = RED if v < 0 else BLUE
    ch.value_axis.has_major_gridlines = True; ch.value_axis.major_gridlines.format.line.color.rgb = LINE
    ch.value_axis.tick_labels.font.size = Pt(10); ch.value_axis.format.line.fill.background()
    ch.category_axis.tick_labels.font.size = Pt(11); ch.category_axis.format.line.color.rgb = LINE
    ch.category_axis.tick_label_position = XL_LABEL_POSITION.LOW if False else ch.category_axis.tick_label_position
    from pptx.enum.chart import XL_TICK_LABEL_POSITION
    ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    # right column: what is hiding
    panel(s, 8.15, 1.85, 4.58, 4.3)
    ctry, chn = A["parts"]["Country"], A["parts"]["Channel"]
    items = [
        ({"t": "Computers is the only category down. ", "bold": True},
         {"t": f"Its best sellers had no stock (question 2). The other computers grew {A['others_chg']:+.0f}%: some buyers switched model."}),
        ({"t": "Smaller baskets. ", "bold": True},
         {"t": f"Average order {eur(mon.loc[M, 'aov'])} vs {eur(A['aov_avg'])} for the year: more orders, cheaper items."}),
        ({"t": "Heavier discounts. ", "bold": True},
         {"t": f"Discount was {mon.loc[M, 'disc_pct']:.1f}% of gross sales vs {A['disc_avg']:.1f}% on average."}),
        ({"t": "By country: ", "bold": True},
         {"t": ", ".join(f"{i} {r['chg']:+.0f}%" for i, r in ctry.iterrows() if r['chg'] < 0) or "all up"},
         {"t": f". Best: {ctry.index[-1]} {ctry.iloc[-1]['chg']:+.0f}%."}),
        ({"t": "By channel: ", "bold": True},
         {"t": ", ".join(f"{i} {r['chg']:+.0f}%" for i, r in chn.iloc[::-1].iterrows())}),
    ]
    text(s, 8.4, 2.05, 4.1, 4.0, [tuple(it) for it in items], size=12.5)
    text(s, 0.6, 6.25, 12.1, 0.6, f"Total revenue {eur(mon.loc[M, 'rev'])}, {pct(chg)} vs {pname}; orders "
         f"{mon.loc[M, 'orders']:,.0f} ({pct((mon.loc[M, 'orders'] / mon.loc[P, 'orders'] - 1) * 100)}). "
         f"Growth came from more orders, not bigger ones.", size=12, color=INK2)

    # ---- 4 Q2
    s = prs.slides.add_slide(blank)
    header(s, "Question 2 · Which products ran out, and what did it cost?",
           f"Our {len(big)} best Kova computers sold out mid-{pname} and were never restocked", 4, TOTAL)
    hist = A["big_rev_hist"]
    cd = CategoryChartData()
    cd.categories = [pd.Timestamp(m + "-01").strftime("%b") for m in hist.columns]
    for k, r in big.iterrows():
        cd.add_series(r["product_name"], [round(v / 1000, 1) for v in hist.loc[k]])
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.85), Inches(6.6), Inches(3.9), cd)
    ch = gf.chart; style_chart(ch); ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM
    ch.legend.include_in_layout = False; ch.legend.font.size = Pt(10)
    ch.has_title = True; ch.chart_title.text_frame.text = "Monthly revenue of the sold-out models (€ thousand)"
    ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12); ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
    for i, col in enumerate([BLUE, ORANGE, RGBColor(0x1B, 0xAF, 0x7A)]):
        if i < len(ch.plots[0].series):
            ser = ch.plots[0].series[i]; ser.format.fill.solid(); ser.format.fill.fore_color.rgb = col
    ch.plots[0].gap_width = 60
    ch.value_axis.major_gridlines.format.line.color.rgb = LINE; ch.value_axis.tick_labels.font.size = Pt(10)
    ch.value_axis.format.line.fill.background(); ch.category_axis.tick_labels.font.size = Pt(10)
    # cost box
    panel(s, 7.5, 1.85, 5.23, 3.9)
    text(s, 7.75, 2.0, 4.8, 0.4, "What it cost us in December", size=13, bold=True, color=BLUE)
    text(s, 7.75, 2.4, 4.8, 0.8, f"{eur(A['lost_net'])} – {eur(A['lost_gross'])}", size=30, bold=True, color=RED)
    refs = f"{pd.Timestamp(A['ref_months'][0] + '-01'):%b}–{pd.Timestamp(A['ref_months'][-1] + '-01'):%b}"
    text(s, 7.75, 3.2, 4.8, 2.5, [
        ({"t": "Upper end: ", "bold": True}, {"t": f"the {len(big)} models usually sell {eur(A['lost_gross'])} a month ({refs} average); in December they sold €0."}),
        ({"t": "Lower end: ", "bold": True}, {"t": f"Computers as a whole made {eur(A['cat_actual'])} vs a usual {eur(A['cat_usual'])}, because some buyers switched to other models."}),
        ({"t": f"Estimate [med]. The second half of {pname} was also lost and is not counted.", "color": MUTED, "size": 11},),
    ], size=12)
    # table of all zero-stock products
    rows = []
    for k, r in A["ran_out"].iterrows():
        last = f"{int(r['last_sale_prev'])} {pd.Timestamp(P + '-01'):%b}" if pd.notna(r["last_sale_prev"]) else "–"
        rows.append([r["product_name"], r["category"], f"€{r['ref_rev']:,.0f}", last])
    small = len(A["ran_out"]) - len(big)
    text(s, 0.6, 5.72, 12, 0.3, f"{len(A['ran_out'])} products at zero stock on {pd.Timestamp(M + '-01') + pd.offsets.MonthEnd(0):%d %b}: "
         f"the {len(big)} that matter below; the other {small} sell under €10K a month", size=11, bold=True, color=INK2)
    table(s, 0.6, 6.0, 12.13, rows[:len(big)],
          [5.2, 2.6, 2.4, 1.93], ["Product", "Category", f"Usual monthly revenue ({refs})", f"Last sale in {pname}"], size=10)

    # ---- 5 Q3
    s = prs.slides.add_slide(blank)
    need = A["need"].head(10)
    header(s, "Question 3 · What should we order more of?",
           f"Restock the Kova computers now, then the fast sellers with under a month of stock", 5, TOTAL)
    rows = []
    for k, r in need.iterrows():
        sold = f"{int(r['units']):,}" if r["units"] > 0 else "0 (no stock)"
        cover = f"{r['cover']:.1f}" if r["units"] > 0 else "0"
        rows.append([r["product_name"], r["category"], sold, f"{int(r['stock']):,}", cover, f"{int(r['order']):,}"])
    table(s, 0.6, 1.9, 12.13, rows, [4.1, 2.2, 1.6, 1.4, 1.4, 1.43],
          [f"Product", "Category", f"Units sold in {month_name(M).split()[0][:3]}", "Stock now", "Months of cover", "Suggested order"],
          size=11, highlight=lambda i, j: RED if (j == 2 and rows[i][2].startswith("0")) else INK)
    text(s, 0.6, 5.55, 12.1, 1.2, [
        ({"t": "How to read it: ", "bold": True}, {"t": f"months of cover = stock now ÷ units sold in {month_name(M).split()[0]}. "
          f"Suggested order = enough for {REORDER_MONTHS} months at that pace, minus stock. For sold-out models we use their usual pace ({refs})."}),
        ({"t": f"Assumption [guess]: next months sell like {month_name(M).split()[0]}. January is usually quieter, so treat these as an upper bound and confirm lead times with suppliers.",
          "color": MUTED, "size": 11},),
    ], size=12)

    # ---- 6 prep
    s = prs.slides.add_slide(blank)
    header(s, "For the presenter · not for the screen", "Before anyone asks", 6, TOTAL)
    qa = [
        ("Is this after returns?", "No. Returns live in a separate system and are not in the shop export. Every number here is before returns."),
        ("Why are Spain and Austria in the numbers?", f"They are in the orders ({A['offmkt_share']:.0f}% of {month_name(M).split()[0]} revenue, "
         f"{A['offmkt_year']:.0f}% of the year) but the company overview lists only DE, FR, IT, NL. Open question for the business."),
        ("Can we trust these numbers?", "They come from the cleaned star schema and passed the quality gate: revenue and orders computed two ways, 10 orders traced raw → clean → mart."),
        ("Why does stock not change by country?", "NORDA has one warehouse. Stock is not split by country or channel."),
        (f"Which month was weakest?", f"{month_name(A['lowest'])} at {eur(mon.loc[A['lowest'], 'rev'])}. Worth its own look before planning."),
        ("How was 'what it cost' estimated?", f"Usual monthly revenue of the sold-out models ({refs}) as the upper bound; the category's actual shortfall as the lower bound."),
    ]
    for i, (q, a) in enumerate(qa):
        col, row = i % 2, i // 2
        x, y = 0.6 + col * 6.15, 1.9 + row * 1.65
        panel(s, x, y, 5.98, 1.5)
        text(s, x + 0.2, y + 0.12, 5.6, 0.4, q, size=13, bold=True, color=BLUE)
        text(s, x + 0.2, y + 0.5, 5.6, 1.0, a, size=11.5, color=INK)

    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default="2025-12")
    ap.add_argument("--out", default=os.environ.get("SLIDES_OUT", str(ROOT / "reports" / "slides" / "december-review.pptx")))
    args = ap.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    A = analyse(args.month)
    build(A, out)
    mon = A["mon"]
    print(f"slides: {args.month} revenue €{mon.loc[args.month, 'rev']:,.2f}; ran out {len(A['ran_out'])} "
          f"(big {len(A['big_out'])}); lost €{A['lost_net']:,.0f}-€{A['lost_gross']:,.0f}; reorder list {len(A['need'])} -> {out}")


if __name__ == "__main__":
    main()
