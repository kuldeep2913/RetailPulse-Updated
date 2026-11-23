"""Sales Analytics."""
import streamlit as st

from core import data, insights
from core.config import COLORWAY
from ui import charts, components as ui, filters
from ui.format import money, money_full, number, short_text

ui.page_header("Sales Analytics", "Revenue, orders and product performance across time, markets and customers.")
f = filters.sales_filters()

b = data.sales_bundle(f.start, f.end, f.countries)
if b is None:
    filters.no_data_stop()
k, facts = b["kpis"], b["facts"]
deltas = data.previous_period_deltas(f.start, f.end, f.countries) if f.label != "All time" else None
d = deltas or {}
hint = f"vs previous {f.days} days" if deltas else ""

ui.kpi_cards([
    {"label": "Total Sales", "value": money(k["revenue"]), "full": money_full(k["revenue"]), "icon": "payments",
     "delta": d.get("revenue"), "hint": hint},
    {"label": "Total Orders", "value": number(k["orders"]), "icon": "shopping_cart", "delta": d.get("orders"), "hint": hint},
    {"label": "Total Customers", "value": number(k["customers"]), "icon": "group", "delta": d.get("customers"), "hint": hint},
    {"label": "Average Order Value", "value": money_full(k["aov"], 2), "icon": "receipt_long",
     "delta": d.get("aov"), "hint": hint},
])

# ---- Revenue trends ------------------------------------------------------------------------
ui.section("Revenue Trends", "How revenue moves over time.")
with ui.card("Daily revenue trend", "Revenue per trading day with a 7-day moving average"):
    charts.show(charts.daily_revenue(b["daily"], 340))
t1, t2 = st.columns([1.5, 1])
with t1:
    with ui.card("Monthly revenue analysis", "Lighter bars mark months only partly covered by the selection"):
        charts.show(charts.monthly_revenue(b["monthly"], 320))
with t2:
    with ui.card("Revenue by weekday", "Total revenue per day of the week"):
        charts.show(charts.weekday_revenue(b["weekday"], 320))

# ---- Markets -----------------------------------------------------------------------------------
ui.section("Markets", "Where revenue comes from.")
m1, m2 = st.columns([1.5, 1])
with m1:
    with ui.card("Top 10 countries by sales", "Total revenue per country"):
        charts.show(charts.hbar(b["countries"].head(10), "Country", "Revenue", 380))
with m2:
    with ui.card("Revenue share", "Top 5 countries versus all others"):
        top5 = b["countries"].head(5)
        rest = b["countries"]["Revenue"].iloc[5:].sum()
        labels = top5["Country"].tolist() + (["All others"] if rest > 0 else [])
        values = top5["Revenue"].tolist() + ([rest] if rest > 0 else [])
        colors = COLORWAY[: len(top5)] + (["#C9D3E0"] if rest > 0 else [])
        charts.show(charts.donut(labels, values, colors, 380, center=money(k["revenue"]), sub="total revenue",
                                 value_name="Revenue", money=True))
with ui.card("Global revenue distribution", "Darker shading means higher revenue (log scale, so smaller markets stay visible)"):
    charts.show(charts.country_map(b["countries"], 380))
    ui.note("Countries without a standard map name (Unspecified, European Community, Channel Islands) are not drawn.")

# ---- Products and customers ----------------------------------------------------------------
ui.section("Products and Customers", "The items and accounts behind the revenue.")
p1, p2 = st.columns(2)
with p1:
    with ui.card("Top 10 products by revenue", "Best-selling products in the selection"):
        charts.show(charts.hbar(b["products"].head(10), "Description", "Revenue", 380))
with p2:
    top_c = b["customers"].head(10).copy()
    top_c["Label"] = "Customer " + top_c["CustomerID"].astype(str)
    with ui.card("Top customers", "Top 10 customers by total spend"):
        charts.show(charts.hbar(top_c, "Label", "Revenue", 380))

# ---- Distribution + highlights -----------------------------------------------------------
ui.section("Sales Distribution and Performance")
ui.highlight_cards([
    {"label": "Best performing country", "value": facts["best_country"], "icon": "public", "tone": "positive",
     "sub": f"{facts['best_country_share'] * 100:.1f}% of revenue"},
    {"label": "Best selling product", "value": short_text(facts["best_product"], 40), "icon": "sell", "tone": "positive",
     "sub": "Highest revenue in this selection"},
    {"label": "Highest sales day", "value": f"{facts['high_day']:%d %b %Y}", "icon": "trending_up",
     "sub": money_full(facts["high_day_revenue"])},
    {"label": "Lowest sales day", "value": f"{facts['low_day']:%d %b %Y}", "icon": "trending_down", "tone": "warning",
     "sub": money_full(facts["low_day_revenue"])},
])
st.html("<div style='height:1rem'></div>")
with ui.card("Distribution of order line values", "How the value of individual sale lines is spread"):
    charts.show(charts.histogram(b["hist"], "Line value", 300))
    ui.note(f"Values above the 99th percentile ({money_full(b['hist']['cap'])}) are left out of the chart so the "
            "shape of typical sales stays readable. They are still included in every total.")

# ---- Detail tables -------------------------------------------------------------------------------
ui.section("Detail Tables")
tab_p, tab_c, tab_k = st.tabs(["Top products", "Top customers", "Countries"])
with tab_p:
    ui.data_table(b["products"].head(10), [("Description", "Product", "text"), ("Revenue", "Revenue", "num", ",.0f"),
                                           ("Quantity", "Units sold", "num", ",.0f")])
with tab_c:
    ui.data_table(b["customers"].head(10), [("CustomerID", "Customer ID", "text"), ("Revenue", "Revenue", "num", ",.0f"),
                                            ("Orders", "Orders", "num", ",.0f")])
with tab_k:
    ct = b["countries"].head(10).copy()
    ct["Share"] = ct["Revenue"] / k["revenue"] * 100
    ui.data_table(ct, [("Country", "Country", "text"), ("Revenue", "Revenue", "num", ",.0f"),
                       ("Orders", "Orders", "num", ",.0f"), ("Share", "Share of revenue %", "num", ".1f")])

# ---- Recommendations -------------------------------------------------------------------------
ui.section("Recommendations", "Rule-based suggestions derived from the numbers above.")
ui.insight_cards(insights.sales_recommendations(b))
ui.footer()
