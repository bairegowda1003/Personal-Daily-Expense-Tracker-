"""
Monthly Budget Analyzer Module
Analyzes spending versus allocated category budgets, detects overspending,
and provides visual health indicators and progress trackers.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date
from typing import Optional, Callable, Dict, List, Any

from database.db_connection import db_manager
from utils.validators import validate_budget
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
    get_month_list,
    get_year_list,
    format_currency,
)


class BudgetAnalyzerView(ttk.Frame):
    """
    GUI component for evaluating monthly category budgets against actual expenditure.
    """

    def __init__(self, parent: tk.Widget, on_change_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.on_change_callback = on_change_callback
        self.current_analysis: List[Dict[str, Any]] = []

        self.configure(style="TFrame")
        self._build_ui()
        self.refresh_analysis()

    def _build_ui(self) -> None:
        """Construct the budget analyzer layout."""
        container = tk.Frame(self, bg=COLOR_BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header with Month/Year Selection
        header_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        # Title & Subtitle on left
        left_header = tk.Frame(header_frame, bg=COLOR_BG_MAIN)
        left_header.pack(side=tk.LEFT)

        title_lbl = tk.Label(
            left_header,
            text="🎯 Monthly Budget Analyzer & Variance Report",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            left_header,
            text="Evaluate budget consumption, remaining allowances, and overspending alerts across categories.",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Month/Year Selector on right
        selector_card = tk.Frame(
            header_frame,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=12,
            pady=6,
        )
        selector_card.pack(side=tk.RIGHT)

        tk.Label(selector_card, text="Select Period:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG).pack(side=tk.LEFT, padx=(0, 8))

        today = date.today()

        # Month combobox
        self.month_var = tk.StringVar()
        month_names = [m[1] for m in get_month_list()]
        self.combo_month = ttk.Combobox(
            selector_card,
            textvariable=self.month_var,
            values=month_names,
            state="readonly",
            width=11,
            font=FONT_BODY,
        )
        self.combo_month.current(today.month - 1)
        self.combo_month.pack(side=tk.LEFT, padx=(0, 8))
        self.combo_month.bind("<<ComboboxSelected>>", lambda e: self.refresh_analysis())

        # Year combobox
        self.year_var = tk.StringVar(value=str(today.year))
        years = [str(y) for y in get_year_list()]
        self.combo_year = ttk.Combobox(
            selector_card,
            textvariable=self.year_var,
            values=years,
            state="readonly",
            width=7,
            font=FONT_BODY,
        )
        self.combo_year.pack(side=tk.LEFT, padx=(0, 8))
        self.combo_year.bind("<<ComboboxSelected>>", lambda e: self.refresh_analysis())

        btn_refresh = tk.Button(
            selector_card,
            text="🔄 Recalculate",
            command=self.refresh_analysis,
            bg=COLOR_PRIMARY,
            fg="white",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=2,
        )
        btn_refresh.pack(side=tk.LEFT)

        # Overview Metric Cards
        self._build_metric_cards(container)

        # Main Table Card
        self._build_table_card(container)

    def _build_metric_cards(self, parent: tk.Widget) -> None:
        """Top row of 4 KPI cards for the selected month."""
        cards_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        cards_frame.pack(fill=tk.X, pady=(0, 15))

        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="kpi")

        # 1. Total Budget Card
        self.val_budget, _ = self._create_kpi_card(cards_frame, 0, "TOTAL MONTHLY BUDGET", "₹ 0.00", COLOR_PRIMARY, "All Categories Combined")

        # 2. Total Spent Card
        self.val_spent, _ = self._create_kpi_card(cards_frame, 1, "TOTAL SPENT THIS MONTH", "₹ 0.00", "#7C3AED", "Actual Outflow")

        # 3. Overall Remaining Card
        self.val_remaining, self.sub_remaining = self._create_kpi_card(cards_frame, 2, "REMAINING BUDGET", "₹ 0.00", COLOR_SUCCESS, "Available Buffer")

        # 4. Budget Health Status Card
        self.val_health, self.sub_health = self._create_kpi_card(cards_frame, 3, "OVERALL STATUS", "Healthy", COLOR_SUCCESS, "0 Overspending Categories")

    def _create_kpi_card(self, parent: tk.Widget, col: int, label: str, init_val: str, color: str, subtext: str):
        card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=5)

        # Left border indicator
        accent = tk.Frame(card, bg=color, width=4)
        accent.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        content = tk.Frame(card, bg=COLOR_CARD_BG)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        lbl = tk.Label(content, text=label, font=FONT_METRIC_LABEL, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
        lbl.pack(anchor=tk.W)

        val = tk.Label(content, text=init_val, font=FONT_METRIC_VALUE, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        val.pack(anchor=tk.W, pady=(2, 2))

        sub = tk.Label(content, text=subtext, font=("Segoe UI", 8), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
        sub.pack(anchor=tk.W)

        return val, sub

    def _build_table_card(self, parent: tk.Widget) -> None:
        """Card containing the category budget analysis breakdown table."""
        card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=15,
            pady=15,
        )
        card.pack(fill=tk.BOTH, expand=True)

        # Action bar above table
        top_bar = tk.Frame(card, bg=COLOR_CARD_BG)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        title = tk.Label(top_bar, text="Category Variance & Budget Utilization", font=FONT_HEADING, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        title.pack(side=tk.LEFT)

        # Legend badges on right
        legend_frame = tk.Frame(top_bar, bg=COLOR_CARD_BG)
        legend_frame.pack(side=tk.RIGHT)

        self._create_legend_badge(legend_frame, "● Within Budget (<75%)", "#10B981")
        self._create_legend_badge(legend_frame, "▲ Warning (75%-100%)", "#F59E0B")
        self._create_legend_badge(legend_frame, "✖ Over Budget (>100%)", "#EF4444")

        # Treeview for detailed budget lines
        columns = ("name", "budget", "spent", "remaining", "percent", "status")
        self.tree = ttk.Treeview(card, columns=columns, show="headings", selectmode="browse", height=13)

        self.tree.heading("name", text="Category Name")
        self.tree.heading("budget", text="Monthly Budget (₹)")
        self.tree.heading("spent", text="Actual Spent (₹)")
        self.tree.heading("remaining", text="Remaining (₹)")
        self.tree.heading("percent", text="Utilization %")
        self.tree.heading("status", text="Budget Status")

        self.tree.column("name", width=160, anchor=tk.W)
        self.tree.column("budget", width=130, anchor=tk.E)
        self.tree.column("spent", width=130, anchor=tk.E)
        self.tree.column("remaining", width=130, anchor=tk.E)
        self.tree.column("percent", width=120, anchor=tk.CENTER)
        self.tree.column("status", width=140, anchor=tk.CENTER)

        # Custom tag colors
        self.tree.tag_configure("within", foreground="#047857")
        self.tree.tag_configure("warning", foreground="#B45309", background="#FFFBEB")
        self.tree.tag_configure("over", foreground="#B91C1C", background="#FEF2F2")

        v_scroll = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom Bar: Quick Adjust Category Budget
        bottom_bar = tk.Frame(card, bg=COLOR_CARD_BG)
        bottom_bar.pack(fill=tk.X, pady=(12, 0))

        btn_edit_budget = tk.Button(
            bottom_bar,
            text="✏️ Adjust Selected Category Budget",
            command=self._handle_quick_adjust_budget,
            bg="#DBEAFE",
            fg=COLOR_PRIMARY,
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=5,
        )
        btn_edit_budget.pack(side=tk.LEFT)

        hint = tk.Label(
            bottom_bar,
            text="Tip: Double-click a row to quickly revise its monthly budget.",
            font=("Segoe UI", 9),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG,
        )
        hint.pack(side=tk.LEFT, padx=15)

        self.tree.bind("<Double-1>", lambda e: self._handle_quick_adjust_budget())

    def _create_legend_badge(self, parent: tk.Widget, text: str, color: str):
        lbl = tk.Label(parent, text=text, font=FONT_BODY_BOLD, fg=color, bg=COLOR_CARD_BG, padx=8)
        lbl.pack(side=tk.LEFT)

    def _get_selected_period(self) -> tuple:
        """Return (year_int, month_int) currently selected in dropdowns."""
        # Month
        m_name = self.month_var.get()
        month_idx = 1
        for idx, name in get_month_list():
            if name == m_name:
                month_idx = idx
                break

        # Year
        try:
            year_val = int(self.year_var.get())
        except ValueError:
            year_val = date.today().year

        return year_val, month_idx

    def refresh_analysis(self) -> None:
        """Query database for selected month's budget vs actual data and redraw metrics/table."""
        year, month = self._get_selected_period()

        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            summary = db_manager.get_monthly_summary(year, month)
            analysis = db_manager.get_category_budget_analysis(year, month)
            self.current_analysis = analysis

            total_budget = summary["total_budget"]
            total_spent = summary["total_spent"]
            overall_remaining = total_budget - total_spent

            # Update KPI card values
            self.val_budget.config(text=format_currency(total_budget))
            self.val_spent.config(text=format_currency(total_spent))
            self.val_remaining.config(
                text=format_currency(overall_remaining),
                fg=COLOR_SUCCESS if overall_remaining >= 0 else COLOR_DANGER,
            )

            # Check overspending count
            over_count = sum(1 for item in analysis if item["status"] == "Over Budget")
            warn_count = sum(1 for item in analysis if item["status"] == "Warning")

            if over_count > 0:
                self.val_health.config(text=f"⚠️ {over_count} Over Budget", fg=COLOR_DANGER)
                self.sub_health.config(text=f"{over_count} over / {warn_count} near cap")
            elif warn_count > 0:
                self.val_health.config(text=f"⚡ {warn_count} Nearing Cap", fg=COLOR_WARNING)
                self.sub_health.config(text="Caution advised")
            else:
                self.val_health.config(text="✅ Healthy", fg=COLOR_SUCCESS)
                self.sub_health.config(text="All categories within limits")

            # Populate Treeview
            for item in analysis:
                status = item["status"]
                tag = "within"
                status_icon = "● Within Budget"
                if status == "Over Budget":
                    tag = "over"
                    status_icon = "✖ Over Budget"
                elif status == "Warning":
                    tag = "warning"
                    status_icon = "▲ Warning (≥75%)"

                # Utilization text
                if item["monthly_budget"] == 0:
                    pct_str = "N/A (No Cap)" if item["amount_spent"] == 0 else "Over (Cap: ₹0)"
                else:
                    pct_str = f"{item['percent_consumed']:.1f}%"

                # Remaining text
                rem_val = item["remaining"]
                rem_str = format_currency(rem_val) if rem_val >= 0 else f"- {format_currency(abs(rem_val))}"

                self.tree.insert(
                    "",
                    tk.END,
                    iid=str(item["cat_id"]),
                    values=(
                        item["cat_name"],
                        format_currency(item["monthly_budget"]),
                        format_currency(item["amount_spent"]),
                        rem_str,
                        pct_str,
                        status_icon,
                    ),
                    tags=(tag,),
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to compute budget analysis: {e}")

    def _handle_quick_adjust_budget(self) -> None:
        """Prompt user with a clean input dialog to adjust category monthly budget."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a category from the table to adjust its budget.")
            return

        cat_id = int(selected[0])
        category = db_manager.get_category_by_id(cat_id)
        if not category:
            return

        curr_budget = category["monthly_budget"]
        new_val_str = simpledialog.askstring(
            "Adjust Monthly Budget",
            f"Enter new monthly budget for '{category['cat_name']}' (₹):",
            initialvalue=f"{curr_budget:.2f}",
            parent=self,
        )

        if new_val_str is None:
            return  # User canceled

        is_valid, parsed_budget, err = validate_budget(new_val_str)
        if not is_valid:
            messagebox.showerror("Invalid Budget", err)
            return

        try:
            db_manager.update_category_budget(cat_id, parsed_budget)
            messagebox.showinfo("Success", f"Monthly budget for '{category['cat_name']}' updated to {format_currency(parsed_budget)}.")
            self.refresh_analysis()

            if self.on_change_callback:
                self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update budget: {e}")
