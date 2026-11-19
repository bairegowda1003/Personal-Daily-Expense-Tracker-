"""
Modules package initialization.
"""

from .dashboard import DashboardView
from .category_manager import CategoryManagerView
from .expense_manager import ExpenseManagerView
from .expense_history import ExpenseHistoryView
from .budget_analyzer import BudgetAnalyzerView
from .reports import ReportsView

__all__ = [
    "DashboardView",
    "CategoryManagerView",
    "ExpenseManagerView",
    "ExpenseHistoryView",
    "BudgetAnalyzerView",
    "ReportsView",
]
