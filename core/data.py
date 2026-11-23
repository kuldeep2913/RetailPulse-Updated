"""Data loading and aggregation.

All calculations here are the ones the original pages performed inline
(sum of TotalPrice, distinct invoices, groupbys, ABC thresholds, ...). They are
gathered in one place, cached, and computed once per filter combination.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from core.config import (
    FORECAST_CSV, SEGMENTS_CSV, TRANSACTIONS_CSV, WEEKDAYS,
)


# --------------------------------------------------------------------------
# Raw loaders
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading transaction data...")
def load_transactions() -> pd.DataFrame:
    """Cleaned transactions. Shared (not copied) between runs: never mutate it."""
    df = pd.read_csv(
        TRANSACTIONS_CSV,
        usecols=["InvoiceNo", "Description", "Quantity", "InvoiceDate",
                 "CustomerID", "Country", "TotalPrice"],
        dtype={"InvoiceNo": "string"},
        parse_dates=["InvoiceDate"],
    )
    df["Date"] = df["InvoiceDate"].dt.normalize()
    return df


@st.cache_data(show_spinner=False)
def load_segments() -> pd.DataFrame:
    """RFM table with K-Means cluster and customer segment (precomputed)."""
    return pd.read_csv(SEGMENTS_CSV)


@st.cache_data(show_spinner=False)
def load_forecast() -> pd.DataFrame:
    """Prophet output (precomputed in the Demand_Forecasting notebook)."""
    df = pd.read_csv(FORECAST_CSV)
    df["ds"] = pd.to_datetime(df["ds"])
    return df


# --------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Filters:
    start: date
    end: date
    countries: tuple = ()          # empty tuple means "all countries"
    label: str = "All time"

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


@st.cache_data(show_spinner=False)
def data_bounds() -> tuple[date, date]:
    df = load_transactions()
    return df["Date"].min().date(), df["Date"].max().date()


@st.cache_data(show_spinner=False)
def country_options() -> list[str]:
    """Countries ordered by revenue (largest first)."""
    df = load_transactions()
    return df.groupby("Country")["TotalPrice"].sum().sort_values(ascending=False).index.tolist()


def _subset(f: Filters) -> pd.DataFrame:
    df = load_transactions()
    mask = (df["Date"] >= pd.Timestamp(f.start)) & (df["Date"] <= pd.Timestamp(f.end))
    if f.countries:
        mask &= df["Country"].isin(f.countries)
    return df[mask]


# --------------------------------------------------------------------------
# KPI helpers
# --------------------------------------------------------------------------
def _kpis(df: pd.DataFrame) -> dict:
    revenue = float(df["TotalPrice"].sum())
    orders = int(df["InvoiceNo"].nunique())
    return {
        "revenue": revenue,
        "orders": orders,
        "customers": int(df["CustomerID"].nunique()),
        "aov": revenue / orders if orders else 0.0,
        "products": int(df["Description"].nunique()),
        "countries": int(df["Country"].nunique()),
        "units": int(df["Quantity"].sum()),
    }


def _pct_change(cur: float, prev: float):
    return (cur - prev) / prev * 100 if prev else None


@st.cache_data(show_spinner=False)
def previous_period_deltas(start: date, end: date, countries: tuple) -> dict | None:
    """% change versus the immediately preceding window of equal length.

    Returns None unless that previous window lies completely inside the data,
    so a change is only ever shown when it can be calculated accurately.
    """
    data_min, _ = data_bounds()
    length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length - 1)
    if prev_start < data_min:
        return None
    cur = _kpis(_subset(Filters(start, end, countries)))
    prev_df = _subset(Filters(prev_start, prev_end, countries))
    if prev_df.empty:
        return None
    prev = _kpis(prev_df)
    return {k: _pct_change(cur[k], prev[k]) for k in ("revenue", "orders", "customers", "aov")}


# --------------------------------------------------------------------------
# Sales bundle (Overview, Sales Analytics, AI Insights)
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def sales_bundle(start: date, end: date, countries: tuple) -> dict | None:
    df = _subset(Filters(start, end, countries))
    if df.empty:
        return None

    kpis = _kpis(df)

    daily = df.groupby("Date")["TotalPrice"].sum().rename("Revenue").reset_index()
    full_days = pd.date_range(daily["Date"].min(), daily["Date"].max(), freq="D")
    daily_full = daily.set_index("Date")["Revenue"].reindex(full_days, fill_value=0.0)
    daily["MA7"] = daily_full.rolling(7, min_periods=1).mean().reindex(daily["Date"]).to_numpy()

    # Monthly revenue; months only partly covered by the selected window are flagged.
    m = df.assign(Month=df["Date"].dt.to_period("M"))
    monthly = m.groupby("Month").agg(Revenue=("TotalPrice", "sum"),
                                     Orders=("InvoiceNo", "nunique")).reset_index()
    win_start, win_end = df["Date"].min().normalize(), df["Date"].max().normalize()
    coverage = []
    for p in monthly["Month"]:
        s, e = max(p.start_time.normalize(), win_start), min(p.end_time.normalize(), win_end)
        coverage.append(((e - s).days + 1) / p.days_in_month)
    monthly["Coverage"] = coverage
    monthly["Partial"] = monthly["Coverage"] < 0.97
    monthly["Label"] = monthly["Month"].dt.strftime("%b %Y")
    monthly = monthly.drop(columns="Month")

    weekday = (df.groupby(df["Date"].dt.day_name())["TotalPrice"].sum()
                 .reindex(WEEKDAYS).fillna(0).rename("Revenue").rename_axis("Weekday").reset_index())

    country_all = (df.groupby("Country").agg(Revenue=("TotalPrice", "sum"),
                                              Orders=("InvoiceNo", "nunique"))
                     .sort_values("Revenue", ascending=False).reset_index())
    products_all = (df.groupby("Description").agg(Revenue=("TotalPrice", "sum"),
                                                   Quantity=("Quantity", "sum"))
                      .sort_values("Revenue", ascending=False).reset_index())
    customers_all = (df.groupby("CustomerID").agg(Revenue=("TotalPrice", "sum"),
                                                   Orders=("InvoiceNo", "nunique"))
                       .sort_values("Revenue", ascending=False).reset_index())
    customers_all["CustomerID"] = customers_all["CustomerID"].astype(int)

    # Order-value distribution (computed server side; clipped at the 99th percentile for readability)
    values = df["TotalPrice"].to_numpy()
    cap = float(np.percentile(values, 99))
    counts, edges = np.histogram(values[values <= cap], bins=40)

    orders_per_customer = df.groupby("CustomerID")["InvoiceNo"].nunique()
    returning_share = float((orders_per_customer > 1).mean()) if len(orders_per_customer) else 0.0
    top10_share = float(customers_all["Revenue"].head(max(1, len(customers_all) // 10)).sum()
                        / kpis["revenue"]) if kpis["revenue"] else 0.0

    hi_day = daily.loc[daily["Revenue"].idxmax()]
    lo_day = daily.loc[daily["Revenue"].idxmin()]

    return {
        "kpis": kpis,
        "daily": daily,
        "monthly": monthly,
        "weekday": weekday,
        "countries": country_all,
        "products": products_all,
        "customers": customers_all,
        "hist": {"edges": edges, "counts": counts, "cap": cap},
        "facts": {
            "best_country": country_all.iloc[0]["Country"],
            "best_country_share": float(country_all.iloc[0]["Revenue"] / kpis["revenue"]) if kpis["revenue"] else 0.0,
            "best_product": products_all.iloc[0]["Description"],
            "best_customer": int(customers_all.iloc[0]["CustomerID"]),
            "best_customer_revenue": float(customers_all.iloc[0]["Revenue"]),
            "top10_products_share": float(products_all["Revenue"].head(10).sum() / kpis["revenue"]) if kpis["revenue"] else 0.0,
            "high_day": hi_day["Date"].date(), "high_day_revenue": float(hi_day["Revenue"]),
            "low_day": lo_day["Date"].date(), "low_day_revenue": float(lo_day["Revenue"]),
            "max_line": float(values.max()), "min_line": float(values.min()),
            "returning_share": returning_share,
            "top_decile_share": top10_share,
            "peak_month": monthly.loc[monthly["Revenue"].idxmax(), "Label"],
            "peak_month_revenue": float(monthly["Revenue"].max()),
            "records": int(len(df)),
        },
    }


# --------------------------------------------------------------------------
# Customer segmentation
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def customer_bundle(segments: tuple, clusters: tuple) -> dict | None:
    rfm = load_segments()
    rfm = rfm[rfm["CustomerSegment"].isin(segments) & rfm["Cluster"].isin(clusters)]
    if rfm.empty:
        return None

    total_monetary = rfm["Monetary"].sum()
    seg = (rfm.groupby("CustomerSegment")
              .agg(Customers=("CustomerID", "count"), AvgRecency=("Recency", "mean"),
                   AvgFrequency=("Frequency", "mean"), AvgMonetary=("Monetary", "mean"),
                   Revenue=("Monetary", "sum"))
              .reset_index())
    seg["CustomerShare"] = seg["Customers"] / seg["Customers"].sum() * 100
    seg["RevenueShare"] = seg["Revenue"] / total_monetary * 100 if total_monetary else 0.0

    cluster = (rfm.groupby("Cluster")
                  .agg(Customers=("CustomerID", "count"), Recency=("Recency", "mean"),
                       Frequency=("Frequency", "mean"), Monetary=("Monetary", "mean"))
                  .round(2).reset_index())
    cluster["Cluster"] = cluster["Cluster"].astype(str)

    return {
        "rfm": rfm,
        "kpis": {
            "customers": int(rfm["CustomerID"].nunique()),
            "recency": float(rfm["Recency"].mean()),
            "frequency": float(rfm["Frequency"].mean()),
            "monetary": float(rfm["Monetary"].mean()),
        },
        "segments": seg,
        "clusters": cluster,
        "top20": rfm.sort_values("Monetary", ascending=False).head(20).assign(
            CustomerID=lambda d: d["CustomerID"].astype(int)),
    }


# --------------------------------------------------------------------------
# Demand forecast
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def forecast_bundle() -> dict:
    fc = load_forecast()
    tx = load_transactions()
    last_actual = tx["Date"].max()
    actual = tx.groupby("Date")["TotalPrice"].sum().rename("Revenue").reset_index()
    history = fc[fc["ds"] <= last_actual]
    future = fc[fc["ds"] > last_actual].reset_index(drop=True)

    recent = actual[actual["Date"] > last_actual - pd.Timedelta(days=90)]
    recent_avg = float(
        recent["Revenue"].sum() / 90  # average per calendar day over the last 90 days
    )

    monthly_rows = []
    for period, grp in future.groupby(future["ds"].dt.to_period("M")):
        monthly_rows.append({
            "Month": period.strftime("%b %Y"),
            "Revenue": float(grp["yhat"].sum()),
            "Days": int(len(grp)),
            "DaysInMonth": int(period.days_in_month),
        })
    monthly = pd.DataFrame(monthly_rows)
    monthly["Partial"] = monthly["Days"] < monthly["DaysInMonth"]

    weekday = (future.groupby(future["ds"].dt.day_name())["yhat"].mean()
                     .reindex(WEEKDAYS).rename("Revenue").rename_axis("Weekday").reset_index())

    return {
        "forecast": fc,
        "history": history,
        "future": future,
        "actual": actual,
        "last_actual": last_actual,
        "recent_avg_daily": recent_avg,
        "monthly": monthly,
        "weekday": weekday,
    }


# --------------------------------------------------------------------------
# Inventory (product level) with ABC classification
# --------------------------------------------------------------------------
def abc_class(cumulative_share: float) -> str:
    """Thresholds carried over from the original implementation (80% / 95%)."""
    if cumulative_share <= 0.80:
        return "A"
    if cumulative_share <= 0.95:
        return "B"
    return "C"


@st.cache_data(show_spinner=False)
def inventory_bundle(start: date, end: date, countries: tuple) -> dict | None:
    df = _subset(Filters(start, end, countries))
    if df.empty:
        return None

    inv = (df.groupby("Description")
             .agg(Quantity=("Quantity", "sum"), Revenue=("TotalPrice", "sum"),
                  Orders=("InvoiceNo", "nunique"))
             .reset_index()
             .sort_values("Revenue", ascending=False)
             .reset_index(drop=True))
    total_revenue = inv["Revenue"].sum()
    inv["RevenueShare"] = inv["Revenue"] / total_revenue if total_revenue else 0.0
    inv["Cumulative"] = inv["RevenueShare"].cumsum()
    inv["ABC"] = inv["Cumulative"].apply(abc_class)
    inv["Rank"] = np.arange(1, len(inv) + 1)

    abc = (inv.groupby("ABC").agg(Products=("Description", "count"), Revenue=("Revenue", "sum"),
                                  Quantity=("Quantity", "sum")).reindex(["A", "B", "C"]).fillna(0).reset_index())
    abc["ProductShare"] = abc["Products"] / len(inv) * 100
    abc["RevenueShare"] = abc["Revenue"] / total_revenue * 100 if total_revenue else 0.0

    low_cut = float(inv["Quantity"].quantile(0.25))
    inv["LowSales"] = inv["Quantity"] < low_cut

    q = inv["Quantity"].to_numpy()
    cap = float(np.percentile(q, 95))
    counts, edges = np.histogram(q[q <= cap], bins=40)

    return {
        "inventory": inv,
        "abc": abc,
        "kpis": {
            "products": int(len(inv)),
            "quantity": int(inv["Quantity"].sum()),
            "revenue": float(total_revenue),
            "avg_quantity": float(inv["Quantity"].mean()),
        },
        "low_cut": low_cut,
        "hist": {"edges": edges, "counts": counts, "cap": cap},
    }
