"""
UI helpers, formatting utilities, and color theme constants
for Personal Daily Expense Tracker & Monthly Budget Analyzer.
"""

import calendar
from datetime import datetime, date
from typing import List, Tuple

# ========================================================
# COLOR THEME CONSTANTS (Modern Sleek Slate / Navy Design)
# ========================================================
COLOR_SIDEBAR_BG = "#0F172A"       # Deep dark slate navy
COLOR_SIDEBAR_HOVER = "#1E293B"    # Slightly lighter navy for hover
COLOR_SIDEBAR_ACTIVE = "#2563EB"   # Vivid Royal Blue for active tab
COLOR_SIDEBAR_TEXT = "#E2E8F0"     # Crisp soft white for sidebar text
COLOR_SIDEBAR_MUTED = "#94A3B8"    # Muted secondary text in sidebar

COLOR_BG_MAIN = "#F8FAFC"          # Clean light grey/blue workspace background
COLOR_CARD_BG = "#FFFFFF"          # Pure white cards
COLOR_CARD_BORDER = "#E2E8F0"      # Subtle border for elevation
COLOR_CARD_HEADER = "#F1F5F9"      # Very subtle header tint

COLOR_TEXT_PRIMARY = "#0F172A"     # High-contrast charcoal text
COLOR_TEXT_SECONDARY = "#475569"   # Slate medium contrast text
COLOR_TEXT_MUTED = "#94A3B8"       # Light muted text

# Semantic status colors
COLOR_PRIMARY = "#2563EB"          # Action blue
COLOR_PRIMARY_HOVER = "#1D4ED8"    # Darker blue on hover
COLOR_SUCCESS = "#10B981"          # Emerald green (Within budget)
COLOR_SUCCESS_BG = "#ECFDF5"       # Light green badge background
COLOR_WARNING = "#F59E0B"          # Amber (75%+ budget warning)
COLOR_WARNING_BG = "#FFFBEB"       # Light amber badge background
COLOR_DANGER = "#EF4444"           # Coral red (Over budget)
COLOR_DANGER_BG = "#FEF2F2"        # Light red badge background
COLOR_INFO = "#0284C7"             # Info sky blue

# ========================================================
# TYPOGRAPHY
# ========================================================
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 15, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 10)
FONT_HEADING = (FONT_FAMILY, 12, "bold")
FONT_SUBHEADING = (FONT_FAMILY, 10, "bold")
FONT_BODY = (FONT_FAMILY, 9)
FONT_BODY_BOLD = (FONT_FAMILY, 9, "bold")
FONT_SMALL = (FONT_FAMILY, 8)
FONT_METRIC_VALUE = (FONT_FAMILY, 18, "bold")
FONT_METRIC_LABEL = (FONT_FAMILY, 9)


def format_currency(amount: float) -> str:
    """
    Format numeric value into standard Indian currency representation:
    e.g. 125000.5 -> ₹ 1,25,000.50 or ₹ 125,000.50
    """
    try:
        val = float(amount)
        # Indian numbering system formatting
        s, *d = f"{val:.2f}".partition(".")
        r = ",".join([s[x-2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]]) if len(s) > 3 else s
        formatted = "".join([r] + d)
        return f"₹ {formatted}"
    except (ValueError, TypeError):
        return f"₹ {amount:.2f}" if isinstance(amount, (int, float)) else "₹ 0.00"


def format_date_display(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' into 'DD Mon YYYY' for human display."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except Exception:
        return date_str


def get_current_year_month() -> Tuple[int, int]:
    """Return (current_year, current_month)."""
    today = date.today()
    return today.year, today.month


def get_month_name(month_num: int) -> str:
    """Return full month name from month number (1-12)."""
    if 1 <= month_num <= 12:
        return calendar.month_name[month_num]
    return "Unknown"


def get_month_list() -> List[Tuple[int, str]]:
    """Return list of (month_number, month_name) for 1..12."""
    return [(i, calendar.month_name[i]) for i in range(1, 13)]


def get_year_list(offset_back: int = 4, offset_forward: int = 5) -> List[int]:
    """Return a list of years centered around the current year."""
    curr_year = date.today().year
    return list(range(curr_year - offset_back, curr_year + offset_forward + 1))


def get_status_colors(status: str) -> Tuple[str, str]:
    """
    Returns (foreground_color, background_color) for a budget status:
    'Within Budget' -> Green
    'Warning'       -> Amber
    'Over Budget'   -> Red
    """
    if status == "Over Budget":
        return COLOR_DANGER, COLOR_DANGER_BG
    elif status == "Warning":
        return COLOR_WARNING, COLOR_WARNING_BG
    return COLOR_SUCCESS, COLOR_SUCCESS_BG
