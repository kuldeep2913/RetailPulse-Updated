"""Overview: executive dashboard."""
import streamlit as st

from core import data, insights
from ui import charts, components as ui, filters
from ui.format import money, money_full, number, short_text

ui.page_header("Retail Analytics Dashboard", "Monitor sales performance, customer behavior, and business growth.")
f = filters.sales_filters()

b = data.sales_bundle(f.start, f.end, f.countries)
if b is None:
    filters.no_data_stop()
k, facts = b["kpis"], b["facts"]
deltas = data.previous_period_deltas(f.start, f.end, f.countries) if f.label != "All time" else None
d = deltas or {}
hint = f"vs previous {f.days} days" if deltas else ""

SEGS = ("VIP", "Loyal", "Regular", "At-Risk")
rfm = data.customer_bundle(SEGS, tuple(sorted(data.load_segments()["Cluster"].unique())))
fb = data.forecast_bundle()
future = fb["future"]
cards, growth = insights.forecast_insights(fb)

ui.hero_row([
    ui.hero_revenue(k["revenue"], b["monthly"], d.get("revenue"), hint),
    ui.hero_aov(k["aov"], k["orders"], b["daily"]["MA7"], d.get("aov"), hint),
    ui.hero_customers(k["customers"], rfm["segments"], facts["returning_share"]),
])
st.html("<div style='height:1rem'></div>")

# The forecast is for all countries, so it is only drawn when no country filter is active
# and the selected period reaches the last day with recorded sales.
show_fc = (not f.countries) and f.end >= fb["last_actual"].date() and not future.empty
t1, t2 = st.columns([2, 1])
with t1:
    with ui.card("Revenue trend", "Daily revenue with the 7-day average" + (", plus the 90-day forecast" if show_fc else "")):
        charts.show(charts.trend_forecast(b["daily"], fb if show_fc else None, 320))
        if f.countries:
            ui.note("The forecast covers all countries, so it is hidden while a country filter is active.")
with t2:
    with ui.card("Revenue by country", f"{facts['best_country']} leads with {facts['best_country_share'] * 100:.1f}%"):
        charts.show(charts.hbar(b["countries"].head(5), "Country", "Revenue", 320))
st.html("<div style='height:1rem'></div>")

p1, p2, p3 = st.columns(3)
with p1:
    with ui.card("Top-selling products", "By revenue"):
        charts.show(charts.hbar(b["products"].head(5), "Description", "Revenue", 300))
with p2:
    with ui.card("Revenue by weekday", "Which days of the week drive sales"):
        charts.show(charts.weekday_revenue(b["weekday"], 300))
with p3:
    if future.empty:
        ui.empty_state("No forecast available", "The forecast file has no future dates.", "query_stats")
    else:
        peak = future.loc[future["yhat"].idxmax()]
        ui.forecast_card(float(future["yhat"].sum()), growth, f"{peak['ds']:%d %b %Y}", len(future))

ui.section("Key Insights", "Rule-based observations calculated from the data.")
ui.insight_cards(insights.business_observations(b, rfm)[:3])

ui.section("Monthly Sales Trends", "Months covered only in part by the selected range are shown in a lighter shade.")
with ui.card("Monthly revenue", "Total revenue per calendar month"):
    charts.show(charts.monthly_revenue(b["monthly"], 330))

ui.section("Sales Performance")
ui.highlight_cards([
    {"label": "Best performing country", "value": facts["best_country"], "icon": "public", "tone": "positive",
     "sub": f"{facts['best_country_share'] * 100:.1f}% of revenue"},
    {"label": "Best selling product", "value": short_text(facts["best_product"], 40), "icon": "sell", "tone": "positive",
     "sub": "Highest revenue in this selection"},
    {"label": "Highest sales day", "value": f"{facts['high_day']:%d %b %Y}", "icon": "trending_up",
     "sub": money_full(facts["high_day_revenue"])},
])

ui.section("Customer Overview", "Segments come from the RFM and K-Means analysis of all customers.")
c1, c2 = st.columns([1, 1.25])
with c1:
    with ui.card("Customer segments", "Share of customers by segment"):
        charts.show(charts.segment_donut(rfm["segments"], 300))
with c2:
    with ui.card("Segment summary", "Average behaviour per segment"):
        seg = rfm["segments"].set_index("CustomerSegment").reindex(
            [s for s in ["VIP", "Loyal", "Regular", "At-Risk"] if s in rfm["segments"]["CustomerSegment"].values]).reset_index()
        ui.data_table(seg, [
            ("CustomerSegment", "Segment", "badge_segment"),
            ("Customers", "Customers", "num", ",.0f"),
            ("CustomerShare", "Share %", "num", ".1f"),
            ("AvgRecency", "Avg recency (days)", "num", ".0f"),
            ("AvgFrequency", "Avg orders", "num", ".1f"),
            ("AvgMonetary", "Avg spend", "num", ",.0f"),
        ])
        ui.note(f"Returning customers in the current selection: {facts['returning_share'] * 100:.1f}% "
                "placed more than one order.")

ui.team_section()
