"""
Expense History Module
Provides advanced querying, searching, multi-criteria filtering,
sorting, and CSV export for recorded expenses.
"""

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from typing import Optional, Callable, Dict, List

from tkcalendar import DateEntry

from database.db_connection import db_manager
from utils.helpers import (
    COLOR_BG_MAIN,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_DANGER,
    COLOR_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_TITLE,
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_BODY,
    FONT_BODY_BOLD,
    get_month_list,
    get_year_list,
    format_currency,
    format_date_display,
)


class ExpenseHistoryView(ttk.Frame):
    """
    GUI component for browsing, searching, filtering, and exporting expense history.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_edit_expense_callback: Optional[Callable[[int], None]] = None,
        on_change_callback: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self.on_edit_expense_callback = on_edit_expense_callback
        self.on_change_callback = on_change_callback
        self.category_map: Dict[str, int] = {}

        self.configure(style="TFrame")
        self._build_ui()
        self.refresh_filter_options()
        self.apply_filters()

    def _build_ui(self) -> None:
        """Construct the UI layout."""
        container = tk.Frame(self, bg=COLOR_BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_lbl = tk.Label(
            header_frame,
            text="📜 Expense History & Audit Trail",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Search, filter by category or date, sort by amount, and export complete transaction reports.",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Filter Panel Card
        self._build_filter_card(container)

        # Table & Summary Card
        self._build_table_card(container)

    def _build_filter_card(self, parent: tk.Widget) -> None:
        """Filter control panel."""
        filter_card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=15,
            pady=12,
        )
        filter_card.pack(fill=tk.X, pady=(0, 15))

        # Row 1: Search, Category, Payment Mode, Sort
        row1 = tk.Frame(filter_card, bg=COLOR_CARD_BG)
        row1.pack(fill=tk.X, pady=(0, 8))

        # Search Box
        lbl_search = tk.Label(row1, text="🔍 Search:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_search.pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.entry_search = ttk.Entry(row1, textvariable=self.search_var, width=18, font=FONT_BODY)
        self.entry_search.pack(side=tk.LEFT, padx=(0, 15))
        self.entry_search.bind("<Return>", lambda e: self.apply_filters())

        # Category Filter
        lbl_cat = tk.Label(row1, text="Category:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_cat.pack(side=tk.LEFT, padx=(0, 5))

        self.filter_cat_var = tk.StringVar(value="All Categories")
        self.combo_cat = ttk.Combobox(row1, textvariable=self.filter_cat_var, state="readonly", width=14, font=FONT_BODY)
        self.combo_cat.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_cat.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Payment Mode Filter
        lbl_mode = tk.Label(row1, text="Payment Mode:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_mode.pack(side=tk.LEFT, padx=(0, 5))

        self.filter_mode_var = tk.StringVar(value="All")
        self.combo_mode = ttk.Combobox(
            row1,
            textvariable=self.filter_mode_var,
            values=["All", "Cash", "UPI", "Card"],
            state="readonly",
            width=8,
            font=FONT_BODY,
        )
        self.combo_mode.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_mode.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Sort Order
        lbl_sort = tk.Label(row1, text="Sort By:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_sort.pack(side=tk.LEFT, padx=(0, 5))

        self.sort_var = tk.StringVar(value="Date (Newest First)")
        self.combo_sort = ttk.Combobox(
            row1,
            textvariable=self.sort_var,
            values=[
                "Date (Newest First)",
                "Date (Oldest First)",
                "Amount (High to Low)",
                "Amount (Low to High)",
            ],
            state="readonly",
            width=18,
            font=FONT_BODY,
        )
        self.combo_sort.pack(side=tk.LEFT, padx=(0, 10))
        self.combo_sort.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Row 2: Date Range, Month/Year Filter, Action Buttons
        row2 = tk.Frame(filter_card, bg=COLOR_CARD_BG)
        row2.pack(fill=tk.X)

        # Quick Month & Year Filter
        lbl_month = tk.Label(row2, text="Month:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_month.pack(side=tk.LEFT, padx=(0, 5))

        self.month_var = tk.StringVar(value="All Months")
        month_options = ["All Months"] + [m_name for _, m_name in get_month_list()]
        self.combo_month = ttk.Combobox(row2, textvariable=self.month_var, values=month_options, state="readonly", width=11, font=FONT_BODY)
        self.combo_month.pack(side=tk.LEFT, padx=(0, 10))
        self.combo_month.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        lbl_year = tk.Label(row2, text="Year:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_year.pack(side=tk.LEFT, padx=(0, 5))

        self.year_var = tk.StringVar(value=str(date.today().year))
        year_options = ["All Years"] + [str(y) for y in get_year_list()]
        self.combo_year = ttk.Combobox(row2, textvariable=self.year_var, values=year_options, state="readonly", width=9, font=FONT_BODY)
        self.combo_year.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_year.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Date Range Checkbox & Pickers
        self.enable_date_range_var = tk.BooleanVar(value=False)
        self.chk_date_range = ttk.Checkbutton(
            row2,
            text="Custom Date Range:",
            variable=self.enable_date_range_var,
            command=self._toggle_date_range_state,
        )
        self.chk_date_range.pack(side=tk.LEFT, padx=(0, 5))

        self.start_date_picker = DateEntry(
            row2,
            width=11,
            background="#0F172A",
            foreground="white",
            date_pattern="yyyy-mm-dd",
            font=FONT_BODY,
            state="disabled",
        )
        self.start_date_picker.pack(side=tk.LEFT, padx=(0, 5))

        lbl_to = tk.Label(row2, text="to", font=FONT_BODY, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG)
        lbl_to.pack(side=tk.LEFT, padx=(0, 5))

        self.end_date_picker = DateEntry(
            row2,
            width=11,
            background="#0F172A",
            foreground="white",
            date_pattern="yyyy-mm-dd",
            font=FONT_BODY,
            state="disabled",
        )
        self.end_date_picker.pack(side=tk.LEFT, padx=(0, 15))

        # Buttons on right of Row 2
        btn_apply = tk.Button(
            row2,
            text="Filter",
            command=self.apply_filters,
            bg=COLOR_PRIMARY,
            fg="white",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=3,
        )
        btn_apply.pack(side=tk.LEFT, padx=3)

        btn_reset = tk.Button(
            row2,
            text="Reset",
            command=self.reset_filters,
            bg="#E2E8F0",
            fg=COLOR_TEXT_PRIMARY,
            font=FONT_BODY,
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=3,
        )
        btn_reset.pack(side=tk.LEFT, padx=3)

        btn_export = tk.Button(
            row2,
            text="📥 Export CSV",
            command=self.export_to_csv,
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=3,
        )
        btn_export.pack(side=tk.RIGHT)

    def _build_table_card(self, parent: tk.Widget) -> None:
        """Table display and summary banner."""
        card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=15,
            pady=15,
        )
        card.pack(fill=tk.BOTH, expand=True)

        # Summary Bar (Top of table)
        summary_bar = tk.Frame(card, bg="#F1F5F9", padx=15, pady=8)
        summary_bar.pack(fill=tk.X, pady=(0, 10))

        self.lbl_records_count = tk.Label(
            summary_bar,
            text="Filtered Transactions: 0",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg="#F1F5F9",
        )
        self.lbl_records_count.pack(side=tk.LEFT)

        self.lbl_total_filtered = tk.Label(
            summary_bar,
            text="Total Spending: ₹ 0.00",
            font=FONT_HEADING,
            fg=COLOR_PRIMARY,
            bg="#F1F5F9",
        )
        self.lbl_total_filtered.pack(side=tk.RIGHT)

        # Treeview Table
        table_container = tk.Frame(card, bg=COLOR_CARD_BG)
        table_container.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "date", "category", "description", "payment_mode", "amount")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("id", text="Exp ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")
        self.tree.heading("payment_mode", text="Payment Mode")
        self.tree.heading("amount", text="Amount (₹)")

        self.tree.column("id", width=65, anchor=tk.CENTER)
        self.tree.column("date", width=110, anchor=tk.CENTER)
        self.tree.column("category", width=140, anchor=tk.W)
        self.tree.column("description", width=320, anchor=tk.W)
        self.tree.column("payment_mode", width=110, anchor=tk.CENTER)
        self.tree.column("amount", width=140, anchor=tk.E)

        v_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Bottom Action Bar
        bottom_bar = tk.Frame(card, bg=COLOR_CARD_BG)
        bottom_bar.pack(fill=tk.X, pady=(10, 0))

        btn_edit = tk.Button(
            bottom_bar,
            text="✏️ Edit in Expense Manager",
            command=self._handle_edit_selected,
            bg="#DBEAFE",
            fg=COLOR_PRIMARY,
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        btn_edit.pack(side=tk.LEFT, padx=(0, 8))

        btn_delete = tk.Button(
            bottom_bar,
            text="🗑️ Delete Selected",
            command=self._handle_delete_selected,
            bg="#FEE2E2",
            fg=COLOR_DANGER,
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        btn_delete.pack(side=tk.LEFT)

    def _toggle_date_range_state(self) -> None:
        """Enable or disable date pickers based on checkbox."""
        state = "normal" if self.enable_date_range_var.get() else "disabled"
        self.start_date_picker.configure(state=state)
        self.end_date_picker.configure(state=state)
        self.apply_filters()

    def refresh_filter_options(self) -> None:
        """Reload category names into combobox."""
        categories = db_manager.get_all_categories()
        self.category_map = {c["cat_name"]: c["cat_id"] for c in categories}
        cat_options = ["All Categories"] + list(self.category_map.keys())
        self.combo_cat["values"] = cat_options
        if not self.filter_cat_var.get():
            self.filter_cat_var.set("All Categories")

    def reset_filters(self) -> None:
        """Reset all filter controls to default."""
        self.search_var.set("")
        self.filter_cat_var.set("All Categories")
        self.filter_mode_var.set("All")
        self.month_var.set("All Months")
        self.year_var.set(str(date.today().year))
        self.sort_var.set("Date (Newest First)")
        self.enable_date_range_var.set(False)
        self.start_date_picker.configure(state="disabled")
        self.end_date_picker.configure(state="disabled")
        self.apply_filters()

    def apply_filters(self) -> None:
        """Execute database query with currently active filters."""
        # 1. Search text
        search = self.search_var.get().strip() or None

        # 2. Category
        cat_name = self.filter_cat_var.get()
        cat_id = self.category_map.get(cat_name) if cat_name != "All Categories" else None

        # 3. Payment Mode
        mode = self.filter_mode_var.get()
        payment_mode = mode if mode != "All" else None

        # 4. Custom Date Range vs Month/Year
        start_date = None
        end_date = None
        year = None
        month = None

        if self.enable_date_range_var.get():
            try:
                start_date = self.start_date_picker.get_date().strftime("%Y-%m-%d")
                end_date = self.end_date_picker.get_date().strftime("%Y-%m-%d")
            except Exception:
                pass
        else:
            # Check Year
            y_val = self.year_var.get()
            if y_val != "All Years" and y_val.isdigit():
                year = int(y_val)

            # Check Month
            m_val = self.month_var.get()
            if m_val != "All Months":
                for m_num, m_name in get_month_list():
                    if m_name == m_val:
                        month = m_num
                        break

        # 5. Sort By
        sort_map = {
            "Date (Newest First)": "date_desc",
            "Date (Oldest First)": "date_asc",
            "Amount (High to Low)": "amount_desc",
            "Amount (Low to High)": "amount_asc",
        }
        sort_by = sort_map.get(self.sort_var.get(), "date_desc")

        # Fetch records
        try:
            records = db_manager.get_filtered_expenses(
                search=search,
                cat_id=cat_id,
                payment_mode=payment_mode,
                start_date=start_date,
                end_date=end_date,
                month=month,
                year=year,
                sort_by=sort_by,
            )

            # Update Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            total_sum = 0.0
            for r in records:
                total_sum += float(r["amount"])
                self.tree.insert(
                    "",
                    tk.END,
                    iid=str(r["exp_id"]),
                    values=(
                        r["exp_id"],
                        format_date_display(r["exp_date"]),
                        r["cat_name"],
                        r["description"],
                        r["payment_mode"],
                        format_currency(r["amount"]),
                    ),
                )

            # Update Summary labels
            self.lbl_records_count.config(text=f"Filtered Transactions: {len(records)}")
            self.lbl_total_filtered.config(text=f"Total Spending: {format_currency(total_sum)}")

        except Exception as e:
            messagebox.showerror("Query Error", f"Failed to retrieve expense history: {e}")

    def _handle_edit_selected(self) -> None:
        """Switch to Expense Manager view with the selected record preloaded."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select an expense row to edit.")
            return

        exp_id = int(selected[0])
        if self.on_edit_expense_callback:
            self.on_edit_expense_callback(exp_id)

    def _handle_delete_selected(self) -> None:
        """Delete selected expense with confirmation."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select an expense row to delete.")
            return

        exp_id = int(selected[0])
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to permanently delete Expense #{exp_id}?",
        )
        if not confirm:
            return

        try:
            db_manager.delete_expense(exp_id)
            messagebox.showinfo("Deleted", f"Expense #{exp_id} successfully deleted.")
            self.apply_filters()

            if self.on_change_callback:
                self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete expense: {e}")

    def export_to_csv(self) -> None:
        """Export currently filtered records to a CSV spreadsheet."""
        children = self.tree.get_children()
        if not children:
            messagebox.showinfo("No Data", "There are no transactions to export under the current filter.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")],
            initialfile=f"expense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Expense ID", "Date", "Category", "Description", "Payment Mode", "Amount (INR)"])

                for item in children:
                    vals = self.tree.item(item, "values")
                    # Clean currency symbol from amount
                    cleaned_amt = str(vals[5]).replace("₹", "").replace(",", "").strip()
                    writer.writerow([vals[0], vals[1], vals[2], vals[3], vals[4], cleaned_amt])

            messagebox.showinfo("Export Successful", f"Successfully exported {len(children)} transaction records to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not save CSV file: {e}")
