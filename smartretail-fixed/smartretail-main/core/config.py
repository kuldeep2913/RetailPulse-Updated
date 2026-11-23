"""Central configuration: paths, palette, labels and project metadata."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
ASSETS_DIR = ROOT / "assets"

TRANSACTIONS_CSV = DATA_DIR / "cleaned_retail.csv"
SEGMENTS_CSV = DATA_DIR / "customer_segments.csv"
FORECAST_CSV = DATA_DIR / "sales_forecast.csv"

# Currency symbol used across the app. Change it here if your data is in another currency.
CURRENCY = "₹"

# Weekday order used by every weekday chart.
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Colour palette (muted, low-saturation). Keep in sync with assets/style.css.
COLORS = {
    "bg": "#ECECE5",
    "card": "#FFFFFF",
    "primary": "#8F84E0",          # violet
    "primary_strong": "#15151A",   # ink
    "secondary": "#B9B1EE",
    "text": "#15151A",
    "muted": "#6D6D75",
    "border": "#E4E4DA",
    "grid": "#E9E9E0",
    "green": "#7DD3B0",
    "amber": "#F6A58F",            # salmon
    "red": "#E8795F",
    "teal": "#6FA0A8",
    "lime": "#C8F23A",
    "violet_soft": "#D8CFF7",
}

# Categorical colour sequence for multi-series charts.
COLORWAY = [
    COLORS["primary"], COLORS["lime"], COLORS["amber"],
    COLORS["primary_strong"], COLORS["green"], COLORS["teal"],
]

SEGMENT_COLORS = {
    "VIP": COLORS["primary_strong"],
    "Loyal": COLORS["lime"],
    "Regular": COLORS["primary"],
    "At-Risk": COLORS["amber"],
}
SEGMENT_ORDER = ["VIP", "Loyal", "Regular", "At-Risk"]

ABC_COLORS = {"A": COLORS["lime"], "B": COLORS["primary"], "C": "#D9D9CF"}

# Plotly country-name fixes for the world map (dataset name -> Plotly name).
MAP_COUNTRY_FIXES = {"EIRE": "Ireland", "RSA": "South Africa", "USA": "United States"}
MAP_COUNTRY_SKIP = {"Unspecified", "European Community", "Channel Islands"}

# Project team shown at the bottom of the Overview page.
# Set SHOW_ROLL_NUMBERS to False if the app is deployed publicly and you prefer not to display them.
SHOW_ROLL_NUMBERS = True
TEAM = [
    {"name": "Kuldeep Yadav", "roll_no": "230410101067"},
    {"name": "Prashant", "roll_no": "230410101110"},
]
