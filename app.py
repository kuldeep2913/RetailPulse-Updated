"""RetailPulse - Retail Analytics Dashboard.

Entry point: configures the page, applies the shared theme and routes between
the analytical views using a sidebar navigation.
"""
import streamlit as st

from core.config import ASSETS_DIR
from ui.theme import apply_theme

st.set_page_config(
    page_title="RetailPulse",
    page_icon=str(ASSETS_DIR / "favicon.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# ── Sidebar brand ────────────────────────────────────────────────────────────
# st.logo pins the logo to the top of the sidebar (above the nav links). The wide logo
# already contains the product name; the square favicon is shown in the top bar while
# the sidebar is collapsed.
logo_path = ASSETS_DIR / "logo.png"
if logo_path.exists():
    st.logo(str(logo_path), icon_image=str(ASSETS_DIR / "favicon.png"), size="large")

# ── Page routing ─────────────────────────────────────────────────────────────
pages = [
    st.Page("views/overview.py", title="Overview", icon=":material/dashboard:", default=True),
    st.Page("views/sales_analytics.py", title="Sales Analytics", icon=":material/bar_chart:", url_path="sales-analytics"),
    st.Page("views/customer_segmentation.py", title="Customer Segmentation", icon=":material/groups:",
            url_path="customer-segmentation"),
    st.Page("views/demand_forecasting.py", title="Demand Forecasting", icon=":material/query_stats:",
            url_path="demand-forecasting"),
    st.Page("views/inventory_optimization.py", title="Inventory Optimization", icon=":material/inventory_2:",
            url_path="inventory-optimization"),
    st.Page("views/ai_insights.py", title="AI Insights", icon=":material/lightbulb:", url_path="ai-insights"),
]

st.navigation(pages, position="sidebar").run()

