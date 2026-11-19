"""
Reports and Analytics Module
Generates graphical charts (Donut, Bar, Line) via Matplotlib embedded in Tkinter,
and produces comprehensive financial summaries.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, List, Tuple

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
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_TITLE,
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_METRIC_VALUE,
    FONT_METRIC_LABEL,
    get_month_list,
    get_year_list,
    format_currency,
)


# Distinctive color palette for charts
CHART_COLORS = [
    "#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
    "#06B6D4", "#EC4899", "#84CC16", "#F97316", "#64748B"
]


class ReportsView(ttk.Frame):
    """
    GUI component displaying interactive visual charts and statistical breakdowns.
    """

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self.canvases: List[FigureCanvasTkAgg] = []

        self.configure(style="TFrame")
        self._build_ui()
        self.render_all_reports()

    def _build_ui(self) -> None:
        """Construct the reports layout."""
        container = tk.Frame(self, bg=COLOR_BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header with Period Selector
        header_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        left_header = tk.Frame(header_frame, bg=COLOR_BG_MAIN)
        left_header.pack(side=tk.LEFT)

        title_lbl = tk.Label(
            left_header,
            text="📈 Financial Reports & Analytics",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            left_header,
            text="Interactive visualization of spending patterns, budget adherence, and category distributions.",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Selector card on right
        sel_card = tk.Frame(
            header_frame,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=12,
            pady=6,
        )
        sel_card.pack(side=tk.RIGHT)

        tk.Label(sel_card, text="Period:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG).pack(side=tk.LEFT, padx=(0, 8))

        today = date.today()

        # Month
        self.month_var = tk.StringVar()
        month_names = [m[1] for m in get_month_list()]
        self.combo_month = ttk.Combobox(
            sel_card,
            textvariable=self.month_var,
            values=month_names,
            state="readonly",
            width=11,
            font=FONT_BODY,
        )
        self.combo_month.current(today.month - 1)
        self.combo_month.pack(side=tk.LEFT, padx=(0, 8))
        self.combo_month.bind("<<ComboboxSelected>>", lambda e: self.render_all_reports())

        # Year
        self.year_var = tk.StringVar(value=str(today.year))
        years = [str(y) for y in get_year_list()]
        self.combo_year = ttk.Combobox(
            sel_card,
            textvariable=self.year_var,
            values=years,
            state="readonly",
            width=7,
            font=FONT_BODY,
        )
        self.combo_year.pack(side=tk.LEFT, padx=(0, 8))
        self.combo_year.bind("<<ComboboxSelected>>", lambda e: self.render_all_reports())

        btn_refresh = tk.Button(
            sel_card,
            text="🔄 Refresh",
            command=self.render_all_reports,
            bg=COLOR_PRIMARY,
            fg="white",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=2,
        )
        btn_refresh.pack(side=tk.LEFT)

        # 4 KPI Summary Cards
        self._build_kpi_cards(container)

        # Tabs for Charts and Tabular Summary
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Category Distribution (Donut Chart)
        self.tab_pie = tk.Frame(self.notebook, bg=COLOR_CARD_BG)
        self.notebook.add(self.tab_pie, text="  🍩 Category Share  ")

        # Tab 2: Category Budget vs Actual (Bar Chart)
        self.tab_bar = tk.Frame(self.notebook, bg=COLOR_CARD_BG)
        self.notebook.add(self.tab_bar, text="  📊 Budget vs Actual  ")

        # Tab 3: Monthly Spending Trend (Line Chart)
        self.tab_trend = tk.Frame(self.notebook, bg=COLOR_CARD_BG)
        self.notebook.add(self.tab_trend, text="  📈 Monthly Trend  ")

        # Tab 4: Payment Mode Analysis
        self.tab_mode = tk.Frame(self.notebook, bg=COLOR_CARD_BG)
        self.notebook.add(self.tab_mode, text="  💳 Payment Modes  ")

        # Tab 5: Detailed Tabular Summary
        self.tab_table = tk.Frame(self.notebook, bg=COLOR_CARD_BG)
        self.notebook.add(self.tab_table, text="  📋 Summary Table  ")

        self._build_table_tab()

    def _build_kpi_cards(self, parent: tk.Widget) -> None:
        """Top row showing statistics."""
        kpi_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        kpi_frame.pack(fill=tk.X, pady=(0, 15))

        for i in range(4):
            kpi_frame.grid_columnconfigure(i, weight=1, uniform="rep_kpi")

        self.kpi_highest = self._add_kpi(kpi_frame, 0, "HIGHEST CATEGORY", "-", "#DC2626")
        self.kpi_lowest = self._add_kpi(kpi_frame, 1, "LOWEST CATEGORY", "-", "#16A34A")
        self.kpi_mode = self._add_kpi(kpi_frame, 2, "PREFERRED PAYMENT", "-", "#2563EB")
        self.kpi_daily_avg = self._add_kpi(kpi_frame, 3, "DAILY AVERAGE SPENT", "₹ 0.00", "#7C3AED")

    def _add_kpi(self, parent: tk.Widget, col: int, title: str, init_val: str, color: str):
        card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=4)

        accent = tk.Frame(card, bg=color, width=4)
        accent.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        inner = tk.Frame(card, bg=COLOR_CARD_BG)
        inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        lbl = tk.Label(inner, text=title, font=("Segoe UI", 8, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
        lbl.pack(anchor=tk.W)

        val = tk.Label(inner, text=init_val, font=("Segoe UI", 13, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        val.pack(anchor=tk.W, pady=(2, 0))
        return val

    def _build_table_tab(self) -> None:
        """Tabular summary of category statistics."""
        frame = tk.Frame(self.tab_table, bg=COLOR_CARD_BG, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl = tk.Label(frame, text="Category Spending & Allocation Overview", font=FONT_HEADING, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl.pack(anchor=tk.W, pady=(0, 10))

        cols = ("cat", "budget", "spent", "pct_budget", "pct_total", "txns")
        self.summary_tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)

        self.summary_tree.heading("cat", text="Category")
        self.summary_tree.heading("budget", text="Monthly Budget (₹)")
        self.summary_tree.heading("spent", text="Actual Spent (₹)")
        self.summary_tree.heading("pct_budget", text="% of Budget Used")
        self.summary_tree.heading("pct_total", text="% of Total Outflow")
        self.summary_tree.heading("txns", text="Transactions")

        self.summary_tree.column("cat", width=160, anchor=tk.W)
        self.summary_tree.column("budget", width=140, anchor=tk.E)
        self.summary_tree.column("spent", width=140, anchor=tk.E)
        self.summary_tree.column("pct_budget", width=130, anchor=tk.CENTER)
        self.summary_tree.column("pct_total", width=130, anchor=tk.CENTER)
        self.summary_tree.column("txns", width=100, anchor=tk.CENTER)

        v_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=v_scroll.set)

        self.summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _get_selected_period(self) -> tuple:
        """Return (year_int, month_int)."""
        m_name = self.month_var.get()
        month_idx = 1
        for idx, name in get_month_list():
            if name == m_name:
                month_idx = idx
                break
        try:
            year_val = int(self.year_var.get())
        except ValueError:
            year_val = date.today().year
        return year_val, month_idx

    def _clear_chart_container(self, parent: tk.Widget) -> None:
        """Destroy any previous widgets inside a chart tab."""
        for widget in parent.winfo_children():
            widget.destroy()

    def render_all_reports(self) -> None:
        """Refresh all KPI cards, chart canvases, and summary tables."""
        year, month = self._get_selected_period()

        # Query data
        analysis = db_manager.get_category_budget_analysis(year, month)
        breakdown = db_manager.get_category_spending_breakdown(year, month)
        payment_modes = db_manager.get_payment_mode_breakdown(year, month)
        daily_spending = db_manager.get_daily_spending_for_month(year, month)
        trend = db_manager.get_monthly_trend(num_months=6)

        total_spent = sum(amt for _, amt in breakdown)

        # 1. Update KPIs
        if breakdown:
            self.kpi_highest.config(text=f"{breakdown[0][0]} ({format_currency(breakdown[0][1])})")
            lowest_item = [item for item in breakdown if item[1] > 0]
            if lowest_item:
                self.kpi_lowest.config(text=f"{lowest_item[-1][0]} ({format_currency(lowest_item[-1][1])})")
            else:
                self.kpi_lowest.config(text="None")
        else:
            self.kpi_highest.config(text="No Expenses")
            self.kpi_lowest.config(text="No Expenses")

        if payment_modes:
            self.kpi_mode.config(text=f"{payment_modes[0][0]} ({payment_modes[0][2]} txns)")
        else:
            self.kpi_mode.config(text="None")

        # Daily Average
        days_with_expenses = len(daily_spending)
        if days_with_expenses > 0 and total_spent > 0:
            avg_per_day = total_spent / days_with_expenses
            self.kpi_daily_avg.config(text=format_currency(avg_per_day))
        else:
            self.kpi_daily_avg.config(text="₹ 0.00")

        # 2. Render Charts
        self._render_pie_chart(breakdown, total_spent)
        self._render_bar_chart(analysis)
        self._render_trend_chart(trend)
        self._render_payment_chart(payment_modes)

        # 3. Render Table
        self._render_summary_table(analysis, total_spent)

    def _render_pie_chart(self, breakdown: List[Tuple[str, float]], total_spent: float) -> None:
        """Render Donut/Pie Chart on tab_pie."""
        self._clear_chart_container(self.tab_pie)

        if not breakdown or total_spent <= 0:
            lbl = tk.Label(self.tab_pie, text="No expense records found for this period to generate a pie chart.", font=FONT_HEADING, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
            lbl.pack(expand=True)
            return

        fig = Figure(figsize=(6.5, 4.2), dpi=100)
        fig.patch.set_facecolor(COLOR_CARD_BG)
        ax = fig.add_subplot(111)

        labels = [item[0] for item in breakdown]
        values = [item[1] for item in breakdown]
        colors = CHART_COLORS[:len(labels)]

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            pctdistance=0.75,
            textprops=dict(color=COLOR_TEXT_PRIMARY, fontsize=9),
        )

        # Draw donut hole
        centre_circle = matplotlib.patches.Circle((0, 0), 0.55, fc=COLOR_CARD_BG)
        ax.add_artist(centre_circle)
        ax.set_title(f"Expense Share by Category (Total: {format_currency(total_spent)})", fontsize=11, fontweight="bold", color=COLOR_TEXT_PRIMARY, pad=12)

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(8)

        canvas = FigureCanvasTkAgg(fig, master=self.tab_pie)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _render_bar_chart(self, analysis: List[dict]) -> None:
        """Render Bar Chart comparing Budget vs Actual on tab_bar."""
        self._clear_chart_container(self.tab_bar)

        active = [c for c in analysis if (c["monthly_budget"] > 0 or c["amount_spent"] > 0)]
        if not active:
            lbl = tk.Label(self.tab_bar, text="No categories with budgets or expenses recorded for this period.", font=FONT_HEADING, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
            lbl.pack(expand=True)
            return

        fig = Figure(figsize=(7.5, 4.2), dpi=100)
        fig.patch.set_facecolor(COLOR_CARD_BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor("#F8FAFC")

        cat_names = [c["cat_name"] for c in active]
        budgets = [c["monthly_budget"] for c in active]
        spents = [c["amount_spent"] for c in active]

        import numpy as np
        x = np.arange(len(cat_names))
        width = 0.35

        rects1 = ax.bar(x - width/2, budgets, width, label="Allocated Budget", color="#93C5FD", edgecolor="#3B82F6")
        rects2 = ax.bar(x + width/2, spents, width, label="Actual Spent", color="#EF4444", edgecolor="#B91C1C")

        ax.set_ylabel("Amount (₹)", fontsize=10, fontweight="bold", color=COLOR_TEXT_PRIMARY)
        ax.set_title("Budget vs Actual Spending by Category", fontsize=11, fontweight="bold", color=COLOR_TEXT_PRIMARY, pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(cat_names, rotation=20, ha="right", fontsize=9)
        ax.legend(frameon=True, facecolor="white")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.tab_bar)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _render_trend_chart(self, trend: List[dict]) -> None:
        """Render Line Chart showing 6-month spending trajectory."""
        self._clear_chart_container(self.tab_trend)

        if not trend:
            lbl = tk.Label(self.tab_trend, text="Not enough monthly history to generate a trend line.", font=FONT_HEADING, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
            lbl.pack(expand=True)
            return

        fig = Figure(figsize=(7.0, 4.2), dpi=100)
        fig.patch.set_facecolor(COLOR_CARD_BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor("#F8FAFC")

        labels = [item["month_key"] for item in trend]
        amounts = [item["total_spent"] for item in trend]

        ax.plot(labels, amounts, marker="o", linewidth=2.5, color="#2563EB", markersize=6, label="Monthly Outflow")
        ax.fill_between(labels, amounts, color="#DBEAFE", alpha=0.5)

        for i, txt in enumerate(amounts):
            ax.annotate(format_currency(txt), (labels[i], amounts[i]), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8, fontweight="bold")

        ax.set_ylabel("Total Spending (₹)", fontsize=10, fontweight="bold", color=COLOR_TEXT_PRIMARY)
        ax.set_title("Historical Monthly Expenditure Trajectory", fontsize=11, fontweight="bold", color=COLOR_TEXT_PRIMARY, pad=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(frameon=True, facecolor="white")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.tab_trend)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _render_payment_chart(self, payment_modes: List[Tuple[str, float, int]]) -> None:
        """Render Bar / Donut Chart for Payment Modes."""
        self._clear_chart_container(self.tab_mode)

        if not payment_modes:
            lbl = tk.Label(self.tab_mode, text="No expense data for payment modes.", font=FONT_HEADING, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
            lbl.pack(expand=True)
            return

        fig = Figure(figsize=(6.5, 4.2), dpi=100)
        fig.patch.set_facecolor(COLOR_CARD_BG)
        ax = fig.add_subplot(111)

        modes = [m[0] for m in payment_modes]
        amounts = [m[1] for m in payment_modes]
        colors = ["#10B981", "#3B82F6", "#F59E0B"][:len(modes)]

        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=modes,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            pctdistance=0.75,
            textprops=dict(color=COLOR_TEXT_PRIMARY, fontsize=9),
        )

        centre_circle = matplotlib.patches.Circle((0, 0), 0.55, fc=COLOR_CARD_BG)
        ax.add_artist(centre_circle)
        ax.set_title("Payment Method Distribution", fontsize=11, fontweight="bold", color=COLOR_TEXT_PRIMARY, pad=12)

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(8)

        canvas = FigureCanvasTkAgg(fig, master=self.tab_mode)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _render_summary_table(self, analysis: List[dict], total_spent: float) -> None:
        """Populate summary treeview on Tab 5."""
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        for c in analysis:
            budget = c["monthly_budget"]
            spent = c["amount_spent"]

            pct_budget_str = f"{c['percent_consumed']:.1f}%" if budget > 0 else "N/A"
            pct_total_val = (spent / total_spent * 100.0) if total_spent > 0 else 0.0
            pct_total_str = f"{pct_total_val:.1f}%"

            self.summary_tree.insert(
                "",
                tk.END,
                values=(
                    c["cat_name"],
                    format_currency(budget),
                    format_currency(spent),
                    pct_budget_str,
                    pct_total_str,
                    f"{c['txn_count']} txns",
                ),
            )
