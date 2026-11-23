"""Customer Segmentation (RFM + K-Means, precomputed in the notebook)."""
import streamlit as st

from core import data, insights
from core.config import SEGMENT_ORDER
from ui import charts, components as ui, filters
from ui.format import money_full, number

ui.page_header("Customer Segmentation",
               "RFM analysis and K-Means clusters: who your customers are and how they behave.")
segments, clusters = filters.customer_filters()

c = data.customer_bundle(segments, clusters)
if c is None:
    filters.no_data_stop("No customers match the selected segments and clusters.")
k = c["kpis"]

ui.kpi_cards([
    {"label": "Total Customers", "value": number(k["customers"]), "icon": "group"},
    {"label": "Average Recency", "value": f"{k['recency']:.0f} days", "icon": "schedule",
     "hint": "Days since the last purchase"},
    {"label": "Average Frequency", "value": f"{k['frequency']:.1f}", "icon": "repeat", "hint": "Orders per customer"},
    {"label": "Average Monetary Value", "value": money_full(k["monetary"]), "icon": "payments",
     "hint": "Total spend per customer"},
])

ui.section("Segment and Cluster Distribution", "How customers split across segments and K-Means clusters.")
d1, d2, d3 = st.columns([1, 1, 1])
seg = c["segments"].set_index("CustomerSegment")
seg = seg.reindex([s for s in SEGMENT_ORDER if s in seg.index] + [s for s in seg.index if s not in SEGMENT_ORDER]).reset_index()
with d1:
    with ui.card("Customer segments", "Share of customers"):
        charts.show(charts.segment_donut(seg, 320))
with d2:
    with ui.card("Clusters", "Customers per K-Means cluster"):
        charts.show(charts.cluster_bar(c["clusters"], 320))
with d3:
    with ui.card("Spend by segment", "Share of total customer spend"):
        charts.show(charts.revenue_share_bar(seg, 320))

ui.section("Recency, Frequency and Monetary Analysis",
           "Each dot is a customer. Colours show the segment. Monetary value uses a log scale because a few "
           "customers spend far more than the rest.")
s1, s2 = st.columns(2)
with s1:
    with ui.card("Recency vs monetary value", "Customers who bought recently tend to spend more"):
        charts.show(charts.rfm_scatter(c["rfm"], "Recency", 400))
with s2:
    with ui.card("Frequency vs monetary value", "Frequent buyers account for the highest spend"):
        charts.show(charts.rfm_scatter(c["rfm"], "Frequency", 400))

ui.section("Segment Summary", "Average behaviour and value of each segment and cluster.")
t1, t2 = st.columns([1.5, 1])
with t1:
    with ui.card("Segments"):
        ui.data_table(seg, [
            ("CustomerSegment", "Segment", "badge_segment"),
            ("Customers", "Customers", "num", ",.0f"),
            ("CustomerShare", "Share %", "num", ".1f"),
            ("AvgRecency", "Avg recency", "num", ".0f"),
            ("AvgFrequency", "Avg orders", "num", ".1f"),
            ("AvgMonetary", "Avg spend", "num", ",.0f"),
            ("RevenueShare", "Spend share %", "num", ".1f"),
        ])
with t2:
    with ui.card("Clusters"):
        ui.data_table(c["clusters"], [
            ("Cluster", "Cluster", "text"),
            ("Customers", "Customers", "num", ",.0f"),
            ("Recency", "Recency", "num", ".0f"),
            ("Frequency", "Frequency", "num", ".1f"),
            ("Monetary", "Monetary", "num", ",.0f"),
        ])

ui.section("Top Customers", "The 20 highest-spending customers in the selection.")
ui.data_table(c["top20"], [
    ("CustomerID", "Customer ID", "text"),
    ("CustomerSegment", "Segment", "badge_segment"),
    ("Recency", "Recency (days)", "num", ".0f"),
    ("Frequency", "Orders", "num", ".0f"),
    ("Monetary", "Total spend", "num", ",.0f"),
])

ui.section("Recommendations", "Rule-based suggestions derived from the segment summary.")
ui.insight_cards(insights.customer_recommendations(c))
ui.footer()
