"""
Input validation utilities for Personal Daily Expense Tracker.
Uses regex, type conversions, and boundary checks to prevent crashes and invalid data.
"""

import re
from datetime import datetime
from typing import Tuple, Optional, Any


def validate_amount(amount_input: Any) -> Tuple[bool, Optional[float], str]:
    """
    Validates an expense or budget amount.
    Returns: (is_valid, parsed_float_or_None, error_message)
    """
    if amount_input is None:
        return False, None, "Amount cannot be empty."

    val_str = str(amount_input).strip()
    if not val_str:
        return False, None, "Amount cannot be empty."

    # Remove commas if user typed e.g. 1,000.50
    val_cleaned = val_str.replace(",", "")

    # Strict regex check for positive decimal or integer
    # e.g. 12, 12.5, 12.50
    if not re.match(r"^\d+(\.\d{1,2})?$", val_cleaned):
        return False, None, "Amount must be a positive number with up to 2 decimal places (e.g. 250.00)."

    try:
        val_float = float(val_cleaned)
    except ValueError:
        return False, None, "Invalid numeric format for amount."

    if val_float <= 0:
        return False, None, "Amount must be greater than zero."

    if val_float > 100_000_000:
        return False, None, "Amount exceeds maximum allowable limit (₹100,000,000)."

    return True, round(val_float, 2), ""


def validate_budget(budget_input: Any) -> Tuple[bool, Optional[float], str]:
    """
    Validates category monthly budget (allows 0.0 or positive).
    Returns: (is_valid, parsed_float_or_None, error_message)
    """
    if budget_input is None:
        return False, None, "Budget cannot be empty."

    val_str = str(budget_input).strip()
    if not val_str:
        return False, None, "Budget cannot be empty."

    val_cleaned = val_str.replace(",", "")

    if not re.match(r"^\d+(\.\d{1,2})?$", val_cleaned):
        return False, None, "Budget must be a non-negative number with up to 2 decimal places (e.g. 5000 or 5000.00)."

    try:
        val_float = float(val_cleaned)
    except ValueError:
        return False, None, "Invalid numeric format for budget."

    if val_float < 0:
        return False, None, "Budget cannot be negative."

    if val_float > 100_000_000:
        return False, None, "Budget exceeds maximum allowable limit (₹100,000,000)."

    return True, round(val_float, 2), ""


def validate_description(description: str, min_len: int = 1, max_len: int = 200) -> Tuple[bool, str, str]:
    """
    Validates expense description string.
    Returns: (is_valid, sanitized_description, error_message)
    """
    if not description:
        return False, "", "Description cannot be empty."

    desc_cleaned = description.strip()
    if len(desc_cleaned) < min_len:
        return False, "", f"Description must be at least {min_len} character(s) long."

    if len(desc_cleaned) > max_len:
        return False, "", f"Description cannot exceed {max_len} characters (currently {len(desc_cleaned)})."

    # Reject pure whitespace or control characters
    if not re.search(r"\S", desc_cleaned):
        return False, "", "Description cannot be just blank spaces."

    return True, desc_cleaned, ""


def validate_category_name(category_name: str, max_len: int = 50) -> Tuple[bool, str, str]:
    """
    Validates category name.
    Returns: (is_valid, sanitized_category_name, error_message)
    """
    if not category_name:
        return False, "", "Category name cannot be empty."

    cat_cleaned = category_name.strip()
    if len(cat_cleaned) < 2:
        return False, "", "Category name must be at least 2 characters long."

    if len(cat_cleaned) > max_len:
        return False, "", f"Category name cannot exceed {max_len} characters."

    # Pattern: letters, digits, spaces, hyphens, slashes, ampersands
    if not re.match(r"^[A-Za-z0-9\s&/\-_]+$", cat_cleaned):
        return False, "", "Category name contains invalid characters. Use letters, numbers, spaces, &, /, or -."

    return True, cat_cleaned, ""


def validate_payment_mode(payment_mode: str) -> Tuple[bool, str, str]:
    """
    Validates payment mode. Must be one of 'Cash', 'UPI', 'Card'.
    Returns: (is_valid, normalized_mode, error_message)
    """
    allowed_modes = ["Cash", "UPI", "Card"]
    if not payment_mode or payment_mode.strip() not in allowed_modes:
        return False, "", f"Payment mode must be one of: {', '.join(allowed_modes)}."
    return True, payment_mode.strip(), ""


def validate_date(date_str: str) -> Tuple[bool, str, str]:
    """
    Validates date string in 'YYYY-MM-DD' format.
    Returns: (is_valid, date_str, error_message)
    """
    if not date_str or not date_str.strip():
        return False, "", "Date cannot be empty."

    cleaned_date = date_str.strip()

    # Regex test
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned_date):
        # Also handle common DD/MM/YYYY or DD-MM-YYYY format if user typed it
        match_slash = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$", cleaned_date)
        if match_slash:
            d, m, y = match_slash.groups()
            cleaned_date = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        else:
            return False, "", "Date must be in YYYY-MM-DD format."

    try:
        parsed_dt = datetime.strptime(cleaned_date, "%Y-%m-%d")
    except ValueError:
        return False, "", "Date is not a valid calendar date."

    # Reasonable date range: 2000-01-01 to 2099-12-31
    if parsed_dt.year < 2000 or parsed_dt.year > 2099:
        return False, "", "Year must be between 2000 and 2099."

    return True, cleaned_date, ""
