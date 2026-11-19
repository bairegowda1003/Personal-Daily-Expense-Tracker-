"""
Sample Data Seeder
Populates realistic demonstration expenses for November 2026 and prior months
so the dashboard, budget analyzer, charts, and history are populated with realistic data on initial presentation.
Safely checks if expenses already exist to avoid duplication.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db_connection import db_manager


def seed_demo_data():
    """Seeds sample transactions across various categories and payment modes if empty."""
    existing_expenses = db_manager.get_all_expenses()
    if len(existing_expenses) > 0:
        print(f"Database already contains {len(existing_expenses)} expenses. Skipping seed.")
        return

    print("Seeding sample expenses for academic demonstration...")

    # Fetch category IDs
    cats = {c["cat_name"]: c["cat_id"] for c in db_manager.get_all_categories()}

    # Update categories with realistic monthly budgets
    budgets = {
        "Food": 6000.0,
        "Travel": 3000.0,
        "Shopping": 4000.0,
        "Education": 3000.0,
        "Healthcare": 2000.0,
        "Bills": 4000.0,
        "Entertainment": 2000.0,
        "Others": 1500.0,
    }
    for cat_name, budget_amt in budgets.items():
        if cat_name in cats:
            db_manager.update_category_budget(cats[cat_name], budget_amt)

    # Sample expenses for November 2026 (Demonstrates normal, warning, and over budget)
    # Food: 6000 budget -> Spend 6450 (Over Budget)
    # Travel: 3000 budget -> Spend 2400 (80% -> Warning)
    # Shopping: 4000 budget -> Spend 1850 (Within Budget)
    # Bills: 4000 budget -> Spend 3800 (95% -> Warning)
    # Healthcare: 2000 budget -> Spend 750 (Within Budget)
    # Education: 3000 budget -> Spend 2500 (Within Budget)
    # Entertainment: 2000 budget -> Spend 950 (Within Budget)
    sample_records = [
        # Food (Total: 6450 - Over budget)
        (cats["Food"], 1850.00, "2026-11-02", "Monthly Grocery Store (Supermarket)", "UPI"),
        (cats["Food"], 720.00, "2026-11-06", "Weekend Dinner with College Friends", "Card"),
        (cats["Food"], 1400.00, "2026-11-10", "Weekly Vegetables, Milk & Provisions", "Cash"),
        (cats["Food"], 980.00, "2026-11-14", "Family Lunch Outing", "UPI"),
        (cats["Food"], 1500.00, "2026-11-18", "Organic Pantry & Dry Fruits", "UPI"),

        # Travel (Total: 2400 - Warning at 80%)
        (cats["Travel"], 1200.00, "2026-11-03", "Metro Smart Card Monthly Recharge", "UPI"),
        (cats["Travel"], 750.00, "2026-11-08", "Cab Ride to Campus Examination Center", "UPI"),
        (cats["Travel"], 450.00, "2026-11-15", "Fuel / Petrol Refill", "Cash"),

        # Shopping (Total: 1850 - Within budget)
        (cats["Shopping"], 1250.00, "2026-11-05", "Formal Campus Wear Shirt", "Card"),
        (cats["Shopping"], 600.00, "2026-11-12", "Notebooks & Lab Stationery", "Cash"),

        # Bills (Total: 3800 - Warning at 95%)
        (cats["Bills"], 1500.00, "2026-11-04", "Broadband High-Speed Internet Bill", "UPI"),
        (cats["Bills"], 1800.00, "2026-11-07", "Monthly Electricity Utility Bill", "UPI"),
        (cats["Bills"], 500.00, "2026-11-11", "Mobile Postpaid Plan Recharge", "UPI"),

        # Healthcare (Total: 750 - Within budget)
        (cats["Healthcare"], 450.00, "2026-11-09", "Prescription Multivitamins & Medicines", "Card"),
        (cats["Healthcare"], 300.00, "2026-11-16", "Dental Checkup & Consultation", "UPI"),

        # Education (Total: 2500 - Within budget)
        (cats["Education"], 1800.00, "2026-11-01", "Python & Machine Learning Textbook", "Card"),
        (cats["Education"], 700.00, "2026-11-13", "IEEE Student Chapter Membership Fee", "UPI"),

        # Entertainment (Total: 950 - Within budget)
        (cats["Entertainment"], 550.00, "2026-11-07", "Weekend IMAX Movie Ticket", "Card"),
        (cats["Entertainment"], 400.00, "2026-11-17", "OTT Subscription Renewal", "UPI"),

        # Prior months for historical trend line chart:
        # October 2026
        (cats["Food"], 5200.00, "2026-10-10", "October Groceries and Dining", "UPI"),
        (cats["Travel"], 2200.00, "2026-10-15", "October Travel & Commute", "UPI"),
        (cats["Bills"], 3900.00, "2026-10-05", "October Utility and Internet Bills", "UPI"),
        (cats["Shopping"], 3100.00, "2026-10-20", "Festival Shopping", "Card"),

        # September 2026
        (cats["Food"], 4900.00, "2026-09-12", "September Groceries", "UPI"),
        (cats["Bills"], 3600.00, "2026-09-08", "September Electricity & WiFi", "UPI"),
        (cats["Education"], 2800.00, "2026-09-02", "Semester Lab Manuals & Materials", "Card"),
        (cats["Travel"], 1950.00, "2026-09-18", "September Bus and Metro Pass", "Cash"),

        # August 2026
        (cats["Food"], 4800.00, "2026-08-14", "August Food Expenses", "UPI"),
        (cats["Bills"], 3500.00, "2026-08-05", "August Household Bills", "UPI"),
        (cats["Shopping"], 2400.00, "2026-08-22", "College Supplies & Backpack", "Card"),
    ]

    for cat_id, amt, exp_date, desc, mode in sample_records:
        db_manager.add_expense(cat_id, amt, exp_date, desc, mode)

    print(f"Successfully seeded {len(sample_records)} demonstration transactions.")


if __name__ == "__main__":
    seed_demo_data()
