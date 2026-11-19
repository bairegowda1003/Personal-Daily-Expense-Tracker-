"""
Comprehensive Unit & Integration Test Suite
Personal Daily Expense Tracker & Monthly Budget Analyzer
MCA III Semester Python Programming Lab - Chanakya University
Student: Kiran R (Reg No: 25PG00171)
"""

import os
import sys
import unittest
import tempfile
import sqlite3

# Ensure project root is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db_connection import DatabaseManager
from utils.validators import (
    validate_amount,
    validate_budget,
    validate_description,
    validate_category_name,
    validate_payment_mode,
    validate_date,
)
from utils.helpers import format_currency, format_date_display


class TestDatabaseManager(unittest.TestCase):
    """Tests for SQLite database operations, schema integrity, and transactions."""

    def setUp(self):
        # Create a temporary database file for each test
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = DatabaseManager(self.temp_file.name)

    def tearDown(self):
        # Clean up temporary database file
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except Exception:
                pass

    def test_database_initialization_and_default_categories(self):
        """Verify tables and default categories are created properly."""
        categories = self.db.get_all_categories()
        self.assertEqual(len(categories), 8)
        cat_names = [c["cat_name"] for c in categories]
        self.assertIn("Food", cat_names)
        self.assertIn("Travel", cat_names)
        self.assertIn("Bills", cat_names)
        self.assertIn("Others", cat_names)

    def test_foreign_keys_enforced(self):
        """Verify that SQLite foreign key enforcement is active."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(fk_status, 1)

    def test_add_and_get_category(self):
        """Verify adding and retrieving a category."""
        cat_id = self.db.add_category("Gym & Fitness", 2500.0)
        self.assertIsInstance(cat_id, int)

        cat = self.db.get_category_by_id(cat_id)
        self.assertIsNotNone(cat)
        self.assertEqual(cat["cat_name"], "Gym & Fitness")
        self.assertEqual(cat["monthly_budget"], 2500.0)

    def test_duplicate_category_raises_error(self):
        """Verify that duplicate category names are rejected."""
        with self.assertRaises(ValueError):
            self.db.add_category("Food", 1000.0)

    def test_update_category(self):
        """Verify updating category details."""
        cat = self.db.get_category_by_name("Travel")
        self.assertIsNotNone(cat)

        updated = self.db.update_category(cat["cat_id"], "Travel & Commute", 3500.0)
        self.assertTrue(updated)

        revised = self.db.get_category_by_id(cat["cat_id"])
        self.assertEqual(revised["cat_name"], "Travel & Commute")
        self.assertEqual(revised["monthly_budget"], 3500.0)

    def test_delete_empty_category(self):
        """Verify deleting a category that has no expenses."""
        cat_id = self.db.add_category("Temporary", 500.0)
        deleted = self.db.delete_category(cat_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.db.get_category_by_id(cat_id))

    def test_delete_category_with_expenses_is_prevented(self):
        """Verify that categories with linked expenses cannot be deleted."""
        cat = self.db.get_category_by_name("Food")
        # Add an expense under Food
        self.db.add_expense(cat["cat_id"], 450.0, "2026-11-01", "Dinner", "UPI")

        # Deleting category should raise ValueError
        with self.assertRaises(ValueError):
            self.db.delete_category(cat["cat_id"])

    def test_add_and_update_expense(self):
        """Verify expense creation and modification."""
        cat = self.db.get_category_by_name("Food")
        exp_id = self.db.add_expense(cat["cat_id"], 250.0, "2026-11-10", "Lunch with team", "UPI")
        self.assertIsInstance(exp_id, int)

        expense = self.db.get_expense_by_id(exp_id)
        self.assertIsNotNone(expense)
        self.assertEqual(expense["amount"], 250.0)
        self.assertEqual(expense["description"], "Lunch with team")
        self.assertEqual(expense["payment_mode"], "UPI")

        # Update expense
        self.db.update_expense(exp_id, cat["cat_id"], 300.0, "2026-11-10", "Buffet Lunch", "Card")
        updated = self.db.get_expense_by_id(exp_id)
        self.assertEqual(updated["amount"], 300.0)
        self.assertEqual(updated["description"], "Buffet Lunch")
        self.assertEqual(updated["payment_mode"], "Card")

    def test_delete_expense(self):
        """Verify deleting an expense."""
        cat = self.db.get_category_by_name("Shopping")
        exp_id = self.db.add_expense(cat["cat_id"], 1200.0, "2026-11-12", "Books", "Card")
        self.assertTrue(self.db.delete_expense(exp_id))
        self.assertIsNone(self.db.get_expense_by_id(exp_id))

    def test_persistence_across_connections(self):
        """Verify that data persists when reconnecting to the database."""
        cat = self.db.get_category_by_name("Education")
        self.db.add_expense(cat["cat_id"], 1500.0, "2026-11-15", "Python Course", "UPI")

        # Re-open database with a new DatabaseManager instance
        new_manager = DatabaseManager(self.temp_file.name)
        expenses = new_manager.get_all_expenses()
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0]["description"], "Python Course")


class TestBudgetAndAnalyticsLogic(unittest.TestCase):
    """Tests for monthly budget calculations, variances, and threshold statuses."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = DatabaseManager(self.temp_file.name)

        # Set specific budgets for testing
        food = self.db.get_category_by_name("Food")
        travel = self.db.get_category_by_name("Travel")
        self.db.update_category_budget(food["cat_id"], 5000.0)
        self.db.update_category_budget(travel["cat_id"], 2000.0)

        self.food_id = food["cat_id"]
        self.travel_id = travel["cat_id"]

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except Exception:
                pass

    def test_monthly_summary_calculation(self):
        """Verify summary statistics for a given month."""
        self.db.add_expense(self.food_id, 1000.0, "2026-11-05", "Groceries", "UPI")
        self.db.add_expense(self.food_id, 2000.0, "2026-11-10", "Dine out", "Card")
        self.db.add_expense(self.travel_id, 800.0, "2026-11-12", "Metro Pass", "Cash")

        # Expense in another month (should not affect November)
        self.db.add_expense(self.food_id, 999.0, "2026-10-15", "October Dinner", "UPI")

        summary = self.db.get_monthly_summary(2026, 11)
        self.assertEqual(summary["total_spent"], 3800.0)
        self.assertEqual(summary["txn_count"], 3)
        self.assertEqual(summary["highest_category"], "Food")
        self.assertEqual(summary["highest_category_amount"], 3000.0)

    def test_category_budget_threshold_statuses(self):
        """
        Verify budget status rules:
        - Within Budget: < 75%
        - Warning: >= 75% and <= 100%
        - Over Budget: > 100%
        """
        # Food has budget 5000:
        # Spend 3500 -> 70% -> Within Budget
        self.db.add_expense(self.food_id, 3500.0, "2026-11-01", "Bulk Groceries", "UPI")
        analysis = self.db.get_category_budget_analysis(2026, 11)
        food_item = next(item for item in analysis if item["cat_id"] == self.food_id)
        self.assertEqual(food_item["status"], "Within Budget")
        self.assertEqual(food_item["remaining"], 1500.0)

        # Add 500 more -> 4000 (80%) -> Warning
        self.db.add_expense(self.food_id, 500.0, "2026-11-02", "Snacks", "Cash")
        analysis = self.db.get_category_budget_analysis(2026, 11)
        food_item = next(item for item in analysis if item["cat_id"] == self.food_id)
        self.assertEqual(food_item["status"], "Warning")
        self.assertEqual(food_item["remaining"], 1000.0)

        # Add 1500 more -> 5500 (110%) -> Over Budget
        self.db.add_expense(self.food_id, 1500.0, "2026-11-03", "Party", "Card")
        analysis = self.db.get_category_budget_analysis(2026, 11)
        food_item = next(item for item in analysis if item["cat_id"] == self.food_id)
        self.assertEqual(food_item["status"], "Over Budget")
        self.assertEqual(food_item["remaining"], -500.0)

    def test_zero_budget_category_handling(self):
        """Ensure no ZeroDivisionError when category budget is 0."""
        zero_cat_id = self.db.add_category("Miscellaneous", 0.0)
        self.db.add_expense(zero_cat_id, 150.0, "2026-11-04", "Sundries", "Cash")

        analysis = self.db.get_category_budget_analysis(2026, 11)
        misc_item = next(item for item in analysis if item["cat_id"] == zero_cat_id)
        self.assertEqual(misc_item["status"], "Over Budget")
        self.assertEqual(misc_item["remaining"], -150.0)

    def test_filtered_queries(self):
        """Verify multi-criteria filtering."""
        self.db.add_expense(self.food_id, 250.0, "2026-11-01", "Coffee and tea", "Cash")
        self.db.add_expense(self.travel_id, 500.0, "2026-11-05", "Bus fare", "UPI")
        self.db.add_expense(self.food_id, 1200.0, "2026-11-10", "Team Lunch", "Card")

        # 1. Search by keyword
        res_search = self.db.get_filtered_expenses(search="Coffee")
        self.assertEqual(len(res_search), 1)
        self.assertEqual(res_search[0]["description"], "Coffee and tea")

        # 2. Filter by Category
        res_cat = self.db.get_filtered_expenses(cat_id=self.travel_id)
        self.assertEqual(len(res_cat), 1)
        self.assertEqual(res_cat[0]["cat_name"], "Travel")

        # 3. Filter by Payment Mode
        res_mode = self.db.get_filtered_expenses(payment_mode="Card")
        self.assertEqual(len(res_mode), 1)
        self.assertEqual(res_mode[0]["description"], "Team Lunch")

        # 4. Filter by Date Range
        res_date = self.db.get_filtered_expenses(start_date="2026-11-02", end_date="2026-11-08")
        self.assertEqual(len(res_date), 1)
        self.assertEqual(res_date[0]["description"], "Bus fare")


