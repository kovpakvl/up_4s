"""Тема для устаревшего клиента на чистом ttk.

Палитра выровнена с новым UI-слоем (ui/theme.py), чтобы оба окна
выглядели как один продукт. Не переписывает архитектуру старого
клиента — только пересобирает стили ttk.
"""
import tkinter as tk
from tkinter import ttk


COLORS = {
    # фон / поверхности
    "bg": "#0B0E14",
    "sidebar": "#12161F",
    "panel": "#12161F",
    "panel_soft": "#171C27",
    "panel_hi": "#1F2533",
    "line": "#262C3A",
    "line_strong": "#374151",

    # текст
    "text": "#E6EAF2",
    "text_soft": "#B4BCCC",
    "muted": "#7E8597",
    "text_inverse": "#0B0E14",

    # бренд / CTA
    "accent": "#818CF8",
    "accent_hover": "#6366F1",
    "accent_soft": "#1E2240",
    "accent_text": "#0B0E14",

    # семантика
    "blue": "#38BDF8",
    "danger": "#F87171",
    "warning": "#F59E0B",
    "success": "#22C55E",
}


def apply_theme(window: tk.Misc) -> None:
    window.configure(background=COLORS["bg"])
    try:
        window.tk.call("tk", "scaling", 1.15)
    except tk.TclError:
        pass

    style = ttk.Style(window)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    base_font = ("Segoe UI Variable Display", 11)
    title_font = ("Segoe UI Variable Display", 22, "bold")
    h2_font = ("Segoe UI Variable Display", 16, "bold")
    button_font = ("Segoe UI", 11, "bold")

    # базовые контейнеры
    style.configure(".", background=COLORS["bg"], foreground=COLORS["text"], font=base_font)
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Sidebar.TFrame", background=COLORS["sidebar"])
    style.configure("Panel.TFrame", background=COLORS["panel"])
    style.configure("Soft.TFrame", background=COLORS["panel_soft"])

    # текстовые стили
    style.configure(
        "TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text"],
        font=base_font,
    )
    style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"])
    style.configure("Sidebar.TLabel", background=COLORS["sidebar"], foreground=COLORS["text"])
    style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"])
    style.configure(
        "SidebarMuted.TLabel",
        background=COLORS["sidebar"],
        foreground=COLORS["muted"],
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text"],
        font=title_font,
    )
    style.configure(
        "AuthTitle.TLabel",
        background=COLORS["panel"],
        foreground=COLORS["text"],
        font=("Segoe UI Variable Display", 20, "bold"),
    )
    style.configure(
        "Stat.TLabel",
        background=COLORS["panel"],
        foreground=COLORS["text"],
        font=("Segoe UI Variable Display", 26, "bold"),
    )
    style.configure(
        "Brand.TLabel",
        background=COLORS["sidebar"],
        foreground=COLORS["text"],
        font=h2_font,
    )
    style.configure(
        "BrandMark.TLabel",
        background=COLORS["accent"],
        foreground=COLORS["accent_text"],
        font=("Segoe UI", 13, "bold"),
        padding=(12, 9),
    )
    style.configure(
        "AuthMuted.TLabel",
        background=COLORS["panel"],
        foreground=COLORS["muted"],
        font=("Segoe UI", 11),
    )

    # ноутбук (вкладки)
    style.configure(
        "Auth.TNotebook",
        background=COLORS["panel"],
        borderwidth=0,
        tabmargins=(0, 12, 0, 0),
    )
    style.configure(
        "Auth.TNotebook.Tab",
        background=COLORS["panel_soft"],
        foreground=COLORS["muted"],
        bordercolor=COLORS["line"],
        lightcolor=COLORS["panel_soft"],
        darkcolor=COLORS["panel_soft"],
        padding=(18, 9),
        font=("Segoe UI", 11, "bold"),
    )
    style.map(
        "Auth.TNotebook.Tab",
        background=[
            ("selected", COLORS["accent"]),
            ("active", COLORS["panel_hi"]),
        ],
        foreground=[
            ("selected", COLORS["accent_text"]),
            ("active", COLORS["text"]),
        ],
    )

    # кнопки
    style.configure(
        "TButton",
        background=COLORS["panel_soft"],
        foreground=COLORS["text"],
        bordercolor=COLORS["line"],
        lightcolor=COLORS["panel_soft"],
        darkcolor=COLORS["panel_soft"],
        padding=(14, 9),
        relief="flat",
        font=button_font,
    )
    style.map(
        "TButton",
        background=[
            ("pressed", COLORS["panel_hi"]),
            ("active", COLORS["panel_hi"]),
        ],
        foreground=[("disabled", COLORS["muted"])],
    )
    style.configure(
        "Accent.TButton",
        background=COLORS["accent"],
        foreground=COLORS["accent_text"],
        bordercolor=COLORS["accent"],
        font=button_font,
        padding=(16, 9),
    )
    style.map(
        "Accent.TButton",
        background=[
            ("pressed", COLORS["accent_hover"]),
            ("active", COLORS["accent_hover"]),
        ],
        foreground=[("active", COLORS["accent_text"])],
    )
    style.configure(
        "Danger.TButton",
        background=COLORS["panel"],
        foreground="#FCA5A5",
        bordercolor=COLORS["danger"],
        padding=(14, 9),
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#2C1117")],
    )

    # боковое меню
    style.configure(
        "Nav.TButton",
        background=COLORS["sidebar"],
        foreground=COLORS["muted"],
        bordercolor=COLORS["sidebar"],
        anchor="w",
        padding=(16, 12),
        font=("Segoe UI", 11),
    )
    style.map(
        "Nav.TButton",
        background=[("active", COLORS["panel_soft"])],
        foreground=[("active", COLORS["text"])],
    )
    style.configure(
        "NavActive.TButton",
        background=COLORS["accent_soft"],
        foreground=COLORS["accent"],
        bordercolor=COLORS["accent_soft"],
        anchor="w",
        padding=(16, 12),
        font=("Segoe UI", 11, "bold"),
    )

    # поля ввода
    field_options = {
        "fieldbackground": COLORS["panel_soft"],
        "background": COLORS["panel_soft"],
        "foreground": COLORS["text"],
        "bordercolor": COLORS["line"],
        "insertcolor": COLORS["text"],
        "lightcolor": COLORS["line"],
        "darkcolor": COLORS["line"],
        "padding": 8,
    }
    style.configure("TEntry", **field_options)
    style.configure("TSpinbox", **field_options)
    style.configure("TCombobox", arrowcolor=COLORS["muted"], **field_options)
    style.map(
        "TEntry",
        bordercolor=[("focus", COLORS["accent"])],
        lightcolor=[("focus", COLORS["accent"])],
        darkcolor=[("focus", COLORS["accent"])],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["panel_soft"])],
        foreground=[("readonly", COLORS["text"])],
        selectbackground=[("readonly", COLORS["panel_soft"])],
        selectforeground=[("readonly", COLORS["text"])],
        bordercolor=[("focus", COLORS["accent"])],
    )
    window.option_add("*TCombobox*Listbox.background", COLORS["panel_soft"])
    window.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    window.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
    window.option_add("*TCombobox*Listbox.selectForeground", COLORS["accent_text"])

    # фреймы-группы
    style.configure(
        "TLabelframe",
        background=COLORS["panel"],
        bordercolor=COLORS["line"],
        lightcolor=COLORS["line"],
        darkcolor=COLORS["line"],
        relief="solid",
    )
    style.configure(
        "TLabelframe.Label",
        background=COLORS["panel"],
        foreground=COLORS["muted"],
        font=("Segoe UI", 10, "bold"),
    )

    # таблицы
    style.configure(
        "Treeview",
        background=COLORS["panel"],
        fieldbackground=COLORS["panel"],
        foreground=COLORS["text"],
        bordercolor=COLORS["line"],
        rowheight=34,
        font=("Segoe UI", 10),
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["accent"])],
        foreground=[("selected", COLORS["accent_text"])],
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["panel_soft"],
        foreground=COLORS["muted"],
        bordercolor=COLORS["line"],
        font=("Segoe UI", 10, "bold"),
        padding=(8, 9),
    )
    style.map("Treeview.Heading", background=[("active", COLORS["panel_hi"])])

    # чекбоксы
    style.configure("TCheckbutton", background=COLORS["bg"], foreground=COLORS["text"])
    style.map(
        "TCheckbutton",
        background=[("active", COLORS["bg"])],
        indicatorcolor=[
            ("selected", COLORS["accent"]),
            ("!selected", COLORS["panel_soft"]),
        ],
    )
    style.configure(
        "Panel.TCheckbutton", background=COLORS["panel"], foreground=COLORS["text"]
    )
    style.map(
        "Panel.TCheckbutton",
        background=[("active", COLORS["panel"])],
        indicatorcolor=[
            ("selected", COLORS["accent"]),
            ("!selected", COLORS["panel_soft"]),
        ],
    )

    # скроллбары и разделители
    style.configure(
        "Vertical.TScrollbar",
        background=COLORS["panel_soft"],
        troughcolor=COLORS["bg"],
        bordercolor=COLORS["bg"],
        arrowcolor=COLORS["muted"],
    )
    style.configure("TSeparator", background=COLORS["line"])


def style_text_widget(widget: tk.Text) -> None:
    widget.configure(
        background=COLORS["panel_soft"],
        foreground=COLORS["text"],
        insertbackground=COLORS["text"],
        selectbackground=COLORS["accent"],
        selectforeground=COLORS["accent_text"],
        relief="flat",
        highlightthickness=1,
        highlightbackground=COLORS["line"],
        highlightcolor=COLORS["accent"],
        padx=10,
        pady=8,
        font=("Segoe UI", 10),
    )
