"""Filter bars. Selections persist while the user moves between pages."""
from __future__ import annotations

from datetime import timedelta

import streamlit as st

from core import data
from core.data import Filters
from ui.components import empty_state

PERIODS = ["All time", "Last 90 days", "Last 30 days", "Custom"]


def _sync(widget_key: str, state_key: str) -> None:
    """Copy a widget value into persistent state; ignore 'deselect' clicks."""
    value = st.session_state.get(widget_key)
    if value is None:
        st.session_state[widget_key] = st.session_state[state_key]
    else:
        st.session_state[state_key] = value


def sales_filters() -> Filters:
    """Period + country filter used by Overview, Sales, Inventory and AI Insights."""
    d_min, d_max = data.data_bounds()
    state = st.session_state
    state.setdefault("f_period", "All time")
    state.setdefault("f_from", d_min)
    state.setdefault("f_to", d_max)
    state.setdefault("f_countries", [])

    with st.container(border=True, key="rp-filters"):
        c_period, c_dates, c_country = st.columns([1.9, 1.3, 1.5], vertical_alignment="bottom")
        with c_period:
            st.segmented_control(
                "Period", PERIODS, default=state["f_period"], key="w_period",
                on_change=_sync, args=("w_period", "f_period"),
            )
        period = state["f_period"]

        if period == "Custom":
            with c_dates:
                a, b = st.columns(2)
                a.date_input("From", value=state["f_from"], min_value=d_min, max_value=d_max,
                             key="w_from", on_change=_sync, args=("w_from", "f_from"), format="DD/MM/YYYY")
                b.date_input("To", value=state["f_to"], min_value=d_min, max_value=d_max,
                             key="w_to", on_change=_sync, args=("w_to", "f_to"), format="DD/MM/YYYY")
            start, end = state["f_from"], state["f_to"]
        else:
            days = {"All time": None, "Last 90 days": 90, "Last 30 days": 30}[period]
            start = d_min if days is None else max(d_min, d_max - timedelta(days=days - 1))
            end = d_max
            with c_dates:
                st.html(
                    f'<div class="rp-range"><span>Date range</span>'
                    f'<strong>{start:%d %b %Y} &ndash; {end:%d %b %Y}</strong></div>'
                )

        with c_country:
            st.multiselect(
                "Country", data.country_options(), default=state["f_countries"], key="w_countries",
                placeholder="All countries", on_change=_sync, args=("w_countries", "f_countries"),
            )

    if start > end:
        empty_state("Invalid date range", "The start date is after the end date. Please adjust the range above.",
                    "event_busy")
        st.stop()

    return Filters(start, end, tuple(state["f_countries"]), period)


def customer_filters():
    """Segment + cluster filter for the Customer Segmentation page."""
    rfm = data.load_segments()
    segments = [s for s in ["VIP", "Loyal", "Regular", "At-Risk"] if s in set(rfm["CustomerSegment"])]
    segments += sorted(set(rfm["CustomerSegment"]) - set(segments))
    clusters = sorted(rfm["Cluster"].unique().tolist())
    state = st.session_state
    state.setdefault("f_segments", segments)
    state.setdefault("f_clusters", clusters)

    with st.container(border=True, key="rp-filters"):
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.multiselect("Customer segment", segments, default=state["f_segments"], key="w_segments",
                           on_change=_sync, args=("w_segments", "f_segments"), placeholder="All segments")
        with c2:
            st.multiselect("Cluster", clusters, default=state["f_clusters"], key="w_clusters",
                           on_change=_sync, args=("w_clusters", "f_clusters"), placeholder="All clusters")

    # An empty selection is treated as "all" so the page never ends up blank by accident.
    return tuple(state["f_segments"] or segments), tuple(state["f_clusters"] or clusters)


def no_data_stop(message: str = "No transactions match the selected filters. "
                                "Try a wider date range or fewer countries.") -> None:
    empty_state("No data for this selection", message)
    st.stop()