class TestValidators(unittest.TestCase):
    """Tests for input validation functions."""

    def test_validate_amount(self):
        # Valid amounts
        valid, val, _ = validate_amount("250.00")
        self.assertTrue(valid)
        self.assertEqual(val, 250.00)

        valid, val, _ = validate_amount("1,500.50")
        self.assertTrue(valid)
        self.assertEqual(val, 1500.50)

        # Invalid amounts
        self.assertFalse(validate_amount("")[0])
        self.assertFalse(validate_amount("-50")[0])
        self.assertFalse(validate_amount("0")[0])
        self.assertFalse(validate_amount("abc")[0])
        self.assertFalse(validate_amount("50.123")[0])  # More than 2 decimal places

    def test_validate_budget(self):
        # Zero budget is allowed
        valid, val, _ = validate_budget("0")
        self.assertTrue(valid)
        self.assertEqual(val, 0.0)

        # Positive budget
        valid, val, _ = validate_budget("10000")
        self.assertTrue(valid)
        self.assertEqual(val, 10000.0)

        # Negative budget rejected
        self.assertFalse(validate_budget("-100")[0])

    def test_validate_description(self):
        valid, desc, _ = validate_description("Grocery shopping")
        self.assertTrue(valid)
        self.assertEqual(desc, "Grocery shopping")

        # Empty string
        self.assertFalse(validate_description("")[0])
        self.assertFalse(validate_description("   ")[0])

        # Exceeding length
        long_str = "a" * 250
        self.assertFalse(validate_description(long_str)[0])

    def test_validate_category_name(self):
        self.assertTrue(validate_category_name("Travel & Tourism")[0])
        self.assertTrue(validate_category_name("Books-2026")[0])
        self.assertFalse(validate_category_name("")[0])
        self.assertFalse(validate_category_name("A")[0])  # Too short
        self.assertFalse(validate_category_name("Bad<Script>")[0])  # Invalid characters

    def test_validate_payment_mode(self):
        self.assertTrue(validate_payment_mode("Cash")[0])
        self.assertTrue(validate_payment_mode("UPI")[0])
        self.assertTrue(validate_payment_mode("Card")[0])
        self.assertFalse(validate_payment_mode("Crypto")[0])
        self.assertFalse(validate_payment_mode("")[0])

    def test_validate_date(self):
        self.assertTrue(validate_date("2026-11-19")[0])
        self.assertTrue(validate_date("2026-02-28")[0])
        self.assertFalse(validate_date("2026-02-30")[0])  # Non-existent date
        self.assertFalse(validate_date("not-a-date")[0])
        self.assertFalse(validate_date("1990-01-01")[0])  # Outside 2000-2099 bounds


class TestHelpers(unittest.TestCase):
    """Tests for UI helpers and formatting."""

    def test_format_currency(self):
        self.assertEqual(format_currency(500), "₹ 500.00")
        self.assertEqual(format_currency(125000), "₹ 1,25,000.00")

    def test_format_date_display(self):
        self.assertEqual(format_date_display("2026-11-19"), "19 Nov 2026")


if __name__ == "__main__":
    unittest.main()
