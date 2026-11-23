"""Demand Forecasting (Prophet output, precomputed in the notebook)."""
import streamlit as st

from core import data, insights
from ui import charts, components as ui
from ui.format import money, money_full

ui.page_header("Demand Forecasting", "Expected sales for the coming weeks, with confidence intervals.")

fb = data.forecast_bundle()
future, last = fb["future"], fb["last_actual"]
if future.empty:
    ui.empty_state("No forecast available", "The forecast file contains no dates after the last recorded sale.",
                   "query_stats")
    st.stop()

cards, growth = insights.forecast_insights(fb)
peak = future.loc[future["yhat"].idxmax()]
low = future.loc[future["yhat"].idxmin()]

ui.kpi_cards([
    {"label": "Forecasted Revenue", "value": money(future["yhat"].sum()), "full": money_full(future["yhat"].sum()),
     "icon": "payments", "hint": "Total over the forecast period"},
    {"label": "Average Daily Sales", "value": money(future["yhat"].mean()), "full": money_full(future["yhat"].mean()),
     "icon": "show_chart", "delta": growth, "hint": "vs last 90 days of actual sales"},
    {"label": "Peak Forecast", "value": money(peak["yhat"]), "full": money_full(peak["yhat"]), "icon": "trending_up",
     "hint": f"{peak['ds']:%a %d %b %Y}"},
    {"label": "Forecast Period", "value": f"{len(future)} days", "icon": "calendar_month",
     "hint": f"{future['ds'].min():%d %b %Y} to {future['ds'].max():%d %b %Y}"},
])

ui.section("Sales Forecast", "Historical sales, the forecast and its confidence interval.")
WINDOWS = {"Full history": None, "Last 6 months": 183, "Last 90 days": 90}
with ui.card("Daily sales forecast", f"Actual sales up to {last:%d %b %Y}, forecast afterwards"):
    choice = st.segmented_control("Chart range", list(WINDOWS), default="Full history", key="fc_window")
    charts.show(charts.forecast_chart(fb, WINDOWS.get(choice or "Full history"), 440))
    ui.note("The shaded band is the model's confidence interval. The dotted line marks where the forecast starts. "
            "The 'Model fit (history)' line can be switched on from the legend. The sales data has no Saturday "
            "trading, so Saturday values in the forecast are extrapolated by the model.")

ui.section("Short and Medium Term Outlook")
o1, o2 = st.columns(2)
with o1:
    with ui.card("Next 30 days", "Daily forecast; whiskers show the confidence interval"):
        charts.show(charts.next_days_chart(future, 30, 320))
with o2:
    with ui.card("Monthly forecast", "Lighter bars are months only partly inside the forecast period"):
        charts.show(charts.monthly_forecast(fb["monthly"], 320))

ui.section("Forecast Analysis")
ui.highlight_cards([
    {"label": "Highest forecast day", "value": f"{peak['ds']:%d %b %Y}", "icon": "arrow_upward", "tone": "positive",
     "sub": money_full(peak["yhat"])},
    {"label": "Lowest forecast day", "value": f"{low['ds']:%d %b %Y}", "icon": "arrow_downward", "tone": "warning",
     "sub": money_full(low["yhat"])},
    {"label": "Last 90 days of actual sales", "value": f"{money_full(fb['recent_avg_daily'])} per day",
     "icon": "history", "sub": "Average per calendar day, used as the comparison baseline"},
])
st.html("<div style='height:1rem'></div>")
w1, w2 = st.columns([1, 1.2])
with w1:
    with ui.card("Expected revenue by weekday", "Average forecast per weekday"):
        charts.show(charts.weekday_revenue(fb["weekday"], 300, label="Average forecast"))
with w2:
    with ui.card("Next 30 days", "Forecast values with confidence range"):
        nxt = future.head(30).copy()
        nxt["Day"] = nxt["ds"].dt.strftime("%a %d %b %Y")
        ui.data_table(nxt, [("Day", "Date", "text"), ("yhat", "Forecast", "num", ",.0f"),
                            ("yhat_lower", "Lower", "num", ",.0f"), ("yhat_upper", "Upper", "num", ",.0f")], max_rows=10)
        ui.note("Showing the first 10 of the next 30 days.")

ui.section("Forecast Insights", "Rule-based observations from the forecast. The model itself is not re-trained in the app.")
ui.insight_cards(cards)
ui.footer()
