"""Number and text formatting helpers shared by every page."""
from __future__ import annotations

from core.config import CURRENCY


def compact(value: float) -> str:
    """12,345,678 -> 12.35M, 12,345 -> 12.3K."""
    sign = "-" if value < 0 else ""
    v = abs(value)
    if v >= 1e9:
        return f"{sign}{v / 1e9:.2f}B"
    if v >= 1e6:
        return f"{sign}{v / 1e6:.2f}M"
    if v >= 1e4:
        return f"{sign}{v / 1e3:.1f}K"
    return f"{sign}{v:,.0f}"


def money(value: float, short: bool = True) -> str:
    return f"{CURRENCY} {compact(value) if short else format(value, ',.0f')}"


def money_full(value: float, decimals: int = 0) -> str:
    return f"{CURRENCY} {value:,.{decimals}f}"


def number(value: float) -> str:
    return f"{value:,.0f}"


def pct(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}%"


def signed_pct(value: float, decimals: int = 1) -> str:
    return f"{value:+.{decimals}f}%"


def short_text(text: str, limit: int = 34) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
