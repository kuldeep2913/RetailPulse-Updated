"""AI Insights: executive business-intelligence summary (rule-based)."""
import streamlit as st

from core import data, insights
from ui import charts, components as ui, filters
from ui.format import money, money_full, number, short_text

ui.page_header("AI Insights", "Executive summary of revenue, sales performance and customers.")
f = filters.sales_filters()

b = data.sales_bundle(f.start, f.end, f.countries)
if b is None:
    filters.no_data_stop()
k, facts = b["kpis"], b["facts"]
all_clusters = tuple(sorted(data.load_segments()["Cluster"].unique()))
cust = data.customer_bundle(("VIP", "Loyal", "Regular", "At-Risk"), all_clusters)

ui.note("These insights come from predefined analytical rules applied to your data. No generative AI model is "
        "running, so every statement can be traced back to a figure on this page.")
st.html("<div style='height:.75rem'></div>")

ui.kpi_cards([
    {"label": "Total Revenue", "value": money(k["revenue"]), "full": money_full(k["revenue"]), "icon": "payments"},
    {"label": "Total Orders", "value": number(k["orders"]), "icon": "shopping_cart"},
    {"label": "Total Customers", "value": number(k["customers"]), "icon": "group"},
    {"label": "Average Order Value", "value": money_full(k["aov"], 2), "icon": "receipt_long"},
])

ui.section("Executive Summary", "The leaders in the current selection.")
ui.highlight_cards([
    {"label": "Best performing country", "value": facts["best_country"], "icon": "public", "tone": "positive",
     "sub": f"{facts['best_country_share'] * 100:.1f}% of revenue"},
    {"label": "Best selling product", "value": short_text(facts["best_product"], 42), "icon": "sell", "tone": "positive",
     "sub": f"Top 10 products: {facts['top10_products_share'] * 100:.1f}% of revenue"},
    {"label": "Highest spending customer", "value": f"Customer {facts['best_customer']}", "icon": "workspace_premium",
     "tone": "positive", "sub": money_full(facts["best_customer_revenue"])},
    {"label": "Largest single sale line", "value": money_full(facts["max_line"]), "icon": "arrow_upward",
     "sub": "Highest value of one invoice line"},
    {"label": "Peak month", "value": facts["peak_month"], "icon": "calendar_month",
     "sub": money_full(facts["peak_month_revenue"])},
    {"label": "Returning customers", "value": f"{facts['returning_share'] * 100:.1f}%", "icon": "repeat",
     "sub": "Placed more than one order"},
])

ui.section("Revenue Insights", "How revenue developed over the selected period.")
r1, r2 = st.columns([1.5, 1])
with r1:
    with ui.card("Monthly revenue trend", "Lighter bars mark months only partly covered by the selection"):
        charts.show(charts.monthly_revenue(b["monthly"], 320))
with r2:
    with ui.card("Revenue by weekday"):
        charts.show(charts.weekday_revenue(b["weekday"], 320))

ui.section("Sales Performance Analysis", "Products and markets driving revenue.")
s1, s2 = st.columns(2)
with s1:
    with ui.card("Top 10 products", "By revenue"):
        charts.show(charts.hbar(b["products"].head(10), "Description", "Revenue", 380))
with s2:
    with ui.card("Top 10 countries", "By revenue"):
        charts.show(charts.hbar(b["countries"].head(10), "Country", "Revenue", 380))

ui.section("Customer Insights", "Who spends the most and how customers are segmented.")
c1, c2 = st.columns([1.4, 1])
with c1:
    top_c = b["customers"].head(10).copy()
    top_c["Label"] = "Customer " + top_c["CustomerID"].astype(str)
    with ui.card("Top 10 customers", "By total spend in the selection"):
        charts.show(charts.hbar(top_c, "Label", "Revenue", 380))
with c2:
    with ui.card("Customer segments", "All customers (RFM and K-Means)"):
        charts.show(charts.segment_donut(cust["segments"], 380))

ui.section("Key Observations", "Strengths and risks calculated from the data.")
ui.insight_cards(insights.business_observations(b, cust))

ui.section("Business Recommendations", "Rule-based actions, each supported by a figure from the data.")
ui.insight_cards(insights.business_recommendations(b))
ui.footer()
