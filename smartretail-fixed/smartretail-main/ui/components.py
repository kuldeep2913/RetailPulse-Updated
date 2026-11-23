"""Reusable UI building blocks (header, KPI cards, cards, tables, insight cards...)."""
from __future__ import annotations

from contextlib import contextmanager
from html import escape

import pandas as pd
import streamlit as st

from core.config import ABC_COLORS, SEGMENT_COLORS, SHOW_ROLL_NUMBERS, TEAM
from ui.format import money, money_full, number, signed_pct


def icon(name: str, cls: str = "") -> str:
    """Material Symbols icon (the font ships with Streamlit)."""
    return f'<span class="rp-icon {cls}" aria-hidden="true">{name}</span>'


# --------------------------------------------------------------------------
# Page structure
# --------------------------------------------------------------------------
def page_header(title: str, subtitle: str) -> None:
    st.session_state["_rp_card_n"] = 0
    st.html(
        f'<div class="rp-page-header"><h1>{escape(title)}</h1>'
        f'<p>{escape(subtitle)}</p></div>'
    )


def section(title: str, subtitle: str = "", anchor: str = "") -> None:
    sub = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    aid = f' id="{escape(anchor)}"' if anchor else ""
    st.html(f'<div class="rp-section"{aid}><h2>{escape(title)}</h2>{sub}</div>')


@contextmanager
def card(title: str = "", subtitle: str = "", right: str = ""):
    """A white rounded card. Use as `with card("Title"): st.plotly_chart(...)`."""
    n = st.session_state.get("_rp_card_n", 0)
    st.session_state["_rp_card_n"] = n + 1
    with st.container(border=True, key=f"rp-card-{n}"):
        if title:
            sub = f"<p>{escape(subtitle)}</p>" if subtitle else ""
            tag = f'<span class="rp-card-tag">{escape(right)}</span>' if right else ""
            st.html(f'<div class="rp-card-head"><div><h3>{escape(title)}</h3>{sub}</div>{tag}</div>')
        yield


def empty_state(title: str, message: str, name: str = "search_off") -> None:
    st.html(
        f'<div class="rp-empty">{icon(name)}<h3>{escape(title)}</h3><p>{escape(message)}</p></div>'
    )


def note(text: str) -> None:
    st.html(f'<p class="rp-note">{escape(text)}</p>')


def badge(text: str, kind: str = "neutral") -> str:
    return f'<span class="rp-badge rp-badge-{kind}">{escape(str(text))}</span>'


# --------------------------------------------------------------------------
# KPI cards
# --------------------------------------------------------------------------
def kpi_cards(items: list[dict]) -> None:
    """items: dict(label, value, icon, full=None, delta=None, hint="")."""
    cells = []
    for n, it in enumerate(items):
        delta = it.get("delta")
        tone = it.get("tone") or ["dark", "lime", "", ""][n % 4]
        foot = ""
        if delta is not None:
            tone = "up" if delta >= 0 else "down"
            arrow = "arrow_upward" if delta >= 0 else "arrow_downward"
            foot = (f'<div class="rp-kpi-foot"><span class="rp-delta {tone}">{icon(arrow)}'
                    f'{abs(delta):.1f}%</span><span class="rp-kpi-hint">{escape(it.get("hint", "vs previous period"))}</span></div>')
        elif it.get("hint"):
            foot = f'<div class="rp-kpi-foot"><span class="rp-kpi-hint">{escape(it["hint"])}</span></div>'
        title = escape(it.get("full") or str(it["value"]))
        cells.append(
            f'<div class="rp-kpi tone-{tone}"><div class="rp-kpi-top"><span class="rp-kpi-label">{escape(it["label"])}</span>'
            f'<span class="rp-kpi-icon">{icon(it.get("icon", "analytics"))}</span></div>'
            f'<div class="rp-kpi-value" title="{title}">{escape(str(it["value"]))}</div>{foot}</div>'
        )
    st.html(f'<div class="rp-kpis">{"".join(cells)}</div>')


# --------------------------------------------------------------------------
# Insight cards
# --------------------------------------------------------------------------
def highlight_cards(items: list[dict]) -> None:
    """items: dict(label, value, sub="", icon, tone="neutral|positive|warning|negative")."""
    cells = []
    for it in items:
        tone = it.get("tone", "neutral")
        sub = f'<div class="rp-hl-sub">{escape(it["sub"])}</div>' if it.get("sub") else ""
        cells.append(
            f'<div class="rp-hl rp-tone-{tone}"><div class="rp-hl-icon">{icon(it.get("icon", "insights"))}</div>'
            f'<div class="rp-hl-body"><div class="rp-hl-label">{escape(it["label"])}</div>'
            f'<div class="rp-hl-value">{escape(str(it["value"]))}</div>{sub}</div></div>'
        )
    st.html(f'<div class="rp-hl-grid">{"".join(cells)}</div>')


