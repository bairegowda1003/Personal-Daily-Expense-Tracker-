"""
Personal Daily Expense Tracker & Monthly Budget Analyzer
Database Connection and Data Access Layer
MCA III Semester Python Programming Lab - Chanakya University
Student: Kiran R (Reg No: 25PG00171)
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple

# Default database file path relative to this script's directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "expense_tracker.db")

DEFAULT_CATEGORIES = [
    ("Food", 6000.0),
    ("Travel", 3000.0),
    ("Shopping", 4000.0),
    ("Education", 3000.0),
    ("Healthcare", 2000.0),
    ("Bills", 4000.0),
    ("Entertainment", 2000.0),
    ("Others", 1500.0),
]


class DatabaseManager:
    """
    Manages SQLite database connections, schema initialization,
    and all parameterized CRUD operations for categories and expenses.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path if db_path else DEFAULT_DB_PATH
        # Ensure database directory exists
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(db_dir, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """
        Creates and returns a SQLite connection with foreign keys enabled
        and row_factory set to sqlite3.Row for dictionary-like access.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            # Enforce foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except sqlite3.Error as e:
            raise RuntimeError(f"Database connection error: {e}")

    def init_database(self) -> None:
        """
        Creates required tables if they don't exist and seeds default categories.
        Guarantees that existing user data is never overwritten.
        """
        conn = self.get_connection()
        try:
            with conn:
                # Table 1: categories
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS categories (
                        cat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cat_name TEXT NOT NULL UNIQUE,
                        monthly_budget REAL NOT NULL DEFAULT 0
                    );
                    """
                )

                # Table 2: expenses
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS expenses (
                        exp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cat_id INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        exp_date TEXT NOT NULL,
                        description TEXT NOT NULL,
                        payment_mode TEXT NOT NULL,
                        FOREIGN KEY (cat_id) REFERENCES categories(cat_id)
                    );
                    """
                )

                # Seed default categories if table is empty or missing them
                for cat_name, default_budget in DEFAULT_CATEGORIES:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO categories (cat_name, monthly_budget)
                        VALUES (?, ?);
                        """,
                        (cat_name, default_budget),
                    )
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to initialize database schema: {e}")
        finally:
            conn.close()

    # ==========================================
    # CATEGORY OPERATIONS
    # ==========================================

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Fetch all categories sorted alphabetically."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT cat_id, cat_name, monthly_budget FROM categories ORDER BY cat_name ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_category_by_id(self, cat_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single category by its ID."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT cat_id, cat_name, monthly_budget FROM categories WHERE cat_id = ?", (cat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_category_by_name(self, cat_name: str) -> Optional[Dict[str, Any]]:
        """Fetch a single category by its name (case-insensitive)."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT cat_id, cat_name, monthly_budget FROM categories WHERE LOWER(cat_name) = LOWER(?)", (cat_name.strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def add_category(self, cat_name: str, monthly_budget: float = 0.0) -> int:
        """
        Add a new category with a monthly budget.
        Raises ValueError if category name already exists.
        """
        name = cat_name.strip()
        if not name:
            raise ValueError("Category name cannot be empty.")
        if monthly_budget < 0:
            raise ValueError("Monthly budget cannot be negative.")

        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO categories (cat_name, monthly_budget) VALUES (?, ?)",
                    (name, float(monthly_budget)),
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Category '{name}' already exists.")
        finally:
            conn.close()

    def update_category(self, cat_id: int, cat_name: str, monthly_budget: float) -> bool:
        """
        Update category name and/or budget.
        Raises ValueError if new name conflicts with an existing category.
        """
        name = cat_name.strip()
        if not name:
            raise ValueError("Category name cannot be empty.")
        if monthly_budget < 0:
            raise ValueError("Monthly budget cannot be negative.")

        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE categories SET cat_name = ?, monthly_budget = ? WHERE cat_id = ?",
                    (name, float(monthly_budget), cat_id),
                )
                return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            raise ValueError(f"Category '{name}' already exists.")
        finally:
            conn.close()

    def update_category_budget(self, cat_id: int, monthly_budget: float) -> bool:
        """Update just the monthly budget for a category."""
        if monthly_budget < 0:
            raise ValueError("Monthly budget cannot be negative.")
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE categories SET monthly_budget = ? WHERE cat_id = ?",
                    (float(monthly_budget), cat_id),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def get_category_expense_count(self, cat_id: int) -> int:
        """Return the number of expenses associated with a given category ID."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS cnt FROM expenses WHERE cat_id = ?", (cat_id,))
            row = cursor.fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    def delete_category(self, cat_id: int) -> bool:
        """
        Deletes a category only if no expenses are associated with it.
        Raises ValueError if expenses exist.
        """
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                # Check for associated expenses
                cursor.execute("SELECT COUNT(*) AS cnt FROM expenses WHERE cat_id = ?", (cat_id,))
                cnt = cursor.fetchone()["cnt"]
                if cnt > 0:
                    raise ValueError(f"Cannot delete category: {cnt} expense record(s) are linked to it. Please reassign or delete the expenses first.")

                cursor.execute("DELETE FROM categories WHERE cat_id = ?", (cat_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    # ==========================================
    # EXPENSE OPERATIONS
    # ==========================================

    def add_expense(
        self,
        cat_id: int,
        amount: float,
        exp_date: str,
        description: str,
        payment_mode: str,
    ) -> int:
        """
        Record a new daily expense.
        Uses parameterized query to prevent SQL injection.
        """
        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        desc = description.strip()
        if not desc:
            raise ValueError("Expense description cannot be empty.")
        if payment_mode not in ["Cash", "UPI", "Card"]:
            raise ValueError("Payment mode must be Cash, UPI, or Card.")

        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO expenses (cat_id, amount, exp_date, description, payment_mode)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (cat_id, float(amount), exp_date.strip(), desc, payment_mode),
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Foreign key or database constraint failed: {e}")
        finally:
            conn.close()

    def update_expense(
        self,
        exp_id: int,
        cat_id: int,
        amount: float,
        exp_date: str,
        description: str,
        payment_mode: str,
    ) -> bool:
        """Update an existing expense record."""
        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        desc = description.strip()
        if not desc:
            raise ValueError("Expense description cannot be empty.")
        if payment_mode not in ["Cash", "UPI", "Card"]:
            raise ValueError("Payment mode must be Cash, UPI, or Card.")

        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE expenses
                    SET cat_id = ?, amount = ?, exp_date = ?, description = ?, payment_mode = ?
                    WHERE exp_id = ?
                    """,
                    (cat_id, float(amount), exp_date.strip(), desc, payment_mode, exp_id),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_expense(self, exp_id: int) -> bool:
        """Delete an expense record by its ID."""
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE exp_id = ?", (exp_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def get_expense_by_id(self, exp_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single expense by ID along with its category name."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.exp_id, e.cat_id, e.amount, e.exp_date, e.description, e.payment_mode,
                       c.cat_name, c.monthly_budget
                FROM expenses e
                JOIN categories c ON e.cat_id = c.cat_id
                WHERE e.exp_id = ?
                """,
                (exp_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_expenses(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all expenses sorted newest to oldest."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT e.exp_id, e.cat_id, e.amount, e.exp_date, e.description, e.payment_mode,
                       c.cat_name
                FROM expenses e
                JOIN categories c ON e.cat_id = c.cat_id
                ORDER BY e.exp_date DESC, e.exp_id DESC
            """
            if limit:
                query += f" LIMIT {int(limit)}"
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_recent_expenses(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch the most recent N expenses."""
        return self.get_all_expenses(limit=limit)

    def get_filtered_expenses(
        self,
        search: Optional[str] = None,
        cat_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        sort_by: str = "date_desc",
    ) -> List[Dict[str, Any]]:
        """
        Fetch expenses matching various filter parameters.
        Safe parameterized construction.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT e.exp_id, e.cat_id, e.amount, e.exp_date, e.description, e.payment_mode,
                       c.cat_name
                FROM expenses e
                JOIN categories c ON e.cat_id = c.cat_id
                WHERE 1=1
            """
            params: List[Any] = []

            if search and search.strip():
                query += " AND (e.description LIKE ? OR c.cat_name LIKE ?)"
                kw = f"%{search.strip()}%"
                params.extend([kw, kw])

            if cat_id is not None and cat_id > 0:
                query += " AND e.cat_id = ?"
                params.append(cat_id)

            if payment_mode and payment_mode != "All":
                query += " AND e.payment_mode = ?"
                params.append(payment_mode)

            if start_date:
                query += " AND e.exp_date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND e.exp_date <= ?"
                params.append(end_date)

            if year and month:
                month_str = f"{year:04d}-{month:02d}"
                query += " AND strftime('%Y-%m', e.exp_date) = ?"
                params.append(month_str)
            elif year:
                year_str = f"{year:04d}"
                query += " AND strftime('%Y', e.exp_date) = ?"
                params.append(year_str)

            # Sorting
            if sort_by == "date_desc":
                query += " ORDER BY e.exp_date DESC, e.exp_id DESC"
            elif sort_by == "date_asc":
                query += " ORDER BY e.exp_date ASC, e.exp_id ASC"
            elif sort_by == "amount_desc":
                query += " ORDER BY e.amount DESC, e.exp_date DESC"
            elif sort_by == "amount_asc":
                query += " ORDER BY e.amount ASC, e.exp_date DESC"
            else:
                query += " ORDER BY e.exp_date DESC, e.exp_id DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ==========================================
    # BUDGET & ANALYTICS OPERATIONS
    # ==========================================

    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """
        Calculates key dashboard financial figures for a specific month:
        - Total expenses in month
        - Total monthly budget (sum of all categories)
        - Remaining overall budget
        - Number of transactions
        - Highest spending category (name & amount)
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            month_str = f"{year:04d}-{month:02d}"

            # Total monthly budget across all categories
            cursor.execute("SELECT COALESCE(SUM(monthly_budget), 0.0) AS total_budget FROM categories")
            total_budget = float(cursor.fetchone()["total_budget"])

            # Total expenses and transaction count for this month
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0.0) AS total_spent, COUNT(*) AS txn_count
                FROM expenses
                WHERE strftime('%Y-%m', exp_date) = ?
                """,
                (month_str,),
            )
            row = cursor.fetchone()
            total_spent = float(row["total_spent"])
            txn_count = int(row["txn_count"])

            remaining_budget = total_budget - total_spent

            # Highest spending category for this month
            cursor.execute(
                """
                SELECT c.cat_name, COALESCE(SUM(e.amount), 0.0) AS cat_spent
                FROM expenses e
                JOIN categories c ON e.cat_id = c.cat_id
                WHERE strftime('%Y-%m', e.exp_date) = ?
                GROUP BY c.cat_id, c.cat_name
                ORDER BY cat_spent DESC
                LIMIT 1
                """,
                (month_str,),
            )
            highest_row = cursor.fetchone()
            if highest_row and highest_row["cat_spent"] > 0:
                highest_cat = highest_row["cat_name"]
                highest_cat_spent = float(highest_row["cat_spent"])
            else:
                highest_cat = "None"
                highest_cat_spent = 0.0

            return {
                "year": year,
                "month": month,
                "total_budget": total_budget,
                "total_spent": total_spent,
                "remaining_budget": remaining_budget,
                "txn_count": txn_count,
                "highest_category": highest_cat,
                "highest_category_amount": highest_cat_spent,
            }
        finally:
            conn.close()

    def get_category_budget_analysis(self, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Returns category-wise budget vs actual expenditure for a given month:
        - cat_id, cat_name
        - monthly_budget
        - amount_spent
        - remaining_budget
        - percent_consumed
        - status: 'Within Budget', 'Warning', 'Over Budget'
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            month_str = f"{year:04d}-{month:02d}"

            cursor.execute(
                """
                SELECT c.cat_id, c.cat_name, c.monthly_budget,
                       COALESCE(SUM(e.amount), 0.0) AS amount_spent,
                       COUNT(e.exp_id) AS txn_count
                FROM categories c
                LEFT JOIN expenses e ON c.cat_id = e.cat_id AND strftime('%Y-%m', e.exp_date) = ?
                GROUP BY c.cat_id, c.cat_name, c.monthly_budget
                ORDER BY c.cat_name ASC
                """,
                (month_str,),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                budget = float(row["monthly_budget"])
                spent = float(row["amount_spent"])
                remaining = budget - spent

                if budget > 0:
                    percent = (spent / budget) * 100.0
                    if spent > budget:
                        status = "Over Budget"
                    elif percent >= 75.0:
                        status = "Warning"
                    else:
                        status = "Within Budget"
                else:
                    # Budget is zero
                    if spent > 0:
                        percent = 100.0
                        status = "Over Budget"
                    else:
                        percent = 0.0
                        status = "Within Budget"

                results.append({
                    "cat_id": row["cat_id"],
                    "cat_name": row["cat_name"],
                    "monthly_budget": budget,
                    "amount_spent": spent,
                    "remaining": remaining,
                    "percent_consumed": round(percent, 2),
                    "status": status,
                    "txn_count": row["txn_count"],
                })
            return results
        finally:
            conn.close()

    def get_category_spending_breakdown(self, year: int, month: int) -> List[Tuple[str, float]]:
        """Returns list of (cat_name, amount_spent) for the given month."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            month_str = f"{year:04d}-{month:02d}"
            cursor.execute(
                """
                SELECT c.cat_name, SUM(e.amount) AS total
                FROM expenses e
                JOIN categories c ON e.cat_id = c.cat_id
                WHERE strftime('%Y-%m', e.exp_date) = ?
                GROUP BY c.cat_id, c.cat_name
                HAVING total > 0
                ORDER BY total DESC
                """,
                (month_str,),
            )
            return [(r["cat_name"], float(r["total"])) for r in cursor.fetchall()]
        finally:
            conn.close()

    def get_payment_mode_breakdown(self, year: int, month: int) -> List[Tuple[str, float, int]]:
        """Returns list of (payment_mode, total_amount, count) for the given month."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            month_str = f"{year:04d}-{month:02d}"
            cursor.execute(
                """
                SELECT payment_mode, SUM(amount) AS total, COUNT(*) AS cnt
                FROM expenses
                WHERE strftime('%Y-%m', exp_date) = ?
                GROUP BY payment_mode
                ORDER BY total DESC
                """,
                (month_str,),
            )
            return [(r["payment_mode"], float(r["total"]), int(r["cnt"])) for r in cursor.fetchall()]
        finally:
            conn.close()

    def get_monthly_trend(self, num_months: int = 6) -> List[Dict[str, Any]]:
        """
        Returns spending trend for the last `num_months` up to current date.
        List of dicts: {'month_label': 'Jan 2026', 'month_key': '2026-01', 'total_spent': float}
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT strftime('%Y-%m', exp_date) AS month_key,
                       SUM(amount) AS total
                FROM expenses
                GROUP BY month_key
                ORDER BY month_key DESC
                LIMIT ?
                """,
                (num_months,),
            )
            rows = cursor.fetchall()
            # Reverse so it's chronological
            results = []
            for r in reversed(rows):
                results.append({
                    "month_key": r["month_key"],
                    "total_spent": float(r["total"]),
                })
            return results
        finally:
            conn.close()

    def get_daily_spending_for_month(self, year: int, month: int) -> List[Tuple[str, float]]:
        """Returns list of (exp_date, total_spent) for each active day in the month."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            month_str = f"{year:04d}-{month:02d}"
            cursor.execute(
                """
                SELECT exp_date, SUM(amount) AS total
                FROM expenses
                WHERE strftime('%Y-%m', exp_date) = ?
                GROUP BY exp_date
                ORDER BY exp_date ASC
                """,
                (month_str,),
            )
            return [(r["exp_date"], float(r["total"])) for r in cursor.fetchall()]
        finally:
            conn.close()


# Module-level default singleton instance
db_manager = DatabaseManager()
