# Personal Daily Expense Tracker & Monthly Budget Analyzer

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![GUI](https://img.shields.io/badge/GUI-Tkinter%20%26%20ttk-orange)
![Database](https://img.shields.io/badge/Database-SQLite3-lightgrey?logo=sqlite)
![Status](https://img.shields.io/badge/Status-Completed-success)

> **MCA III Semester Python Programming Lab Project (Academic Year 2026–2027)**  
> **Student Name:** Kiran R  
> **Registration Number:** 25PG00171  
> **University:** Chanakya University  
> **Department:** Department of Computer Applications  
> **Domain:** Personal Finance & Wealth Management  

---

## 📌 Project Overview

The **Personal Daily Expense Tracker & Monthly Budget Analyzer** is a robust, standalone desktop application developed in Python. Engineered to help individuals take control of their personal finances, the software allows users to log day-to-day expenditures, classify transactions into customizable categories, establish monthly spending caps, monitor budget variance in real time, and gain deep visual insights into their spending behavior through interactive charts.

The application combines a high-contrast, modern slate-navy dashboard UI built with **Tkinter** and **ttk**, a relational database engine driven by Python's native **SQLite3** library with foreign key constraints, and embedded financial data visualizations powered by **Matplotlib**.

---

## ✨ Key Features

### 1. 📊 Executive Financial Dashboard (Module A)
- Real-time monthly spending vs. allocated budget KPI cards.
- Remaining budget balance with dynamic overspending warnings.
- Transaction counter and automatic detection of peak spending category.
- Recent transactions list with live status indicators.
- Embedded Matplotlib Donut Chart visualizing current month category distribution.
- One-click shortcuts to add expenses or adjust budgets.

### 2. 🏷️ Category & Budget Management (Module B)
- Full CRUD operations (Create, Read, Update, Delete) for spending classifications.
- Set and revise monthly budget caps per category.
- Seeded with 8 sensible defaults on first launch: *Food, Travel, Shopping, Education, Healthcare, Bills, Entertainment, and Others*.
- **Relational Integrity Protection:** Automatically blocks deletion of categories that have linked expenses, preventing orphaned records.

### 3. ➕ Daily Expense Management (Module C)
- Clean, responsive transaction entry form.
- Amount validation (numeric, positive, 2 decimal places).
- Category selection via dynamic dropdown.
- Payment mode tagging (*Cash, UPI, Card*).
- Calendar date selection via `tkcalendar.DateEntry`.
- Interactive table: select any row to populate the form for updating or deletion.
- User confirmation dialogues for destructive operations.

### 4. 📜 Expense History & Audit Trail (Module D)
- Multi-parameter filtering:
  - Real-time substring search by description.
  - Filter by Category.
  - Filter by Payment Mode (*Cash / UPI / Card*).
  - Filter by specific Month and Year.
  - Custom date range filtering with date pickers.
- Multi-mode sorting (*Date newest/oldest, Amount high-to-low/low-to-high*).
- Dynamic summary banner showing total records found and filtered sum total.
- **CSV Export:** One-click export of filtered transaction records to a `.csv` spreadsheet for external auditing.
- Direct edit bridge: select any history record to edit in Expense Manager.

### 5. 🎯 Monthly Budget Analyzer (Module E)
- Month-by-month financial variance analysis.
- Automatic calculations:
  - $\text{Total Budget} = \sum \text{Category Budgets}$
  - $\text{Category Spending} = \sum \text{Expenses for category in selected month}$
  - $\text{Remaining Budget} = \text{Category Budget} - \text{Category Spending}$
  - $\text{Utilization \%} = (\text{Spending} / \text{Budget}) \times 100$
- Visual health badges:
  - 🟢 **Within Budget** ($< 75\%$)
  - 🟡 **Warning** ($75\% - 100\%$)
  - 🔴 **Over Budget** ($> 100\%$)
- Zero-budget category protection (no `ZeroDivisionError`).
- Inline budget adjustment modal via double-clicking.

### 6. 📈 Visual Reports & Analytics (Module F)
- Embedded interactive Matplotlib charts:
  - **Category Share:** Donut chart of expenditure distribution.
  - **Budget vs. Actual:** Grouped bar chart comparing spending caps against actual outflows.
  - **Monthly Trajectory:** Multi-month historical spending trend line chart.
  - **Payment Modes:** Distribution breakdown between UPI, Card, and Cash.
- Statistical metrics: Highest spending category, lowest category, most preferred payment channel, and daily average spending.
- Tabular breakdown with percentages of total budget and total outflow.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.10+** | Core programming language |
| **Tkinter** | Native desktop graphical user interface framework |
| **ttk (Themed Tkinter)** | Modern themed widgets (*Treeview, Combobox, Notebook, Progressbar*) |
| **SQLite3** | Embedded, serverless relational database engine |
| **tkcalendar** | Interactive calendar popup date picker widget (`DateEntry`) |
| **Matplotlib** | Financial data visualization and chart generation (`FigureCanvasTkAgg`) |
| **Pillow (PIL)** | Image manipulation and high-resolution screenshot capture |
| **datetime & calendar** | Date arithmetic, month conversions, and timestamps |
| **re** | Strict regular expression validation for inputs |

---

## 📂 Project Structure

```text
Personal Daily Expense Tracker/
│
├── main.py                     # Application entry point and UI controller
├── requirements.txt            # Python package dependencies
├── README.md                   # Project documentation and user guide
├── PROJECT_REPORT.md           # University academic lab report
├── capture_screenshots.py      # Automated screenshot generator script
│
├── database/                   # Database Layer
│   ├── __init__.py
│   ├── db_connection.py        # SQLite DatabaseManager, queries & schema
│   ├── seed_data.py            # Demonstration data seeder script
│   └── expense_tracker.db      # Persistent SQLite database file
│
├── modules/                    # Application Modules (Views & Logic)
│   ├── __init__.py
│   ├── dashboard.py            # Module A: Dashboard overview & charts
│   ├── category_manager.py     # Module B: Category CRUD & budgets
│   ├── expense_manager.py      # Module C: Expense entry, update, delete
│   ├── expense_history.py      # Module D: Search, filter, sort & CSV export
│   ├── budget_analyzer.py      # Module E: Variance, status & caps
│   └── reports.py              # Module F: Matplotlib analytics & metrics
│
├── utils/                      # Helper Utilities & Validation
│   ├── __init__.py
│   ├── validators.py           # Regex, numeric, and business rule validators
│   └── helpers.py              # Currency formatter, colors, typography, dates
│
├── tests/                      # Automated Test Suite
│   ├── __init__.py
│   └── test_application.py     # 22 unit & integration tests (unittest)
│
└── screenshots/                # Captured UI execution screenshots
    ├── dashboard.png
    ├── add_expense.png
    ├── expense_history.png
    ├── category_management.png
    ├── budget_analyzer.png
    └── reports_analytics.png
```

---

## 💾 Database Schema

The database `expense_tracker.db` enforces relational integrity with `PRAGMA foreign_keys = ON;`.

### Table 1: `categories`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `cat_id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique category identifier |
| `cat_name` | `TEXT` | `NOT NULL UNIQUE` | Category title (e.g., Food, Travel) |
| `monthly_budget` | `REAL` | `NOT NULL DEFAULT 0` | Monthly spending limit in INR |

### Table 2: `expenses`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `exp_id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique transaction identifier |
| `cat_id` | `INTEGER` | `NOT NULL, FOREIGN KEY` | References `categories(cat_id)` |
| `amount` | `REAL` | `NOT NULL` | Expense value in INR (> 0) |
| `exp_date` | `TEXT` | `NOT NULL` | Transaction date (`YYYY-MM-DD`) |
| `description` | `TEXT` | `NOT NULL` | Transaction purpose |
| `payment_mode` | `TEXT` | `NOT NULL` | Payment channel (`Cash`, `UPI`, `Card`) |

---

## 🚀 Installation & Setup

### 1. Prerequisites
Ensure **Python 3.10 or higher** is installed on your system. You can verify your Python version with:
```bash
python --version
```

### 2. Clone / Navigate to Project Directory
```bash
cd "Personal Daily Expense Tracker"
```

### 3. Install Required Dependencies
Install the required third-party libraries using `pip`:
```bash
pip install -r requirements.txt
```

---

## 💻 Running the Application

To launch the desktop application, run:
```bash
python main.py
```

### Running the Automated Test Suite
To execute all 22 unit and integration tests:
```bash
python -m unittest discover tests -v
```

### Capturing Screenshots
To generate high-resolution screenshots of all modules into the `screenshots/` directory:
```bash
python capture_screenshots.py
```

---

## 🖼️ Application Screenshots

| Screen | Description | File |
|---|---|---|
| **Dashboard** | Financial KPIs, recent transactions & category donut chart | `screenshots/dashboard.png` |
| **Add Expense** | Expense entry form with DateEntry and transaction table | `screenshots/add_expense.png` |
| **Expense History** | Search, multi-criteria filters, sorting & CSV export | `screenshots/expense_history.png` |
| **Categories** | Category management and monthly budget caps | `screenshots/category_management.png` |
| **Budget Analyzer** | Variance calculation, progress status and alert badges | `screenshots/budget_analyzer.png` |
| **Reports & Analytics** | Matplotlib category share, budget vs actual, and trends | `screenshots/reports_analytics.png` |

---

## ❓ Troubleshooting & FAQs

1. **Missing `tkinter` on Linux/Ubuntu:**
   Tkinter is built into Windows Python installations. On Linux, run:
   ```bash
   sudo apt-get install python3-tk
   ```

2. **DPI Scaling on High-Resolution Displays:**
   The application includes automatic Windows DPI awareness configuration in `main.py` using `ctypes.windll.shcore.SetProcessDpiAwareness(1)` for crisp font rendering.

3. **Resetting Database to Default Demo State:**
   To reset the database, simply delete `database/expense_tracker.db` and launch `python main.py` or execute `python database/seed_data.py`.

---

## 🎓 Academic Submission Details

- **Student:** Kiran R
- **Registration Number:** 25PG00171
- **Course:** Master of Computer Applications (MCA) III Semester
- **Subject:** Python Programming Lab
- **Institution:** Department of Computer Applications, Chanakya University
- **Academic Year:** 2026–2027
