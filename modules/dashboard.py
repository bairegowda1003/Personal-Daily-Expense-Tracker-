"""
Dashboard Module
Home overview screen displaying real-time financial KPIs, recent transactions,
budget utilization meters, and embedded category spending breakdown charts.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, Callable

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database.db_connection import db_manager
from utils.helpers import (
    COLOR_BG_MAIN,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_TITLE,
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_METRIC_VALUE,
    FONT_METRIC_LABEL,
    get_month_name,
    format_currency,
    format_date_display,
)

CHART_COLORS = [
    "#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
    "#06B6D4", "#EC4899", "#84CC16", "#F97316", "#64748B"
]


class DashboardView(ttk.Frame):
    """
    Main dashboard view providing a high-level executive summary of financial health.
    """

    def __init__(self, parent: tk.Widget, navigate_callback: Optional[Callable[[str], None]] = None):
        super().__init__(parent)
        self.navigate_callback = navigate_callback
        self.chart_canvas: Optional[FigureCanvasTkAgg] = None

        self.configure(style="TFrame")
        self._build_ui()
        self.refresh_dashboard()

    def _build_ui(self) -> None:
        """Construct dashboard visual hierarchy."""
        container = tk.Frame(self, bg=COLOR_BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header Section
        header_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        left_hdr = tk.Frame(header_frame, bg=COLOR_BG_MAIN)
        left_hdr.pack(side=tk.LEFT)

        today = date.today()
        month_str = get_month_name(today.month)
        title_lbl = tk.Label(
            left_hdr,
            text=f"📊 Financial Dashboard • {month_str} {today.year}",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            left_hdr,
            text="Real-time financial summary, active budget tracking, and spending trends.",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Quick Action Buttons on right of header
        quick_actions = tk.Frame(header_frame, bg=COLOR_BG_MAIN)
        quick_actions.pack(side=tk.RIGHT)

        btn_new_exp = tk.Button(
            quick_actions,
            text="➕ New Expense",
            command=lambda: self._navigate("Add Expense"),
            bg=COLOR_PRIMARY,
            fg="white",
            activebackground=COLOR_PRIMARY_HOVER,
            activeforeground="white",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=5,
        )
        btn_new_exp.pack(side=tk.LEFT, padx=5)

        btn_budgets = tk.Button(
            quick_actions,
            text="🎯 Budget Analyzer",
            command=lambda: self._navigate("Budget Analyzer"),
            bg="#DBEAFE",
            fg=COLOR_PRIMARY,
            activebackground="#BFDBFE",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=5,
        )
        btn_budgets.pack(side=tk.LEFT, padx=5)

        # 5 Metric Cards
        self._build_metric_cards(container)

        # Bottom 2-Column Split: Recent Transactions + Embedded Donut Chart
        bottom_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        # Left Column: Recent Transactions (55% width)
        self._build_recent_transactions_panel(bottom_frame)

        # Right Column: Visual Category Breakdown (45% width)
        self._build_chart_panel(bottom_frame)

    def _build_metric_cards(self, parent: tk.Widget) -> None:
        """Top row of 5 KPI cards."""
        cards_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        cards_frame.pack(fill=tk.X, pady=(0, 15))

        for i in range(5):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="dash_kpi")

        self.kpi_spent, self.sub_spent = self._create_card(cards_frame, 0, "MONTHLY EXPENSES", "₹ 0.00", "#EF4444", "Current Month Spent")
        self.kpi_budget, self.sub_budget = self._create_card(cards_frame, 1, "TOTAL BUDGET", "₹ 0.00", COLOR_PRIMARY, "Allocated Cap")
        self.kpi_remaining, self.sub_remaining = self._create_card(cards_frame, 2, "REMAINING BALANCE", "₹ 0.00", COLOR_SUCCESS, "Buffer Available")
        self.kpi_txns, self.sub_txns = self._create_card(cards_frame, 3, "TRANSACTIONS", "0", "#8B5CF6", "Entries Recorded")
        self.kpi_highest, self.sub_highest = self._create_card(cards_frame, 4, "TOP EXPENSE CAT", "-", "#F59E0B", "Peak Expenditure")

    def _create_card(self, parent: tk.Widget, col: int, title: str, default_val: str, accent_color: str, subtitle: str):
        card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=4)

        accent = tk.Frame(card, bg=accent_color, width=4)
        accent.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        content = tk.Frame(card, bg=COLOR_CARD_BG)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        lbl = tk.Label(content, text=title, font=FONT_METRIC_LABEL, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
        lbl.pack(anchor=tk.W)

        val = tk.Label(content, text=default_val, font=FONT_METRIC_VALUE, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        val.pack(anchor=tk.W, pady=(2, 2))

        sub = tk.Label(content, text=subtitle, font=("Segoe UI", 8), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
        sub.pack(anchor=tk.W)

        return val, sub

    def _build_recent_transactions_panel(self, parent: tk.Widget) -> None:
        """Left side: Recent transactions table."""
        panel = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=15,
            pady=15,
        )
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Panel Header
        top_bar = tk.Frame(panel, bg=COLOR_CARD_BG)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        title = tk.Label(top_bar, text="Recent Transactions", font=FONT_HEADING, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        title.pack(side=tk.LEFT)

        btn_view_all = tk.Button(
            top_bar,
            text="View All History →",
            command=lambda: self._navigate("Expense History"),
            bg="#F1F5F9",
            fg=COLOR_PRIMARY,
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=2,
        )
        btn_view_all.pack(side=tk.RIGHT)

        # Table
        cols = ("date", "category", "desc", "mode", "amount")
        self.tree_recent = ttk.Treeview(panel, columns=cols, show="headings", height=10)

        self.tree_recent.heading("date", text="Date")
        self.tree_recent.heading("category", text="Category")
        self.tree_recent.heading("desc", text="Description")
        self.tree_recent.heading("mode", text="Mode")
        self.tree_recent.heading("amount", text="Amount (₹)")

        self.tree_recent.column("date", width=85, anchor=tk.CENTER)
        self.tree_recent.column("category", width=105, anchor=tk.W)
        self.tree_recent.column("desc", width=160, anchor=tk.W)
        self.tree_recent.column("mode", width=70, anchor=tk.CENTER)
        self.tree_recent.column("amount", width=95, anchor=tk.E)

        v_scroll = ttk.Scrollbar(panel, orient=tk.VERTICAL, command=self.tree_recent.yview)
        self.tree_recent.configure(yscrollcommand=v_scroll.set)

        self.tree_recent.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_chart_panel(self, parent: tk.Widget) -> None:
        """Right side: Embedded Matplotlib Donut Chart."""
        self.chart_panel = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=15,
            pady=15,
            width=420,
        )
        self.chart_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.chart_panel.pack_propagate(False)

        top_bar = tk.Frame(self.chart_panel, bg=COLOR_CARD_BG)
        top_bar.pack(fill=tk.X, pady=(0, 5))

        title = tk.Label(top_bar, text="Category Spending Share", font=FONT_HEADING, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        title.pack(side=tk.LEFT)

        self.chart_container = tk.Frame(self.chart_panel, bg=COLOR_CARD_BG)
        self.chart_container.pack(fill=tk.BOTH, expand=True)

    def refresh_dashboard(self) -> None:
        """Fetch latest calculations from database and redraw cards, table, and chart."""
        today = date.today()
        summary = db_manager.get_monthly_summary(today.year, today.month)
        recent = db_manager.get_recent_expenses(limit=8)
        breakdown = db_manager.get_category_spending_breakdown(today.year, today.month)

        # 1. Update KPI Cards
        total_spent = summary["total_spent"]
        total_budget = summary["total_budget"]
        remaining = summary["remaining_budget"]
        txn_count = summary["txn_count"]

        self.kpi_spent.config(text=format_currency(total_spent))
        self.kpi_budget.config(text=format_currency(total_budget))

        rem_color = COLOR_SUCCESS if remaining >= 0 else COLOR_DANGER
        self.kpi_remaining.config(text=format_currency(remaining), fg=rem_color)
        if total_budget > 0:
            pct_used = (total_spent / total_budget) * 100
            self.sub_remaining.config(text=f"{pct_used:.1f}% budget used")
        else:
            self.sub_remaining.config(text="No budget set")

        self.kpi_txns.config(text=str(txn_count))
        self.sub_txns.config(text=f"{get_month_name(today.month)} {today.year}")

        if summary["highest_category"] != "None":
            self.kpi_highest.config(text=summary["highest_category"])
            self.sub_highest.config(text=format_currency(summary["highest_category_amount"]))
        else:
            self.kpi_highest.config(text="None")
            self.sub_highest.config(text="₹ 0.00")

        # 2. Update Recent Transactions
        for item in self.tree_recent.get_children():
            self.tree_recent.delete(item)

        for exp in recent:
            self.tree_recent.insert(
                "",
                tk.END,
                values=(
                    format_date_display(exp["exp_date"]),
                    exp["cat_name"],
                    exp["description"],
                    exp["payment_mode"],
                    format_currency(exp["amount"]),
                ),
            )

        # 3. Update Donut Chart
        self._draw_donut_chart(breakdown, total_spent)

    def _draw_donut_chart(self, breakdown: list, total_spent: float) -> None:
        """Render donut chart inside right chart container."""
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        if not breakdown or total_spent <= 0:
            lbl = tk.Label(
                self.chart_container,
                text="No expenses recorded for this month yet.\n\nClick '+ New Expense' above to get started!",
                font=FONT_BODY,
                fg=COLOR_TEXT_SECONDARY,
                bg=COLOR_CARD_BG,
                justify=tk.CENTER,
            )
            lbl.pack(expand=True)
            return

        fig = Figure(figsize=(4.0, 3.4), dpi=95)
        fig.patch.set_facecolor(COLOR_CARD_BG)
        ax = fig.add_subplot(111)

        labels = [item[0] for item in breakdown]
        values = [item[1] for item in breakdown]
        colors = CHART_COLORS[:len(labels)]

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.0f%%",
            startangle=140,
            colors=colors,
            pctdistance=0.72,
            textprops=dict(color=COLOR_TEXT_PRIMARY, fontsize=8),
        )

        centre_circle = matplotlib.patches.Circle((0, 0), 0.52, fc=COLOR_CARD_BG)
        ax.add_artist(centre_circle)

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(7.5)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _navigate(self, page_name: str) -> None:
        """Trigger navigation in main window."""
        if self.navigate_callback:
            self.navigate_callback(page_name)
