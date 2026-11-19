"""
Personal Daily Expense Tracker & Monthly Budget Analyzer
Main Desktop Application Entry Point

Student: Kiran R
Registration Number: 25PG00171
Course: Master of Computer Applications (MCA) III Semester
Subject: Python Programming Lab
University: Chanakya University
Academic Year: 2026–2027
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Enable DPI awareness on Windows for crisp high-resolution typography
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Ensure project root is in Python module search path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db_connection import db_manager
from modules import (
    DashboardView,
    CategoryManagerView,
    ExpenseManagerView,
    ExpenseHistoryView,
    BudgetAnalyzerView,
    ReportsView,
)
from utils.helpers import (
    COLOR_SIDEBAR_BG,
    COLOR_SIDEBAR_HOVER,
    COLOR_SIDEBAR_ACTIVE,
    COLOR_SIDEBAR_TEXT,
    COLOR_SIDEBAR_MUTED,
    COLOR_BG_MAIN,
    COLOR_CARD_BORDER,
    COLOR_PRIMARY,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_FAMILY,
    FONT_TITLE,
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_BODY,
    FONT_BODY_BOLD,
)


class ExpenseTrackerApp(tk.Tk):
    """
    Main Application Window orchestrating the sidebar navigation,
    header status bar, dynamic page swapping, and cross-module events.
    """

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Personal Daily Expense Tracker & Monthly Budget Analyzer — Chanakya University")
        self.geometry("1240x780")
        self.minsize(1080, 680)
        self.configure(bg=COLOR_BG_MAIN)

        # Application State
        self.current_page_name = "Dashboard"
        self.nav_buttons = {}

        # Configure ttk visual styles
        self._configure_styles()

        # Build Main Layout Structure
        self._build_layout()

        # Instantiate View Frames
        self._init_views()

        # Show initial view
        self.navigate_to("Dashboard")

        # Start header clock ticker
        self._update_clock()

        # Handle window close protocol
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_styles(self) -> None:
        """Configure modern ttk styles for Treeview, Combobox, and Notebook."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Frame style
        style.configure("TFrame", background=COLOR_BG_MAIN)

        # Modern Treeview Styling
        style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground=COLOR_TEXT_PRIMARY,
            fieldbackground="#FFFFFF",
            rowheight=28,
            font=(FONT_FAMILY, 9),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#F1F5F9",
            foreground=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 9, "bold"),
            relief="flat",
            padding=(5, 6),
        )
        style.map(
            "Treeview",
            background=[("selected", "#DBEAFE")],
            foreground=[("selected", "#1E3A8A")],
        )

        # Combobox styling
        style.configure("TCombobox", padding=4)
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#FFFFFF")],
            selectbackground=[("readonly", "#DBEAFE")],
            selectforeground=[("readonly", COLOR_TEXT_PRIMARY)],
        )

        # Notebook tab styling
        style.configure("TNotebook", background=COLOR_BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 6), font=(FONT_FAMILY, 9, "bold"))
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#FFFFFF"), ("!selected", "#E2E8F0")],
            foreground=[("selected", COLOR_PRIMARY), ("!selected", COLOR_TEXT_SECONDARY)],
        )

        # Progressbar styling
        style.configure("TProgressbar", thickness=10)

    def _build_layout(self) -> None:
        """Construct sidebar, top header bar, and content workspace."""
        # Top-level horizontal container
        self.main_container = tk.Frame(self, bg=COLOR_BG_MAIN)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Left Sidebar (250px)
        self.sidebar = tk.Frame(self.main_container, bg=COLOR_SIDEBAR_BG, width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Right Main Workspace
        self.workspace = tk.Frame(self.main_container, bg=COLOR_BG_MAIN)
        self.workspace.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Workspace Top Header Bar
        self._build_top_header()

        # Workspace Dynamic View Container
        self.content_area = tk.Frame(self.workspace, bg=COLOR_BG_MAIN)
        self.content_area.pack(fill=tk.BOTH, expand=True)

        # Build Sidebar Contents
        self._build_sidebar()

    def _build_top_header(self) -> None:
        """Header banner at the top of the workspace."""
        self.header_bar = tk.Frame(
            self.workspace,
            bg="#FFFFFF",
            height=60,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=20,
        )
        self.header_bar.pack(fill=tk.X, side=tk.TOP)
        self.header_bar.pack_propagate(False)

        # Left info: Academic project details
        left_info = tk.Frame(self.header_bar, bg="#FFFFFF")
        left_info.pack(side=tk.LEFT, fill=tk.Y, pady=8)

        lbl_proj = tk.Label(
            left_info,
            text="Personal Daily Expense Tracker & Monthly Budget Analyzer",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg="#FFFFFF",
        )
        lbl_proj.pack(anchor=tk.W)

        lbl_sub = tk.Label(
            left_info,
            text="Chanakya University • MCA III Semester • Kiran R (Reg No: 25PG00171)",
            font=("Segoe UI", 8),
            fg=COLOR_TEXT_SECONDARY,
            bg="#FFFFFF",
        )
        lbl_sub.pack(anchor=tk.W)

        # Right info: Live Clock & Database Status
        right_info = tk.Frame(self.header_bar, bg="#FFFFFF")
        right_info.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        self.lbl_clock = tk.Label(
            right_info,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_TEXT_PRIMARY,
            bg="#FFFFFF",
        )
        self.lbl_clock.pack(anchor=tk.E)

        lbl_db_status = tk.Label(
            right_info,
            text="● SQLite Database Connected",
            font=("Segoe UI", 8, "bold"),
            fg="#16A34A",
            bg="#FFFFFF",
        )
        lbl_db_status.pack(anchor=tk.E)

    def _build_sidebar(self) -> None:
        """Sidebar with application branding, navigation buttons, and student footer."""
        # Branding Header
        brand_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR_BG, padx=16, pady=20)
        brand_frame.pack(fill=tk.X)

        brand_title = tk.Label(
            brand_frame,
            text="💰 EXPENSE TRACKER",
            font=("Segoe UI", 12, "bold"),
            fg="#FFFFFF",
            bg=COLOR_SIDEBAR_BG,
        )
        brand_title.pack(anchor=tk.W)

        brand_sub = tk.Label(
            brand_frame,
            text="Monthly Budget Analyzer",
            font=("Segoe UI", 9),
            fg=COLOR_SIDEBAR_MUTED,
            bg=COLOR_SIDEBAR_BG,
        )
        brand_sub.pack(anchor=tk.W, pady=(2, 0))

        # Divider
        divider = tk.Frame(self.sidebar, bg="#1E293B", height=1)
        divider.pack(fill=tk.X, padx=16, pady=(5, 15))

        # Navigation Menu List
        menu_items = [
            ("Dashboard", "📊  Dashboard"),
            ("Add Expense", "➕  Add Expense"),
            ("Expense History", "📜  Expense History"),
            ("Categories", "🏷️  Categories"),
            ("Budget Analyzer", "🎯  Budget Analyzer"),
            ("Reports & Analytics", "📈  Reports & Analytics"),
        ]

        self.nav_menu_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR_BG)
        self.nav_menu_frame.pack(fill=tk.X, padx=10)

        for page_key, label_text in menu_items:
            btn = tk.Button(
                self.nav_menu_frame,
                text=f"  {label_text}",
                font=FONT_BODY_BOLD,
                fg=COLOR_SIDEBAR_TEXT,
                bg=COLOR_SIDEBAR_BG,
                activebackground=COLOR_SIDEBAR_HOVER,
                activeforeground="#FFFFFF",
                relief=tk.FLAT,
                anchor=tk.W,
                cursor="hand2",
                padx=14,
                pady=10,
                command=lambda k=page_key: self.navigate_to(k),
            )
            btn.pack(fill=tk.X, pady=2)
            self.nav_buttons[page_key] = btn

        # Exit Button
        btn_exit = tk.Button(
            self.nav_menu_frame,
            text="  🚪  Exit Application",
            font=FONT_BODY_BOLD,
            fg="#FCA5A5",
            bg=COLOR_SIDEBAR_BG,
            activebackground="#7F1D1D",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            anchor=tk.W,
            cursor="hand2",
            padx=14,
            pady=10,
            command=self._on_close,
        )
        btn_exit.pack(fill=tk.X, pady=(20, 2))

        # Student Details Footer at the bottom of sidebar
        footer_frame = tk.Frame(self.sidebar, bg="#0B1120", padx=14, pady=14)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

        lbl_student = tk.Label(
            footer_frame,
            text="Kiran R • 25PG00171",
            font=("Segoe UI", 9, "bold"),
            fg="#FFFFFF",
            bg="#0B1120",
        )
        lbl_student.pack(anchor=tk.W)

        lbl_dept = tk.Label(
            footer_frame,
            text="MCA III Semester • 2026-27\nDept of Computer Applications\nChanakya University",
            font=("Segoe UI", 8),
            fg=COLOR_SIDEBAR_MUTED,
            bg="#0B1120",
            justify=tk.LEFT,
        )
        lbl_dept.pack(anchor=tk.W, pady=(2, 0))

    def _init_views(self) -> None:
        """Create view frame instances and configure cross-module callbacks."""
        self.views = {}

        # 1. Dashboard
        self.views["Dashboard"] = DashboardView(
            self.content_area,
            navigate_callback=self.navigate_to,
        )

        # 2. Category Manager
        self.views["Categories"] = CategoryManagerView(
            self.content_area,
            on_change_callback=self._on_data_modified,
        )

        # 3. Expense Manager
        self.views["Add Expense"] = ExpenseManagerView(
            self.content_area,
            on_change_callback=self._on_data_modified,
        )

        # 4. Expense History
        self.views["Expense History"] = ExpenseHistoryView(
            self.content_area,
            on_edit_expense_callback=self._on_edit_expense_request,
            on_change_callback=self._on_data_modified,
        )

        # 5. Budget Analyzer
        self.views["Budget Analyzer"] = BudgetAnalyzerView(
            self.content_area,
            on_change_callback=self._on_data_modified,
        )

        # 6. Reports & Analytics
        self.views["Reports & Analytics"] = ReportsView(
            self.content_area,
        )

    def navigate_to(self, page_name: str) -> None:
        """Swaps the visible view in content_area and updates sidebar button styles."""
        if page_name not in self.views:
            return

        # Hide current view
        for name, view in self.views.items():
            view.pack_forget()

        # Update button highlights
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(
                    bg=COLOR_SIDEBAR_ACTIVE,
                    fg="#FFFFFF",
                    font=(FONT_FAMILY, 9, "bold"),
                )
            else:
                btn.configure(
                    bg=COLOR_SIDEBAR_BG,
                    fg=COLOR_SIDEBAR_TEXT,
                    font=(FONT_FAMILY, 9),
                )

        # Show target view
        target_view = self.views[page_name]
        target_view.pack(fill=tk.BOTH, expand=True)
        self.current_page_name = page_name

        # Trigger on-show refresh hooks
        if page_name == "Dashboard":
            target_view.refresh_dashboard()
        elif page_name == "Categories":
            target_view.load_categories()
        elif page_name == "Add Expense":
            target_view.refresh_categories()
            target_view.load_expenses()
        elif page_name == "Expense History":
            target_view.refresh_filter_options()
            target_view.apply_filters()
        elif page_name == "Budget Analyzer":
            target_view.refresh_analysis()
        elif page_name == "Reports & Analytics":
            target_view.render_all_reports()

    def _on_data_modified(self) -> None:
        """Callback invoked whenever an expense or category is added, edited, or deleted."""
        # Refresh category comboboxes and active views
        if "Add Expense" in self.views:
            self.views["Add Expense"].refresh_categories()
        if "Expense History" in self.views:
            self.views["Expense History"].refresh_filter_options()

        # If currently viewing dashboard, refresh immediately
        if self.current_page_name == "Dashboard":
            self.views["Dashboard"].refresh_dashboard()
        elif self.current_page_name == "Budget Analyzer":
            self.views["Budget Analyzer"].refresh_analysis()
        elif self.current_page_name == "Reports & Analytics":
            self.views["Reports & Analytics"].render_all_reports()

    def _on_edit_expense_request(self, exp_id: int) -> None:
        """Invoked when user clicks 'Edit in Expense Manager' from the history view."""
        self.navigate_to("Add Expense")
        self.views["Add Expense"].load_expense_for_external_edit(exp_id)

    def _update_clock(self) -> None:
        """Update live clock in the top header."""
        now = datetime.now()
        clock_str = now.strftime("%A, %d %B %Y  •  %I:%M:%S %p")
        self.lbl_clock.config(text=clock_str)
        self.after(1000, self._update_clock)

    def _on_close(self) -> None:
        """Prompt confirmation before quitting to ensure clean exit."""
        if messagebox.askokcancel("Exit Application", "Are you sure you want to close Personal Expense Tracker?"):
            self.destroy()


def main():
    """Application launch bootstrap."""
    app = ExpenseTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
