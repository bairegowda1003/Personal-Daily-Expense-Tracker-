"""
Expense Management Module
Allows users to record, update, delete, and view daily expenses.
Uses tkcalendar DateEntry for date picking and ttk components for form inputs.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from typing import Optional, Callable, Dict, List

from tkcalendar import DateEntry

from database.db_connection import db_manager
from utils.validators import (
    validate_amount,
    validate_description,
    validate_payment_mode,
    validate_date,
)
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
    format_currency,
    format_date_display,
)


class ExpenseManagerView(ttk.Frame):
    """
    GUI component for creating, modifying, and deleting daily expenses.
    """

    def __init__(self, parent: tk.Widget, on_change_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.on_change_callback = on_change_callback
        self.selected_exp_id: Optional[int] = None
        self.category_map: Dict[str, int] = {}  # cat_name -> cat_id

        self.configure(style="TFrame")
        self._build_ui()
        self.refresh_categories()
        self.load_expenses()

    def _build_ui(self) -> None:
        """Construct the layout."""
        container = tk.Frame(self, bg=COLOR_BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_lbl = tk.Label(
            header_frame,
            text="➕ Daily Expense Management",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Record daily expenditures, edit past transactions, and classify payments by mode.",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Main 2-column layout
        content_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Form Column (Left ~380px)
        self._build_form_card(content_frame)

        # Expense Table Column (Right)
        self._build_table_card(content_frame)

    def _build_form_card(self, parent: tk.Widget) -> None:
        """Expense entry & update form."""
        form_card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=20,
            pady=20,
            width=380,
        )
        form_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        form_card.pack_propagate(False)

        # Form Title
        self.form_title_var = tk.StringVar(value="Add New Expense")
        lbl_form_title = tk.Label(
            form_card,
            textvariable=self.form_title_var,
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        lbl_form_title.pack(anchor=tk.W, pady=(0, 15))

        # 1. Amount
        lbl_amount = tk.Label(form_card, text="Amount (₹) *", font=FONT_SUBHEADING, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_amount.pack(anchor=tk.W, pady=(2, 2))

        self.amount_var = tk.StringVar()
        self.entry_amount = ttk.Entry(form_card, textvariable=self.amount_var, font=FONT_BODY)
        self.entry_amount.pack(fill=tk.X, pady=(0, 10), ipady=3)

        # 2. Description
        lbl_desc = tk.Label(form_card, text="Description / Purpose *", font=FONT_SUBHEADING, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_desc.pack(anchor=tk.W, pady=(2, 2))

        self.desc_var = tk.StringVar()
        self.entry_desc = ttk.Entry(form_card, textvariable=self.desc_var, font=FONT_BODY)
        self.entry_desc.pack(fill=tk.X, pady=(0, 10), ipady=3)

        # 3. Category
        lbl_cat = tk.Label(form_card, text="Category *", font=FONT_SUBHEADING, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_cat.pack(anchor=tk.W, pady=(2, 2))

        self.cat_var = tk.StringVar()
        self.combo_category = ttk.Combobox(form_card, textvariable=self.cat_var, state="readonly", font=FONT_BODY)
        self.combo_category.pack(fill=tk.X, pady=(0, 10), ipady=3)

        # 4. Payment Mode
        lbl_mode = tk.Label(form_card, text="Payment Mode *", font=FONT_SUBHEADING, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_mode.pack(anchor=tk.W, pady=(2, 2))

        self.mode_var = tk.StringVar(value="UPI")
        self.combo_mode = ttk.Combobox(
            form_card,
            textvariable=self.mode_var,
            values=["Cash", "UPI", "Card"],
            state="readonly",
            font=FONT_BODY,
        )
        self.combo_mode.pack(fill=tk.X, pady=(0, 10), ipady=3)

        # 5. Date
        lbl_date = tk.Label(form_card, text="Expense Date *", font=FONT_SUBHEADING, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl_date.pack(anchor=tk.W, pady=(2, 2))

        self.date_entry = DateEntry(
            form_card,
            width=14,
            background="#0F172A",
            foreground="white",
            borderwidth=1,
            date_pattern="yyyy-mm-dd",
            font=FONT_BODY,
        )
        self.date_entry.pack(fill=tk.X, pady=(0, 20), ipady=3)

        # Action Buttons
        self.btn_add = tk.Button(
            form_card,
            text="➕ Add Expense",
            command=self._handle_add,
            bg=COLOR_PRIMARY,
            fg="white",
            activebackground=COLOR_PRIMARY_HOVER,
            activeforeground="white",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            pady=6,
        )
        self.btn_add.pack(fill=tk.X, pady=(0, 6))

        self.btn_update = tk.Button(
            form_card,
            text="💾 Update Expense",
            command=self._handle_update,
            bg="#16A34A",
            fg="white",
            activebackground="#15803D",
            activeforeground="white",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            pady=6,
            state=tk.DISABLED,
        )
        self.btn_update.pack(fill=tk.X, pady=(0, 6))

        self.btn_delete = tk.Button(
            form_card,
            text="🗑️ Delete Expense",
            command=self._handle_delete,
            bg="#FEE2E2",
            fg=COLOR_DANGER,
            activebackground="#FECACA",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            pady=6,
            state=tk.DISABLED,
        )
        self.btn_delete.pack(fill=tk.X, pady=(0, 6))

        self.btn_clear = tk.Button(
            form_card,
            text="🔄 Clear Form",
            command=self._clear_form,
            bg="#E2E8F0",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#CBD5E1",
            font=FONT_BODY,
            relief=tk.FLAT,
            cursor="hand2",
            pady=6,
        )
        self.btn_clear.pack(fill=tk.X)

    def _build_table_card(self, parent: tk.Widget) -> None:
        """Right panel: recent expenses table."""
        table_card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=20,
            pady=20,
        )
        table_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Top Bar
        top_bar = tk.Frame(table_card, bg=COLOR_CARD_BG)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        tbl_title = tk.Label(
            top_bar,
            text="Recorded Expenses",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        tbl_title.pack(side=tk.LEFT)

        self.count_lbl = tk.Label(
            top_bar,
            text="(0 entries)",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG,
        )
        self.count_lbl.pack(side=tk.LEFT, padx=10)

        btn_refresh = tk.Button(
            top_bar,
            text="🔄 Refresh",
            command=self.load_expenses,
            bg="#F1F5F9",
            fg=COLOR_TEXT_PRIMARY,
            font=FONT_BODY,
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=3,
        )
        btn_refresh.pack(side=tk.RIGHT)

        # Table Treeview
        columns = ("id", "date", "category", "description", "payment_mode", "amount")
        self.tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=15,
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")
        self.tree.heading("payment_mode", text="Payment Mode")
        self.tree.heading("amount", text="Amount (₹)")

        self.tree.column("id", width=45, anchor=tk.CENTER)
        self.tree.column("date", width=95, anchor=tk.CENTER)
        self.tree.column("category", width=120, anchor=tk.W)
        self.tree.column("description", width=220, anchor=tk.W)
        self.tree.column("payment_mode", width=95, anchor=tk.CENTER)
        self.tree.column("amount", width=110, anchor=tk.E)

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_card, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_card, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def refresh_categories(self) -> None:
        """Reload category names from database into combobox."""
        categories = db_manager.get_all_categories()
        self.category_map = {c["cat_name"]: c["cat_id"] for c in categories}
        cat_names = list(self.category_map.keys())
        self.combo_category["values"] = cat_names
        if cat_names and not self.cat_var.get():
            self.combo_category.current(0)

    def load_expenses(self) -> None:
        """Fetch all expenses and populate the treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        expenses = db_manager.get_all_expenses()
        for exp in expenses:
            self.tree.insert(
                "",
                tk.END,
                iid=str(exp["exp_id"]),
                values=(
                    exp["exp_id"],
                    format_date_display(exp["exp_date"]),
                    exp["cat_name"],
                    exp["description"],
                    exp["payment_mode"],
                    format_currency(exp["amount"]),
                ),
            )

        self.count_lbl.config(text=f"({len(expenses)} entries)")

    def _on_tree_select(self, event=None) -> None:
        """Load selected expense into the form fields."""
        selected = self.tree.selection()
        if not selected:
            return

        exp_id = int(selected[0])
        expense = db_manager.get_expense_by_id(exp_id)
        if not expense:
            return

        self.selected_exp_id = exp_id
        self.amount_var.set(f"{expense['amount']:.2f}")
        self.desc_var.set(expense["description"])
        self.cat_var.set(expense["cat_name"])
        self.mode_var.set(expense["payment_mode"])

        # Set date in DateEntry
        try:
            dt = datetime.strptime(expense["exp_date"], "%Y-%m-%d").date()
            self.date_entry.set_date(dt)
        except Exception:
            pass

        self.form_title_var.set(f"Edit Expense #{exp_id}")
        self.btn_add.config(state=tk.DISABLED)
        self.btn_update.config(state=tk.NORMAL)
        self.btn_delete.config(state=tk.NORMAL)

    def _clear_form(self) -> None:
        """Reset inputs and button states."""
        self.selected_exp_id = None
        self.amount_var.set("")
        self.desc_var.set("")
        self.mode_var.set("UPI")
        self.date_entry.set_date(date.today())
        self.form_title_var.set("Add New Expense")

        self.btn_add.config(state=tk.NORMAL)
        self.btn_update.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)

        self.tree.selection_remove(self.tree.selection())

    def _validate_inputs(self) -> Optional[tuple]:
        """Validate all form inputs, displaying messageboxes on error."""
        # 1. Amount
        is_amt_valid, amt, amt_err = validate_amount(self.amount_var.get())
        if not is_amt_valid:
            messagebox.showerror("Validation Error", amt_err)
            self.entry_amount.focus_set()
            return None

        # 2. Description
        is_desc_valid, desc, desc_err = validate_description(self.desc_var.get())
        if not is_desc_valid:
            messagebox.showerror("Validation Error", desc_err)
            self.entry_desc.focus_set()
            return None

        # 3. Category
        cat_name = self.cat_var.get().strip()
        if not cat_name or cat_name not in self.category_map:
            messagebox.showerror("Validation Error", "Please select a valid expense category.")
            self.combo_category.focus_set()
            return None
        cat_id = self.category_map[cat_name]

        # 4. Payment Mode
        is_mode_valid, mode, mode_err = validate_payment_mode(self.mode_var.get())
        if not is_mode_valid:
            messagebox.showerror("Validation Error", mode_err)
            self.combo_mode.focus_set()
            return None

        # 5. Date
        try:
            raw_date = self.date_entry.get_date().strftime("%Y-%m-%d")
        except Exception:
            raw_date = str(self.date_entry.get())

        is_date_valid, date_str, date_err = validate_date(raw_date)
        if not is_date_valid:
            messagebox.showerror("Validation Error", date_err)
            return None

        return (cat_id, amt, date_str, desc, mode)

    def _handle_add(self) -> None:
        """Add expense to database."""
        validated = self._validate_inputs()
        if not validated:
            return

        cat_id, amt, exp_date, desc, mode = validated

        try:
            new_id = db_manager.add_expense(cat_id, amt, exp_date, desc, mode)
            messagebox.showinfo("Success", f"Expense #{new_id} of {format_currency(amt)} saved successfully.")
            self._clear_form()
            self.load_expenses()

            if self.on_change_callback:
                self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to record expense: {e}")

    def _handle_update(self) -> None:
        """Update existing expense in database."""
        if self.selected_exp_id is None:
            messagebox.showinfo("Selection Required", "Please select an expense to update.")
            return

        validated = self._validate_inputs()
        if not validated:
            return

        cat_id, amt, exp_date, desc, mode = validated

        try:
            db_manager.update_expense(self.selected_exp_id, cat_id, amt, exp_date, desc, mode)
            messagebox.showinfo("Success", f"Expense #{self.selected_exp_id} updated successfully.")
            self._clear_form()
            self.load_expenses()

            if self.on_change_callback:
                self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update expense: {e}")

    def _handle_delete(self) -> None:
        """Delete expense after confirmation."""
        if self.selected_exp_id is None:
            messagebox.showinfo("Selection Required", "Please select an expense to delete.")
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to permanently delete Expense #{self.selected_exp_id}?\n\nThis action cannot be undone.",
        )
        if not confirm:
            return

        try:
            db_manager.delete_expense(self.selected_exp_id)
            messagebox.showinfo("Deleted", f"Expense #{self.selected_exp_id} has been deleted.")
            self._clear_form()
            self.load_expenses()

            if self.on_change_callback:
                self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete expense: {e}")

    def load_expense_for_external_edit(self, exp_id: int) -> None:
        """Allow other tabs (e.g. Expense History) to load a record directly for editing."""
        expense = db_manager.get_expense_by_id(exp_id)
        if not expense:
            return

        self.selected_exp_id = exp_id
        self.amount_var.set(f"{expense['amount']:.2f}")
        self.desc_var.set(expense["description"])
        self.cat_var.set(expense["cat_name"])
        self.mode_var.set(expense["payment_mode"])

        try:
            dt = datetime.strptime(expense["exp_date"], "%Y-%m-%d").date()
            self.date_entry.set_date(dt)
        except Exception:
            pass

        self.form_title_var.set(f"Edit Expense #{exp_id}")
        self.btn_add.config(state=tk.DISABLED)
        self.btn_update.config(state=tk.NORMAL)
        self.btn_delete.config(state=tk.NORMAL)

        # Highlight in treeview if present
        if str(exp_id) in self.tree.get_children():
            self.tree.selection_set(str(exp_id))
            self.tree.see(str(exp_id))
