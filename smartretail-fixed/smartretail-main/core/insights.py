"""Rule-based insights.

RetailPulse does not call a generative AI model. Every statement below is
produced by explicit rules over the data (thresholds are carried over from the
original implementation where one existed), so each one can be traced back to a
number on screen.
"""
from __future__ import annotations

from ui.format import money, money_full, pct, short_text


def _card(title: str, body: str, tag: str = "", tone: str = "neutral") -> dict:
    return {"title": title, "body": body, "tag": tag, "tone": tone}


# --------------------------------------------------------------------------
# Sales
# --------------------------------------------------------------------------
def sales_recommendations(b: dict) -> list[dict]:
    k, f = b["kpis"], b["facts"]
    out = []
    if k["revenue"] > 8_000_000:
        out.append(_card("Revenue is strong",
                         f"Total revenue of {money(k['revenue'])} is above the 8M benchmark. "
                         "Continue investing in the top-selling products.", "Revenue", "positive"))
    if k["aov"] < 500:
        out.append(_card("Raise the average order value",
                         f"Average order value is {money_full(k['aov'])}. Product bundles and tiered "
                         "discounts can lift basket size.", "Revenue", "warning"))
    if k["customers"] < 5000:
        out.append(_card("Grow the customer base",
                         f"The selection has {k['customers']:,} customers. Targeted acquisition campaigns "
                         "can widen the base.", "Customers", "warning"))
    out.append(_card(f"Focus marketing on {f['best_country']}",
                     f"{f['best_country']} is the strongest market with {pct(f['best_country_share'] * 100)} "
                     "of revenue in this selection.", "Markets", "neutral"))
    out.append(_card("Protect stock of the best seller",
                     f"'{short_text(f['best_product'], 48)}' leads on revenue. Keep enough inventory to avoid stockouts.",
                     "Inventory", "neutral"))
    out.append(_card("Plan inventory with the forecast",
                     "Use the Demand Forecasting page to align purchasing with expected demand.",
                     "Planning", "neutral"))
    return out


# --------------------------------------------------------------------------
# AI Insights page
# --------------------------------------------------------------------------
def business_recommendations(b: dict) -> list[dict]:
    k, f = b["kpis"], b["facts"]
    countries, products = b["countries"], b["products"]
    top3 = ", ".join(countries["Country"].head(3))
    low_cut = products["Quantity"].quantile(0.25)
    low_share = products.loc[products["Quantity"] < low_cut, "Revenue"].sum() / k["revenue"] * 100 if k["revenue"] else 0

    return [
        _card("Expand in the highest-performing markets",
              f"Top markets by revenue: {top3}. {f['best_country']} alone contributes "
              f"{pct(f['best_country_share'] * 100)} of revenue.", "Markets"),
        _card("Maintain stock of top sellers",
              f"The top 10 products generate {pct(f['top10_products_share'] * 100)} of revenue; "
              f"'{short_text(f['best_product'], 44)}' is first.", "Inventory"),
        _card("Reward high-value customers",
              f"The top 10% of customers generate {pct(f['top_decile_share'] * 100)} of revenue. "
              f"Customer {f['best_customer']} alone spent {money(f['best_customer_revenue'])}.", "Customers"),
        _card("Review low-selling products",
              f"Products in the bottom quartile by units sold contribute only {pct(low_share, 2)} of revenue. "
              "Consider discounts, bundles or discontinuation.", "Inventory", "warning"),
        _card("Increase average order value",
              f"Average order value is {money_full(k['aov'])}. Cross-selling and bundles can raise it.",
              "Revenue", "warning" if k["aov"] < 500 else "neutral"),
        _card("Integrate forecasting with inventory planning",
              "Use the Demand Forecasting page to reduce excess stock and avoid shortages.", "Planning"),
        _card("Automate reorder points for fast movers",
              "Set reorder levels for Category A products and review them weekly.", "Inventory"),
        _card("Track KPIs monthly",
              f"Peak month in this selection was {f['peak_month']} ({money(f['peak_month_revenue'])}). "
              "Review the monthly trend to spot changes early.", "Planning"),
    ]


def business_observations(b: dict, customers: dict | None) -> list[dict]:
    """Data-driven strengths and risks (replaces the previous hard-coded SWOT text)."""
    f = b["facts"]
    obs = []
    rr = f["returning_share"] * 100
    obs.append(_card("Repeat purchasing",
                     f"{pct(rr)} of customers placed more than one order in this selection.",
                     "Strength" if rr >= 50 else "Watch", "positive" if rr >= 50 else "warning"))
    share = f["best_country_share"] * 100
    obs.append(_card("Market concentration",
                     f"{f['best_country']} accounts for {pct(share)} of revenue.",
                     "Risk" if share >= 70 else "Balanced", "warning" if share >= 70 else "positive"))
    td = f["top_decile_share"] * 100
    obs.append(_card("Customer concentration",
                     f"The top 10% of customers generate {pct(td)} of revenue.",
                     "Risk" if td >= 50 else "Balanced", "warning" if td >= 50 else "positive"))
    tp = f["top10_products_share"] * 100
    obs.append(_card("Product concentration",
                     f"The top 10 products generate {pct(tp)} of revenue.",
                     "Risk" if tp >= 40 else "Diversified", "warning" if tp >= 40 else "positive"))
    if customers is not None:
        seg = customers["segments"].set_index("CustomerSegment")
        if "At-Risk" in seg.index:
            obs.append(_card("Customers at risk of churning",
                             f"{pct(seg.loc['At-Risk', 'CustomerShare'])} of customers are in the At-Risk segment "
                             f"(average recency {seg.loc['At-Risk', 'AvgRecency']:.0f} days).",
                             "Risk", "warning"))
    return obs


