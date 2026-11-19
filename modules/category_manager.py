"""
Category Management Module
Handles category creation, listing, updating, deletion, and monthly budget allocation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from database.db_connection import db_manager
from utils.validators import validate_category_name, validate_budget
from utils.helpers import (
    COLOR_BG_MAIN,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_DANGER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_TITLE,
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_BODY,
    FONT_BODY_BOLD,
    format_currency,
)


class CategoryManagerView(ttk.Frame):
    """
    GUI component for managing expense categories and their assigned monthly budgets.
    """

    def __init__(self, parent: tk.Widget, on_change_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.on_change_callback = on_change_callback
        self.selected_cat_id: Optional[int] = None

        self.configure(style="TFrame")
        self._build_ui()
        self.load_categories()

    def _build_ui(self) -> None:
        """Construct the category management interface."""
        # Main container with padding
        container = tk.Frame(self, bg=COLOR_BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header section
        header_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_lbl = tk.Label(
            header_frame,
            text="🏷️ Category & Budget Management",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Define expense classifications and assign monthly spending targets to keep your budget on track.",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Two-column content layout
        content_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Column 1: Add/Edit Form Card (Left ~360px)
        self._build_form_card(content_frame)

        # Column 2: Categories Table Card (Right)
        self._build_table_card(content_frame)

    def _build_form_card(self, parent: tk.Widget) -> None:
        """Left panel: Add/Edit category form."""
        form_card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=20,
            pady=20,
            width=360,
        )
        form_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        form_card.pack_propagate(False)

        # Card Title
        self.form_title_var = tk.StringVar(value="Add New Category")
        form_title = tk.Label(
            form_card,
            textvariable=self.form_title_var,
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        form_title.pack(anchor=tk.W, pady=(0, 15))

        # Field 1: Category Name
        lbl_name = tk.Label(
            form_card,
            text="Category Name *",
            font=FONT_SUBHEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        lbl_name.pack(anchor=tk.W, pady=(5, 3))

        self.name_var = tk.StringVar()
        self.entry_name = ttk.Entry(form_card, textvariable=self.name_var, font=FONT_BODY)
        self.entry_name.pack(fill=tk.X, pady=(0, 12), ipady=3)

        # Field 2: Monthly Budget
        lbl_budget = tk.Label(
            form_card,
            text="Monthly Budget (₹) *",
            font=FONT_SUBHEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        lbl_budget.pack(anchor=tk.W, pady=(5, 3))

        self.budget_var = tk.StringVar(value="0.00")
        self.entry_budget = ttk.Entry(form_card, textvariable=self.budget_var, font=FONT_BODY)
        self.entry_budget.pack(fill=tk.X, pady=(0, 8), ipady=3)

        hint_lbl = tk.Label(
            form_card,
            text="Set ₹0.00 if you do not wish to enforce a spending cap on this category.",
            font=("Segoe UI", 8),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG,
            wraplength=310,
            justify=tk.LEFT,
        )
        hint_lbl.pack(anchor=tk.W, pady=(0, 20))

        # Button Group
        btn_frame = tk.Frame(form_card, bg=COLOR_CARD_BG)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_save = tk.Button(
            btn_frame,
            text="➕ Save Category",
            command=self._handle_save,
            bg=COLOR_PRIMARY,
            fg="white",
            activebackground=COLOR_PRIMARY_HOVER,
            activeforeground="white",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            pady=6,
        )
        self.btn_save.pack(fill=tk.X, pady=(0, 8))

        self.btn_clear = tk.Button(
            btn_frame,
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

        # Info Note
        note_card = tk.Frame(form_card, bg="#F8FAFC", highlightbackground="#E2E8F0", highlightthickness=1, padx=10, pady=10)
        note_card.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        note_title = tk.Label(note_card, text="💡 Tip:", font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg="#F8FAFC")
        note_title.pack(anchor=tk.W)
        note_text = tk.Label(
            note_card,
            text="To delete a category, first delete or reassign all expenses recorded under it to maintain relational integrity.",
            font=("Segoe UI", 8),
            fg=COLOR_TEXT_SECONDARY,
            bg="#F8FAFC",
            wraplength=300,
            justify=tk.LEFT,
        )
        note_text.pack(anchor=tk.W, pady=(2, 0))

    def _build_table_card(self, parent: tk.Widget) -> None:
        """Right panel: Category list table with actions."""
        table_card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
            padx=20,
            pady=20,
        )
        table_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Table Header Actions
        top_bar = tk.Frame(table_card, bg=COLOR_CARD_BG)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        tbl_title = tk.Label(
            top_bar,
            text="Existing Categories",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        tbl_title.pack(side=tk.LEFT)

        self.count_lbl = tk.Label(
            top_bar,
            text="(0 categories)",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG,
        )
        self.count_lbl.pack(side=tk.LEFT, padx=10)

        # Quick action buttons on right of header
        btn_delete = tk.Button(
            top_bar,
            text="🗑️ Delete Selected",
            command=self._handle_delete,
            bg="#FEE2E2",
            fg=COLOR_DANGER,
            activebackground="#FECACA",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=4,
        )
        btn_delete.pack(side=tk.RIGHT, padx=(5, 0))

        btn_edit = tk.Button(
            top_bar,
            text="✏️ Edit Selected",
            command=self._load_selected_for_edit,
            bg="#DBEAFE",
            fg=COLOR_PRIMARY,
            activebackground="#BFDBFE",
            font=FONT_BODY_BOLD,
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=4,
        )
        btn_edit.pack(side=tk.RIGHT, padx=5)

        # Treeview for categories
        columns = ("id", "name", "budget", "expenses_count", "total_spent")
        self.tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=15,
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Category Name")
        self.tree.heading("budget", text="Monthly Budget (₹)")
        self.tree.heading("expenses_count", text="Transactions")
        self.tree.heading("total_spent", text="Total Recorded Spent")

        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=180, anchor=tk.W)
        self.tree.column("budget", width=140, anchor=tk.E)
        self.tree.column("expenses_count", width=110, anchor=tk.CENTER)
        self.tree.column("total_spent", width=150, anchor=tk.E)

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)
        self.tree.bind("<Double-1>", lambda event: self._load_selected_for_edit())

    def load_categories(self) -> None:
        """Fetch categories and their stats from database and populate the treeview."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = db_manager.get_connection()
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT c.cat_id, c.cat_name, c.monthly_budget,
                           COUNT(e.exp_id) as txn_count,
                           COALESCE(SUM(e.amount), 0.0) as total_spent
                    FROM categories c
                    LEFT JOIN expenses e ON c.cat_id = e.cat_id
                    GROUP BY c.cat_id, c.cat_name, c.monthly_budget
                    ORDER BY c.cat_name ASC
                    """
                )
                rows = cursor.fetchall()

            for row in rows:
                self.tree.insert(
                    "",
                    tk.END,
                    iid=str(row["cat_id"]),
                    values=(
                        row["cat_id"],
                        row["cat_name"],
                        format_currency(row["monthly_budget"]),
                        f"{row['txn_count']} txns",
                        format_currency(row["total_spent"]),
                    ),
                )

            self.count_lbl.config(text=f"({len(rows)} categories)")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load categories: {e}")

    def _on_row_select(self, event=None) -> None:
        """Handle selection in table."""
        selected = self.tree.selection()
        if selected:
            self.selected_cat_id = int(selected[0])

    def _load_selected_for_edit(self) -> None:
        """Load selected category into form inputs."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a category from the table to edit.")
            return

        cat_id = int(selected[0])
        category = db_manager.get_category_by_id(cat_id)
        if category:
            self.selected_cat_id = cat_id
            self.name_var.set(category["cat_name"])
            self.budget_var.set(f"{category['monthly_budget']:.2f}")
            self.form_title_var.set(f"Edit Category #{cat_id}")
            self.btn_save.config(text="💾 Update Category", bg="#16A34A")

    def _clear_form(self) -> None:
        """Reset form inputs to initial blank state."""
        self.selected_cat_id = None
        self.name_var.set("")
        self.budget_var.set("0.00")
        self.form_title_var.set("Add New Category")
        self.btn_save.config(text="➕ Save Category", bg=COLOR_PRIMARY)
        self.tree.selection_remove(self.tree.selection())

    def _handle_save(self) -> None:
        """Validate and either insert or update category."""
        # 1. Validate Category Name
        is_name_valid, cat_name, name_err = validate_category_name(self.name_var.get())
        if not is_name_valid:
            messagebox.showerror("Validation Error", name_err)
            self.entry_name.focus_set()
            return

        # 2. Validate Budget
        is_budget_valid, budget_val, budget_err = validate_budget(self.budget_var.get())
        if not is_budget_valid:
            messagebox.showerror("Validation Error", budget_err)
            self.entry_budget.focus_set()
            return

        try:
            if self.selected_cat_id is None:
                # Add new category
                new_id = db_manager.add_category(cat_name, budget_val)
                messagebox.showinfo("Success", f"Category '{cat_name}' successfully added (ID: {new_id}).")
            else:
                # Update existing category
                db_manager.update_category(self.selected_cat_id, cat_name, budget_val)
                messagebox.showinfo("Success", f"Category '{cat_name}' successfully updated.")

            self._clear_form()
            self.load_categories()

            # Trigger notification callback for other tabs
            if self.on_change_callback:
                self.on_change_callback()

        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except Exception as e:
            messagebox.showerror("Database Error", f"Operation failed: {e}")

    def _handle_delete(self) -> None:
        """Validate and delete selected category with confirmation."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a category from the table to delete.")
            return

        cat_id = int(selected[0])
        category = db_manager.get_category_by_id(cat_id)
        if not category:
            messagebox.showerror("Error", "Selected category not found.")
            return

        # Check for linked expenses
        expense_count = db_manager.get_category_expense_count(cat_id)
        if expense_count > 0:
            messagebox.showerror(
                "Cannot Delete Category",
                f"Category '{category['cat_name']}' has {expense_count} associated expense record(s).\n\n"
                "Relational integrity requires you to delete or reassign those expenses before this category can be removed.",
            )
            return

        # Confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Category Deletion",
            f"Are you sure you want to permanently delete the category '{category['cat_name']}'?",
        )
        if not confirm:
            return

        try:
            db_manager.delete_category(cat_id)
            messagebox.showinfo("Deleted", f"Category '{category['cat_name']}' was successfully deleted.")
            self._clear_form()
            self.load_categories()

            if self.on_change_callback:
                self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete category: {e}")
