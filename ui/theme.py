"""Theme: injects the centralised stylesheet and registers the Plotly template."""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from core.config import ASSETS_DIR, COLORS, COLORWAY

FONT_STACK = ('"Plus Jakarta Sans", Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
              '"Helvetica Neue", Arial, sans-serif')


def _build_template() -> go.layout.Template:
    axis = dict(
        showgrid=True, gridcolor=COLORS["grid"], gridwidth=1, zeroline=False,
        showline=False, ticks="", tickfont=dict(size=12, color=COLORS["muted"]),
        title=dict(font=dict(size=12, color=COLORS["muted"]), standoff=8),
        automargin=True,
    )
    layout = go.Layout(
            font=dict(family=FONT_STACK, size=12, color=COLORS["text"]),
            colorway=COLORWAY,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=8, t=16, b=8),
            xaxis={**axis, "showgrid": False},
            yaxis=dict(**axis),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                        font=dict(size=12, color=COLORS["muted"]), title=dict(text="")),
            hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=COLORS["border"],
                            font=dict(family=FONT_STACK, size=12, color=COLORS["text"])),
            hovermode="closest",
            bargap=0.28,
            colorscale=dict(sequential=[[0, "#EEF0E6"], [1, COLORS["primary"]]]),
        )
    try:  # rounded bars need Plotly >= 6.1; older versions simply skip this
        layout.update(barcornerradius=10)
    except ValueError:
        pass
    return go.layout.Template(layout=layout)


def register_plotly_template() -> None:
    pio.templates["retailpulse"] = _build_template()
    pio.templates.default = "retailpulse"


def apply_theme() -> None:
    """Call once from app.py, before the page runs."""
    register_plotly_template()
    css = (ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    # The marker lets the stylesheet hide this element's (empty) container.
    st.html(f"<style>{css}</style><span class='rp-inject'></span>")
