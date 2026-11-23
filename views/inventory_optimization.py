"""Inventory Optimization (product performance and ABC classification)."""
import streamlit as st

from core import data, insights
from core.config import COLORS
from ui import charts, components as ui, filters
from ui.format import money, money_full, number, pct

ui.page_header("Inventory Optimization",
               "Product performance, ABC classification and replenishment priorities.")
f = filters.sales_filters()

inv_b = data.inventory_bundle(f.start, f.end, f.countries)
if inv_b is None:
    filters.no_data_stop()
inv, abc, k = inv_b["inventory"], inv_b["abc"], inv_b["kpis"]

ui.kpi_cards([
    {"label": "Total Products", "value": number(k["products"]), "icon": "inventory_2"},
    {"label": "Total Quantity Sold", "value": number(k["quantity"]), "icon": "shopping_bag"},
    {"label": "Total Revenue", "value": money(k["revenue"]), "full": money_full(k["revenue"]), "icon": "payments"},
    {"label": "Average Quantity", "value": f"{k['avg_quantity']:,.1f}", "icon": "stacked_bar_chart",
     "hint": "Units sold per product"},
])

ui.section("Product Performance", "Best and weakest products by revenue.")
p1, p2 = st.columns(2)
with p1:
    with ui.card("Top 10 products", "Highest revenue"):
        charts.show(charts.hbar(inv.head(10), "Description", "Revenue", 380))
with p2:
    with ui.card("Lowest performing products", "Lowest revenue"):
        charts.show(charts.hbar(inv.sort_values("Revenue").head(10), "Description", "Revenue", 380,
                                color=COLORS["secondary"]))

ui.section("Revenue Contribution", "A small share of products produces most of the revenue.")
r1, r2 = st.columns([1.5, 1])
with r1:
    with ui.card("Cumulative revenue contribution", "Products ranked from best to weakest seller"):
        charts.show(charts.pareto(inv, 340))
with r2:
    with ui.card("Revenue share by ABC class", "Share of total revenue"):
        charts.show(charts.abc_bars(abc, 340))
with ui.card("Product quantity distribution", "Number of products by units sold"):
    charts.show(charts.histogram(inv_b["hist"], "Units sold per product", 280, money=False,
                                 ytitle="Number of products"))
    ui.note(f"Products above the 95th percentile ({inv_b['hist']['cap']:,.0f} units) are left out of the chart "
            "so the shape of typical products stays readable.")

ui.section("ABC Inventory Classification",
           "Class A products make up the first 80% of cumulative revenue, B the next 15% and C the last 5%.")
a = abc.set_index("ABC")
ui.highlight_cards([
    {"label": "Class A: high value", "value": f"{int(a.loc['A', 'Products']):,} products", "icon": "workspace_premium",
     "tone": "positive", "sub": f"{pct(a.loc['A', 'ProductShare'])} of products, {pct(a.loc['A', 'RevenueShare'])} of revenue"},
    {"label": "Class B: medium value", "value": f"{int(a.loc['B', 'Products']):,} products", "icon": "balance",
     "sub": f"{pct(a.loc['B', 'ProductShare'])} of products, {pct(a.loc['B', 'RevenueShare'])} of revenue"},
    {"label": "Class C: low value", "value": f"{int(a.loc['C', 'Products']):,} products", "icon": "arrow_downward",
     "tone": "warning", "sub": f"{pct(a.loc['C', 'ProductShare'])} of products, {pct(a.loc['C', 'RevenueShare'])} of revenue"},
])
st.html("<div style='height:1rem'></div>")
with ui.card("Products by class", "Choose a class to list its highest-revenue products"):
    cls = st.segmented_control("Class", ["All", "A", "B", "C"], default="All", key="abc_class") or "All"
    view = inv if cls == "All" else inv[inv["ABC"] == cls]
    ui.data_table(view, [
        ("Description", "Product", "text"), ("ABC", "Class", "badge_abc"),
        ("Revenue", "Revenue", "num", ",.0f"), ("Quantity", "Units sold", "num", ",.0f"),
        ("Orders", "Orders", "num", ",.0f"), ("RevenueShare", "Revenue share", "num", ".2%"),
    ], max_rows=15)
    ui.note(f"Showing the top 15 of {len(view):,} products.")

ui.section("Low-Sales Products", "Products in the bottom quartile by units sold.")
low = inv[inv["LowSales"]].sort_values("Quantity")
l1, l2 = st.columns([1, 2])
with l1:
    ui.highlight_cards([{"label": "Low-sales products", "value": f"{len(low):,}", "icon": "warning", "tone": "warning",
                         "sub": f"Fewer than {inv_b['low_cut']:,.0f} units sold in the selection"}])
with l2:
    with ui.card("Lowest 10 by units sold"):
        ui.data_table(low, [("Description", "Product", "text"), ("Quantity", "Units sold", "num", ",.0f"),
                            ("Revenue", "Revenue", "num", ",.0f"), ("LowSales", "Status", "flag")], max_rows=10)

ui.section("Reorder Recommendations", "Highest-revenue products to keep in stock first.")
with ui.card():
    ui.data_table(inv, [
        ("Description", "Product", "text"), ("ABC", "Class", "badge_abc"),
        ("Revenue", "Revenue", "num", ",.0f"), ("Quantity", "Units sold", "num", ",.0f"),
        ("Orders", "Orders", "num", ",.0f"),
    ], max_rows=15)
    ui.note("The dataset has no stock-on-hand or lead-time figures, so priorities are based on sales performance "
            "only. Compare these products with your current stock levels before reordering.")

ui.section("Inventory Insights", "Rule-based guidance from the classification above.")
ui.insight_cards(insights.inventory_insights(inv_b))
ui.footer()