def insight_cards(items: list[dict]) -> None:
    """items: dict(title, body, tag="", tone="neutral|positive|warning|negative")."""
    cells = []
    for it in items:
        tone = it.get("tone", "neutral")
        tag = f'<span class="rp-badge rp-badge-{tone}">{escape(it["tag"])}</span>' if it.get("tag") else ""
        cells.append(
            f'<div class="rp-insight rp-tone-{tone}"><div class="rp-insight-head">{tag}</div>'
            f'<h4>{escape(it["title"])}</h4><p>{escape(it["body"])}</p></div>'
        )
    st.html(f'<div class="rp-insight-grid">{"".join(cells)}</div>')


# --------------------------------------------------------------------------
# Tables (HTML, inside a horizontally scrollable wrapper)
# --------------------------------------------------------------------------
_BADGE_KIND = {"A": "primary", "B": "secondary", "C": "light"}
_SEG_KIND = {"VIP": "primary", "Loyal": "positive", "Regular": "secondary", "At-Risk": "warning"}


def data_table(df: pd.DataFrame, columns: list[tuple], max_rows: int | None = None) -> None:
    """columns: (source column, header, kind, optional format string).

    kind: text | num | badge_abc | badge_segment | flag
    """
    if max_rows:
        df = df.head(max_rows)
    head = "".join(
        f'<th class="{"num" if k == "num" else ""}">{escape(h)}</th>' for _, h, k, *_ in columns
    )
    body = []
    for _, row in df.iterrows():
        cells = []
        for col, _h, kind, *fmt in columns:
            v = row[col]
            if kind == "num":
                text = format(v, fmt[0]) if fmt else str(v)
                cells.append(f'<td class="num">{escape(text)}</td>')
            elif kind == "badge_abc":
                cells.append(f"<td>{badge(v, _BADGE_KIND.get(v, 'neutral'))}</td>")
            elif kind == "badge_segment":
                cells.append(f"<td>{badge(v, _SEG_KIND.get(v, 'neutral'))}</td>")
            elif kind == "flag":
                cells.append(f"<td>{badge('Low sales', 'warning') if bool(v) else ''}</td>")
            else:
                cells.append(f'<td title="{escape(str(v))}">{escape(str(v))}</td>')
        body.append(f'<tr>{"".join(cells)}</tr>')
    st.html(
        f'<div class="rp-table-wrap"><table class="rp-table"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


# --------------------------------------------------------------------------
# Footer / team
# --------------------------------------------------------------------------
def _initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    return "".join(p[0] for p in parts[:2]).upper()


def team_section() -> None:
    cards = []
    for m in TEAM:
        roll = (f'<div class="rp-team-roll">Roll No. {escape(m["roll_no"])}</div>'
                if SHOW_ROLL_NUMBERS and m.get("roll_no") else "")
        cards.append(
            f'<div class="rp-team-card"><div class="rp-avatar">{escape(_initials(m["name"]))}</div>'
            f'<div><div class="rp-team-name">{escape(m["name"])}</div>{roll}</div></div>'
        )
    st.html(
        '<div class="rp-team"><div class="rp-team-head"><h3>Project Team</h3>'
        '<p>RetailPulse is our B.Tech Computer Science Engineering capstone project.</p></div>'
        f'<div class="rp-team-grid">{"".join(cards)}</div></div>'
    )


def footer() -> None:
    st.html('<div class="rp-footer">RetailPulse &middot; B.Tech CSE Capstone Project</div>')


# --------------------------------------------------------------------------
# Overview hero cards
# --------------------------------------------------------------------------
def _delta(delta, hint: str = "") -> str:
    if delta is None:
        return f'<span class="rp-kpi-hint">{escape(hint)}</span>' if hint else ""
    tone, arrow = ("up", "arrow_upward") if delta >= 0 else ("down", "arrow_downward")
    return (f'<span class="rp-delta {tone}">{icon(arrow)}{abs(delta):.1f}%</span>'
            f'<span class="rp-kpi-hint">{escape(hint)}</span>')


def hero_revenue(revenue: float, monthly: pd.DataFrame, delta=None, hint: str = "") -> str:
    """Dark card: total revenue with one mini bar per month (peak month in lime, partial months dashed)."""
    vals = list(monthly["Revenue"])
    mx = max(vals) or 1
    full = monthly.loc[~monthly["Partial"], "Revenue"]
    peak = int(monthly.index.get_loc(full.idxmax())) if len(full) else -1
    bars = []
    for i, (v, part) in enumerate(zip(vals, monthly["Partial"])):
        cls = "p" if part else "l" if i == peak else "v" if peak - 2 <= i < peak else ""
        bars.append(f'<b class="{cls}" title="{escape(str(monthly["Label"].iloc[i]))}: {escape(money_full(v))}" '
                    f'style="height:{max(5, v / mx * 100):.0f}%"></b>')
    pill = f'<span class="rp-pill">Peak: {escape(str(monthly["Label"].iloc[peak]))}</span>' if peak >= 0 else ""
    foot = f'<div class="rp-kpi-foot">{_delta(delta, hint)}</div>' if delta is not None else ""
    return (f'<div class="rp-kpi tone-dark"><div class="rp-kpi-row"><span class="rp-kpi-label">Total revenue</span>{pill}</div>'
            f'<div class="rp-kpi-value" title="{escape(money_full(revenue))}">{escape(money(revenue))}</div>{foot}'
            f'<div class="rp-mini">{"".join(bars)}</div>'
            f'<div class="rp-axis"><span>{escape(str(monthly["Label"].iloc[0]))}</span>'
            f'<span>{escape(str(monthly["Label"].iloc[-1]))}{" (partial)" if bool(monthly["Partial"].iloc[-1]) else ""}</span></div></div>')


def hero_aov(aov: float, orders: int, ma7, delta=None, hint: str = "") -> str:
    """Lime card: average order value with a revenue sparkline."""
    s = [float(v) for v in ma7]
    step = max(1, len(s) // 36)
    s = [sum(s[i:i + step]) / len(s[i:i + step]) for i in range(0, len(s), step)] or [0.0]
    lo, hi = min(s), max(s)
    span = (hi - lo) or 1
    # Plain CSS bars: st.html strips inline <svg>, so the sparkline is drawn with divs.
    bars = "".join(f'<b style="height:{12 + (v - lo) / span * 88:.0f}%"></b>' for v in s)
    foot = f'<div class="rp-kpi-foot">{_delta(delta, hint)}</div>' if delta is not None else ""
    return (f'<div class="rp-kpi tone-lime"><span class="rp-kpi-label">Average order value</span>'
            f'<div class="rp-kpi-value">{escape(money_full(aov, 2))}</div>{foot}'
            f'<div class="rp-spark" aria-hidden="true">{bars}</div><b>{escape(number(orders))} orders</b></div>')


def hero_customers(customers: int, seg: pd.DataFrame, returning: float) -> str:
    """White card: total customers with a segment split bar and legend."""
    seg = seg.set_index("CustomerSegment").reindex([s for s in SEGMENT_COLORS if s in set(seg["CustomerSegment"])])
    total = seg["Customers"].sum() or 1
    bar = "".join(f'<i style="width:{n / total * 100:.2f}%;background:{SEGMENT_COLORS[s]}"></i>' for s, n in seg["Customers"].items())
    leg = "".join(f'<span><i style="background:{SEGMENT_COLORS[s]}"></i>{escape(s)} {escape(number(n))}</span>'
                  for s, n in seg["Customers"].items())
    return (f'<div class="rp-kpi"><div class="rp-kpi-row"><span class="rp-kpi-label">Total customers</span>'
            f'<span class="rp-pill soft">{returning * 100:.1f}% returning</span></div>'
            f'<div class="rp-kpi-value">{escape(number(customers))}</div>'
            f'<div style="flex:1"></div><div class="rp-segbar" style="margin-top:1.1rem">{bar}</div><div class="rp-legend">{leg}</div></div>')


def hero_row(cards: list[str]) -> None:
    st.html(f'<div class="rp-hero">{"".join(cards)}</div>')


def forecast_card(total: float, growth, peak_day: str, days: int) -> None:
    pill = f'<span class="rp-pill dark">{escape(signed_pct(growth))} daily avg</span>' if growth is not None else ""
    st.html(f'<div class="rp-forecast"><span class="rp-kpi-label" style="color:#55507A">Forecasted revenue, next {days} days</span>'
            f'<div class="big">{escape(money(total))}</div><div style="flex:1;min-height:3rem"></div>{pill}'
            f'<p>vs last 90 days of actual sales. Peak day {escape(peak_day)}.</p></div>')