# --------------------------------------------------------------------------
# Customers
# --------------------------------------------------------------------------
def customer_recommendations(c: dict) -> list[dict]:
    seg = c["segments"].set_index("CustomerSegment")
    best = seg["AvgMonetary"].idxmax()
    out = [_card(f"Focus campaigns on {best} customers",
                 f"{best} is the highest-value segment with an average spend of {money_full(seg.loc[best, 'AvgMonetary'])}.",
                 "Priority", "positive")]
    if "Regular" in seg.index:
        out.append(_card("Reward Regular customers",
                         f"{int(seg.loc['Regular', 'Customers']):,} Regular customers average "
                         f"{seg.loc['Regular', 'AvgFrequency']:.1f} orders. Loyalty rewards can raise repeat purchases.",
                         "Retention"))
    if "At-Risk" in seg.index:
        out.append(_card("Re-engage At-Risk customers",
                         f"{int(seg.loc['At-Risk', 'Customers']):,} customers have not purchased for "
                         f"{seg.loc['At-Risk', 'AvgRecency']:.0f} days on average. Personalised email campaigns can win them back.",
                         "Retention", "warning"))
    if "Loyal" in seg.index:
        out.append(_card("Offer premium benefits to Loyal customers",
                         f"{int(seg.loc['Loyal', 'Customers']):,} Loyal customers generate "
                         f"{pct(seg.loc['Loyal', 'RevenueShare'])} of spend.", "Loyalty"))
    out.append(_card("Increase basket value",
                     "Recommend complementary products to raise the value of each order.", "Revenue"))
    return out


# --------------------------------------------------------------------------
# Forecast
# --------------------------------------------------------------------------
def forecast_insights(fb: dict) -> tuple[list[dict], float | None]:
    future = fb["future"]
    recent = fb["recent_avg_daily"]
    growth = (future["yhat"].mean() - recent) / recent * 100 if recent else None
    out = []
    if growth is not None:
        if growth > 5:
            out.append(_card("Demand is expected to increase",
                             f"Forecast average daily revenue is {growth:.1f}% above the last 90 days of actual sales. "
                             "Prepare additional inventory.", "Outlook", "positive"))
        elif growth < -5:
            out.append(_card("Demand may soften",
                             f"Forecast average daily revenue is {abs(growth):.1f}% below the last 90 days of actual sales. "
                             "Focus on promotional campaigns.", "Outlook", "warning"))
        else:
            out.append(_card("Demand is expected to remain stable",
                             f"Forecast average daily revenue is within 5% of the last 90 days of actual sales "
                             f"({growth:+.1f}%).", "Outlook"))
    width = ((future["yhat_upper"] - future["yhat_lower"]) / 2 / future["yhat"]).mean() * 100
    out.append(_card("Forecast uncertainty",
                     f"The confidence interval averages about +/-{width:.0f}% around the central forecast. "
                     "Plan inventory with this range in mind.", "Confidence"))
    out.append(_card("Review inventory weekly",
                     "Compare incoming sales with the forecast and adjust purchasing each week.", "Planning"))
    out.append(_card("Keep high-demand products in stock",
                     "Prioritise availability of Category A products during peak forecast days.", "Inventory"))
    out.append(_card("Use low-demand periods for promotions",
                     "Schedule offers when forecast demand is lowest to smooth revenue.", "Revenue"))
    out.append(_card("Refresh the model regularly",
                     "Re-run the forecasting notebook monthly with the latest sales data.", "Model"))
    return out, growth


# --------------------------------------------------------------------------
# Inventory
# --------------------------------------------------------------------------
def inventory_insights(inv_bundle: dict) -> list[dict]:
    abc = inv_bundle["abc"].set_index("ABC")
    n = inv_bundle["kpis"]["products"]
    a, b, c = (int(abc.loc[x, "Products"]) for x in "ABC")
    return [
        _card("Prioritise Category A",
              f"{a:,} products ({pct(a / n * 100)} of the catalogue) generate {pct(abc.loc['A', 'RevenueShare'])} of revenue. "
              "Keep them well stocked and restock promptly.", "Class A", "positive"),
        _card("Monitor Category B",
              f"{b:,} products contribute {pct(abc.loc['B', 'RevenueShare'])} of revenue. "
              "Review stock regularly to prevent shortages.", "Class B"),
        _card("Reduce excess in Category C",
              f"{c:,} products ({pct(c / n * 100)} of the catalogue) contribute only {pct(abc.loc['C', 'RevenueShare'])} "
              "of revenue. Limit stock and reduce excess inventory.", "Class C", "warning"),
        _card("Promote slow movers",
              f"Products below {inv_bundle['low_cut']:,.0f} units sold (bottom quartile) are flagged as low sales. "
              "Focus promotions on them.", "Low sales", "warning"),
        _card("Automate reorder points",
              "Set automatic reorder levels for high-demand products.", "Planning"),
        _card("Link inventory with the forecast",
              "Use the Demand Forecasting page to time replenishment.", "Planning"),
    ]
