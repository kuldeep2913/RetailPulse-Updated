"""Chart builders. Every chart uses the shared 'retailpulse' Plotly template."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.config import (
    ABC_COLORS, COLORS, COLORWAY, CURRENCY, MAP_COUNTRY_FIXES, MAP_COUNTRY_SKIP, SEGMENT_COLORS,
)
from ui.format import compact, short_text

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


def show(fig: go.Figure) -> None:
    """Render a figure with our template (theme=None stops Streamlit overriding it)."""
    st.plotly_chart(fig, theme=None, width="stretch", config=PLOT_CONFIG)
LIGHT_PRIMARY = "#D8CFF7"


def _month_colors(monthly: pd.DataFrame, col: str = "Revenue") -> list[str]:
    """Violet bars, lighter for partial months, lime for the strongest full month."""
    full = monthly.loc[~monthly["Partial"], col]
    peak = full.idxmax() if len(full) else None
    return [LIGHT_PRIMARY if r["Partial"] else COLORS["lime"] if i == peak else COLORS["primary"]
            for i, r in monthly.iterrows()]


def _money_axis(fig: go.Figure, axis: str = "y") -> go.Figure:
    getattr(fig, f"update_{axis}axes")(tickprefix=f"{CURRENCY} ", tickformat=".3~s")
    return fig


def _finish(fig: go.Figure, height: int = 340, **layout) -> go.Figure:
    fig.update_layout(height=height, **layout)
    return fig


# --------------------------------------------------------------------------
# Time series
# --------------------------------------------------------------------------
def daily_revenue(daily: pd.DataFrame, height: int = 340) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Revenue"], mode="lines", name="Daily revenue",
        line=dict(color="#CFCFC4", width=1.2),
        hovertemplate=f"%{{x|%d %b %Y}}<br>Revenue: {CURRENCY} %{{y:,.0f}}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily["Date"], y=daily["MA7"], mode="lines", name="7-day average",
        line=dict(color=COLORS["primary_strong"], width=2),
        fill="tozeroy", fillcolor="rgba(200,242,58,0.16)",
        hovertemplate=f"%{{x|%d %b %Y}}<br>7-day avg: {CURRENCY} %{{y:,.0f}}<extra></extra>",
    ))
    _money_axis(fig)
    return _finish(fig, height, hovermode="x unified")


def monthly_revenue(monthly: pd.DataFrame, height: int = 340) -> go.Figure:
    colors = _month_colors(monthly)
    custom = np.stack([monthly["Orders"], monthly["Coverage"] * 100], axis=-1)
    fig = go.Figure(go.Bar(
        x=monthly["Label"], y=monthly["Revenue"], marker_color=colors,
        text=[compact(v) for v in monthly["Revenue"]], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=COLORS["muted"]), customdata=custom,
        hovertemplate=(f"<b>%{{x}}</b><br>Revenue: {CURRENCY} %{{y:,.0f}}<br>Orders: %{{customdata[0]:,.0f}}"
                       "<br>Month covered: %{customdata[1]:.0f}%<extra></extra>"),
    ))
    _money_axis(fig)
    fig.update_xaxes(type="category", tickangle=-45 if len(monthly) > 8 else 0)
    return _finish(fig, height)


def weekday_revenue(weekday: pd.DataFrame, height: int = 300, label: str = "Revenue") -> go.Figure:
    peak = weekday["Revenue"].idxmax()
    colors = [COLORS["primary_strong"] if i == peak else COLORS["primary"] for i in weekday.index]
    fig = go.Figure(go.Bar(
        x=weekday["Weekday"].str[:3], y=weekday["Revenue"], marker_color=colors,
        text=[compact(v) for v in weekday["Revenue"]], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=COLORS["muted"]), customdata=weekday["Weekday"],
        hovertemplate=f"<b>%{{customdata}}</b><br>{label}: {CURRENCY} %{{y:,.0f}}<extra></extra>",
    ))
    _money_axis(fig)
    return _finish(fig, height)


# --------------------------------------------------------------------------
# Rankings
# --------------------------------------------------------------------------
def hbar(df: pd.DataFrame, label_col: str, value_col: str, height: int | None = None,
         color: str | None = None, label_limit: int = 30, value_name: str = "Revenue",
         money: bool = True) -> go.Figure:
    """Horizontal ranking bar: first row of `df` appears at the top."""
    labels = [short_text(v, label_limit) for v in df[label_col].astype(str)]
    values = df[value_col]
    text = [compact(v) for v in values]
    fmt = f"{CURRENCY} %{{x:,.0f}}" if money else "%{x:,.0f}"
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", marker_color=color or COLORS["primary"],
        text=text, textposition="outside", cliponaxis=False, textfont=dict(size=11, color=COLORS["muted"]),
        customdata=df[label_col].astype(str),
        hovertemplate=f"<b>%{{customdata}}</b><br>{value_name}: {fmt}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False, automargin=True)
    fig.update_xaxes(showgrid=True, tickformat=".3~s", tickprefix=f"{CURRENCY} " if money else "",
                     range=[0, float(values.max()) * 1.18 if len(values) else 1])
    return _finish(fig, height or max(260, 34 * len(df) + 40), bargap=0.35)


def donut(labels, values, colors=None, height: int = 300, center: str = "", sub: str = "",
          value_name: str = "Value", money: bool = False) -> go.Figure:
    colors = colors or COLORWAY[: len(labels)]
    fmt = f"{CURRENCY} %{{value:,.0f}}" if money else "%{value:,.0f}"
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.66, sort=False, direction="clockwise",
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textinfo="none",
        hovertemplate=f"<b>%{{label}}</b><br>{value_name}: {fmt}<br>Share: %{{percent}}<extra></extra>",
    ))
    if center:
        fig.add_annotation(text=f"<b style='font-size:22px'>{center}</b>"
                                f"<br><span style='font-size:12px;color:{COLORS['muted']}'>{sub}</span>",
                           showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")
    return _finish(fig, height, showlegend=True,
                   legend=dict(orientation="h", y=-0.04, x=0.5, xanchor="center", yanchor="top"),
                   margin=dict(l=8, r=8, t=8, b=8))


def histogram(hist: dict, xtitle: str, height: int = 300, money: bool = True,
              ytitle: str = "Number of records") -> go.Figure:
    edges, counts = hist["edges"], hist["counts"]
    mids = (edges[:-1] + edges[1:]) / 2
    width = edges[1] - edges[0]
    prefix = f"{CURRENCY} " if money else ""
    fig = go.Figure(go.Bar(
        x=mids, y=counts, width=width * 0.94, marker_color=COLORS["primary"],
        customdata=np.stack([edges[:-1], edges[1:]], axis=-1),
        hovertemplate=(f"Range: {prefix}%{{customdata[0]:,.0f}} to {prefix}%{{customdata[1]:,.0f}}"
                       "<br>Count: %{y:,.0f}<extra></extra>"),
    ))
    fig.update_xaxes(title_text=xtitle, tickprefix=prefix)
    fig.update_yaxes(title_text=ytitle)
    return _finish(fig, height, bargap=0.05)


# --------------------------------------------------------------------------
# Geography
# --------------------------------------------------------------------------
def country_map(countries: pd.DataFrame, height: int = 380) -> go.Figure:
    df = countries[~countries["Country"].isin(MAP_COUNTRY_SKIP)].copy()
    df["Place"] = df["Country"].replace(MAP_COUNTRY_FIXES)
    fig = go.Figure(go.Choropleth(
        locations=df["Place"], locationmode="country names", z=np.log10(df["Revenue"].clip(lower=1)),
        customdata=np.stack([df["Country"], df["Revenue"], df["Orders"]], axis=-1),
        colorscale=[[0, "#EEF0E6"], [1, COLORS["primary"]]], showscale=False,
        marker_line_color="#FFFFFF", marker_line_width=0.6,
        hovertemplate=(f"<b>%{{customdata[0]}}</b><br>Revenue: {CURRENCY} %{{customdata[1]:,.0f}}"
                       "<br>Orders: %{customdata[2]:,.0f}<extra></extra>"),
    ))
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth",
                    bgcolor="rgba(0,0,0,0)", landcolor="#F1F4F8", showcountries=False,
                    lataxis_range=[-58, 85])
    return _finish(fig, height, margin=dict(l=0, r=0, t=0, b=0))


# --------------------------------------------------------------------------
# Customers
# --------------------------------------------------------------------------
def segment_donut(seg: pd.DataFrame, height: int = 300) -> go.Figure:
    seg = seg.set_index("CustomerSegment").reindex(
        [s for s in SEGMENT_COLORS if s in set(seg["CustomerSegment"])]).reset_index()
    from core.config import SEGMENT_ORDER
    seg = seg.set_index("CustomerSegment").reindex(
        [s for s in SEGMENT_ORDER if s in set(seg["CustomerSegment"])]).reset_index()
    colors = [SEGMENT_COLORS.get(s, COLORS["secondary"]) for s in seg["CustomerSegment"]]
    return donut(seg["CustomerSegment"], seg["Customers"], colors, height,
                 center=f"{int(seg['Customers'].sum()):,}", sub="customers", value_name="Customers")


def cluster_bar(clusters: pd.DataFrame, height: int = 300) -> go.Figure:
    fig = go.Figure(go.Bar(
        x="Cluster " + clusters["Cluster"], y=clusters["Customers"], marker_color=COLORWAY[: len(clusters)],
        text=[f"{v:,}" for v in clusters["Customers"]], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=COLORS["muted"]),
        hovertemplate="<b>%{x}</b><br>Customers: %{y:,.0f}<extra></extra>",
    ))
    fig.update_yaxes(title_text="Customers")
    return _finish(fig, height)


def revenue_share_bar(seg: pd.DataFrame, height: int = 300) -> go.Figure:
    colors = [SEGMENT_COLORS.get(s, COLORS["secondary"]) for s in seg["CustomerSegment"]]
    fig = go.Figure(go.Bar(
        x=seg["CustomerSegment"], y=seg["RevenueShare"], marker_color=colors,
        text=[f"{v:.1f}%" for v in seg["RevenueShare"]], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=COLORS["muted"]), customdata=seg["Revenue"],
        hovertemplate=(f"<b>%{{x}}</b><br>Share of customer spend: %{{y:.1f}}%"
                       f"<br>Total spend: {CURRENCY} %{{customdata:,.0f}}<extra></extra>"),
    ))
    fig.update_yaxes(ticksuffix="%", title_text="Share of total spend")
    return _finish(fig, height)


def rfm_scatter(rfm: pd.DataFrame, x: str, height: int = 380) -> go.Figure:
    fig = go.Figure()
    for seg in [s for s in SEGMENT_COLORS if s in set(rfm["CustomerSegment"])]:
        sub = rfm[rfm["CustomerSegment"] == seg]
        fig.add_trace(go.Scatter(
            x=sub[x], y=sub["Monetary"], mode="markers", name=seg,
            marker=dict(color=SEGMENT_COLORS[seg], size=6, opacity=0.7, line=dict(width=0)),
            customdata=np.stack([sub["CustomerID"].astype(int), sub["Recency"], sub["Frequency"]], axis=-1),
            hovertemplate=(f"<b>Customer %{{customdata[0]}}</b> ({seg})<br>Recency: %{{customdata[1]:,.0f}} days"
                           f"<br>Frequency: %{{customdata[2]:,.0f}}<br>Monetary: {CURRENCY} %{{y:,.0f}}<extra></extra>"),
        ))
    fig.update_xaxes(title_text=f"{x}" + (" (days)" if x == "Recency" else " (orders)"), showgrid=True)
    fig.update_yaxes(title_text="Monetary value (log scale)", type="log", tickprefix=f"{CURRENCY} ")
    return _finish(fig, height)


def trend_forecast(daily: pd.DataFrame, fb: dict | None = None, height: int = 340) -> go.Figure:
    """Daily revenue (7-day average) with the forecast and its confidence band appended when available."""
    fig = go.Figure()
    last = daily["Date"].max()
    ma_last = float(daily["MA7"].iloc[-1])
    future = fb["future"] if fb is not None else None
    if future is not None and not future.empty:
        sm = future[["yhat", "yhat_lower", "yhat_upper"]].rolling(7, min_periods=1).mean()
        xs = [last] + list(future["ds"])
        fig.add_trace(go.Scatter(x=xs, y=[ma_last] + list(sm["yhat_upper"]), mode="lines", line=dict(width=0),
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=xs, y=[ma_last] + list(sm["yhat_lower"]), mode="lines", line=dict(width=0),
                                 fill="tonexty", fillcolor="rgba(143,132,224,0.2)", name="Confidence interval",
                                 hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=xs, y=[ma_last] + list(sm["yhat"]), mode="lines", name="Forecast",
            line=dict(color=COLORS["primary"], width=2.2, dash="dash"),
            hovertemplate=f"%{{x|%d %b %Y}}<br>Forecast (7-day avg): {CURRENCY} %{{y:,.0f}}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Revenue"], mode="lines", name="Daily revenue", line=dict(color="#CFCFC4", width=1.1),
        hovertemplate=f"%{{x|%d %b %Y}}<br>Revenue: {CURRENCY} %{{y:,.0f}}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=daily["Date"], y=daily["MA7"], mode="lines", name="Actual (7-day average)",
        line=dict(color=COLORS["primary_strong"], width=2), fill="tozeroy", fillcolor="rgba(200,242,58,0.16)",
        hovertemplate=f"%{{x|%d %b %Y}}<br>7-day avg: {CURRENCY} %{{y:,.0f}}<extra></extra>"))
    if future is not None and not future.empty:
        x0 = last.to_pydatetime()
        fig.add_shape(type="line", x0=x0, x1=x0, y0=0, y1=1, xref="x", yref="paper",
                      line=dict(color=COLORS["muted"], width=1, dash="dot"))
        fig.add_annotation(x=x0, y=1, xref="x", yref="paper", text="Forecast starts", showarrow=False,
                           xanchor="left", yanchor="bottom", xshift=6, font=dict(size=11, color=COLORS["muted"]))
    _money_axis(fig)
    return _finish(fig, height, hovermode="x unified", margin=dict(l=8, r=8, t=28, b=8))


# --------------------------------------------------------------------------
# Forecast
# --------------------------------------------------------------------------
def forecast_chart(fb: dict, window_days: int | None = None, height: int = 440) -> go.Figure:
    actual, history, future = fb["actual"], fb["history"], fb["future"]
    last = fb["last_actual"]
    if window_days:
        cutoff = last - pd.Timedelta(days=window_days)
        actual, history = actual[actual["Date"] >= cutoff], history[history["ds"] >= cutoff]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=future["ds"], y=future["yhat_upper"], mode="lines", line=dict(width=0),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=future["ds"], y=future["yhat_lower"], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(143,132,224,0.2)", name="Confidence interval",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=actual["Date"], y=actual["Revenue"], mode="lines", name="Historical sales",
        line=dict(color=COLORS["text"], width=1.3), opacity=0.9,
        hovertemplate=f"%{{x|%d %b %Y}}<br>Actual: {CURRENCY} %{{y:,.0f}}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=history["ds"], y=history["yhat"], mode="lines", name="Model fit (history)",
        line=dict(color=COLORS["secondary"], width=1.6), visible="legendonly",
        hovertemplate=f"%{{x|%d %b %Y}}<br>Model fit: {CURRENCY} %{{y:,.0f}}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=future["ds"], y=future["yhat"], mode="lines", name="Forecast",
        line=dict(color=COLORS["primary"], width=2.2, dash="dash"),
        customdata=np.stack([future["yhat_lower"], future["yhat_upper"]], axis=-1),
        hovertemplate=(f"%{{x|%d %b %Y}}<br>Forecast: {CURRENCY} %{{y:,.0f}}"
                       f"<br>Range: {CURRENCY} %{{customdata[0]:,.0f}} to {CURRENCY} %{{customdata[1]:,.0f}}<extra></extra>"),
    ))
    x0 = (last + pd.Timedelta(days=1)).to_pydatetime()
    fig.add_shape(type="line", x0=x0, x1=x0, y0=0, y1=1, xref="x", yref="paper",
                  line=dict(color=COLORS["secondary"], width=1, dash="dot"))
    fig.add_annotation(x=x0, y=1, xref="x", yref="paper", text="Forecast starts", showarrow=False,
                       xanchor="left", yanchor="bottom", xshift=6, font=dict(size=11, color=COLORS["muted"]))
    _money_axis(fig)
    return _finish(fig, height, hovermode="x unified", margin=dict(l=8, r=8, t=28, b=8))


def next_days_chart(future: pd.DataFrame, days: int = 30, height: int = 320) -> go.Figure:
    nxt = future.head(days)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=nxt["ds"], y=nxt["yhat"], marker_color=COLORS["primary"], name="Forecast",
        error_y=dict(type="data", symmetric=False, array=nxt["yhat_upper"] - nxt["yhat"],
                     arrayminus=nxt["yhat"] - nxt["yhat_lower"], color="#A9B7CE", thickness=1, width=2),
        hovertemplate=f"%{{x|%a %d %b}}<br>Forecast: {CURRENCY} %{{y:,.0f}}<extra></extra>",
    ))
    _money_axis(fig)
    fig.update_xaxes(tickformat="%d %b")
    return _finish(fig, height, showlegend=False, bargap=0.2)


def monthly_forecast(monthly: pd.DataFrame, height: int = 320) -> go.Figure:
    colors = _month_colors(monthly)
    custom = np.stack([monthly["Days"], monthly["DaysInMonth"]], axis=-1)
    fig = go.Figure(go.Bar(
        x=monthly["Month"], y=monthly["Revenue"], marker_color=colors,
        text=[compact(v) for v in monthly["Revenue"]], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=COLORS["muted"]), customdata=custom,
        hovertemplate=(f"<b>%{{x}}</b><br>Forecast revenue: {CURRENCY} %{{y:,.0f}}"
                       "<br>Days forecast: %{customdata[0]} of %{customdata[1]}<extra></extra>"),
    ))
    _money_axis(fig)
    return _finish(fig, height)


# --------------------------------------------------------------------------
# Inventory
# --------------------------------------------------------------------------
def pareto(inv: pd.DataFrame, height: int = 340) -> go.Figure:
    n = len(inv)
    x = inv["Rank"] / n * 100
    y = inv["Cumulative"] * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", line=dict(color=COLORS["primary_strong"], width=2.6),
        fill="tozeroy", fillcolor="rgba(100,127,168,0.14)", name="Cumulative revenue",
        customdata=np.stack([inv["Rank"], inv["ABC"]], axis=-1),
        hovertemplate=("Top %{x:.1f}% of products (rank %{customdata[0]})<br>"
                       "Cumulative revenue: %{y:.1f}%<br>Class: %{customdata[1]}<extra></extra>"),
    ))
    for level, label in ((80, "80% (A / B boundary)"), (95, "95% (B / C boundary)")):
        fig.add_hline(y=level, line=dict(color=COLORS["secondary"], width=1, dash="dot"),
                      annotation_text=label, annotation_position="bottom right",
                      annotation_font=dict(size=11, color=COLORS["muted"]))
    fig.update_xaxes(title_text="Products ranked by revenue (%)", ticksuffix="%", range=[0, 100])
    fig.update_yaxes(title_text="Cumulative revenue", ticksuffix="%", range=[0, 102])
    return _finish(fig, height, showlegend=False)


def abc_bars(abc: pd.DataFrame, height: int = 300) -> go.Figure:
    fig = go.Figure(go.Bar(
        x="Class " + abc["ABC"], y=abc["RevenueShare"], marker_color=[ABC_COLORS[c] for c in abc["ABC"]],
        text=[f"{v:.1f}%" for v in abc["RevenueShare"]], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=COLORS["muted"]),
        customdata=np.stack([abc["Products"], abc["ProductShare"], abc["Revenue"]], axis=-1),
        hovertemplate=(f"<b>%{{x}}</b><br>Revenue share: %{{y:.1f}}%<br>Products: %{{customdata[0]:,.0f}}"
                       f" (%{{customdata[1]:.1f}}% of catalogue)<br>Revenue: {CURRENCY} %{{customdata[2]:,.0f}}<extra></extra>"),
    ))
    fig.update_yaxes(ticksuffix="%", title_text="Share of revenue", range=[0, 100])
    return _finish(fig, height, bargap=0.4)
