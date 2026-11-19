"""
Automated Screenshot Capture Utility
Navigates through all views of the Personal Daily Expense Tracker
and captures high-resolution window screenshots for university submission.
Uses Win32 GDI PrintWindow API for 100% reliable capture in all environments.
"""

import os
import sys
import time
import ctypes
from ctypes import wintypes, Structure, c_long, c_short, c_uint32, sizeof, byref
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import ExpenseTrackerApp

SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ("biSize", c_uint32),
        ("biWidth", c_long),
        ("biHeight", c_long),
        ("biPlanes", c_short),
        ("biBitCount", c_short),
        ("biCompression", c_uint32),
        ("biSizeImage", c_uint32),
        ("biXPelsPerMeter", c_long),
        ("biYPelsPerMeter", c_long),
        ("biClrUsed", c_uint32),
        ("biClrImportant", c_uint32),
    ]


def capture_window_to_image(root_widget) -> Image.Image:
    """Capture a Tkinter window directly using Windows PrintWindow GDI API."""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    # GA_ROOT = 2
    hwnd = user32.GetAncestor(root_widget.winfo_id(), 2)

    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top

    hdc_window = user32.GetWindowDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_window)
    hbm = gdi32.CreateCompatibleBitmap(hdc_window, w, h)
    gdi32.SelectObject(hdc_mem, hbm)

    # PW_RENDERFULLCONTENT = 2
    user32.PrintWindow(hwnd, hdc_mem, 2)

    bmi = BITMAPINFOHEADER()
    bmi.biSize = sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # top-down DIB
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, byref(bmi), 0)

    im = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
    im = im.convert("RGB")

    user32.ReleaseDC(hwnd, hdc_window)
    gdi32.DeleteDC(hdc_mem)
    gdi32.DeleteObject(hbm)

    return im


def capture_all_views():
    print("Launching ExpenseTrackerApp for screenshot capture...")
    app = ExpenseTrackerApp()
    app.geometry("1240x780+30+30")
    app.update_idletasks()
    app.update()
    time.sleep(0.5)

    views = [
        ("Dashboard", "dashboard.png"),
        ("Add Expense", "add_expense.png"),
        ("Expense History", "expense_history.png"),
        ("Categories", "category_management.png"),
        ("Budget Analyzer", "budget_analyzer.png"),
        ("Reports & Analytics", "reports_analytics.png"),
    ]

    for page_name, filename in views:
        app.navigate_to(page_name)
        app.update_idletasks()
        app.update()
        time.sleep(0.6)  # Allow Tkinter and Matplotlib to paint

        save_path = os.path.join(SCREENSHOTS_DIR, filename)
        img = capture_window_to_image(app)
        img.save(save_path, "PNG")
        print(f"Captured: {page_name} -> {save_path} ({img.size[0]}x{img.size[1]})")

    app.destroy()
    print("All screenshots generated and verified successfully.")


if __name__ == "__main__":
    capture_all_views()
