import tkinter as tk
from tkinter import ttk


COLORS = {
    "bg": "#0d1117",
    "sidebar": "#0f1621",
    "panel": "#151b24",
    "panel_soft": "#1b2430",
    "line": "#2d3748",
    "text": "#e6edf3",
    "muted": "#94a3b8",
    "accent": "#22c55e",
    "accent_hover": "#16a34a",
    "accent_text": "#061019",
    "blue": "#38bdf8",
    "danger": "#f43f5e",
    "warning": "#f59e0b",
}


def apply_theme(window: tk.Misc) -> None:
    window.configure(background=COLORS["bg"])
    style = ttk.Style(window)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(".", background=COLORS["bg"], foreground=COLORS["text"])
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Sidebar.TFrame", background=COLORS["sidebar"])
    style.configure("Panel.TFrame", background=COLORS["panel"])
    style.configure("Soft.TFrame", background=COLORS["panel_soft"])

    style.configure(
        "TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text"],
        font=("Segoe UI", 10),
    )
    style.configure(
        "Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"]
    )
    style.configure(
        "Sidebar.TLabel", background=COLORS["sidebar"], foreground=COLORS["text"]
    )
    style.configure(
        "Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"]
    )
    style.configure(
        "SidebarMuted.TLabel",
        background=COLORS["sidebar"],
        foreground=COLORS["muted"],
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text"],
        font=("Segoe UI", 22, "bold"),
    )
    style.configure(
        "AuthTitle.TLabel",
        background=COLORS["panel"],
        foreground=COLORS["text"],
        font=("Segoe UI", 21, "bold"),
    )
    style.configure(
        "Stat.TLabel",
        background=COLORS["panel"],
        foreground=COLORS["text"],
        font=("Segoe UI", 25, "bold"),
    )
    style.configure(
        "Brand.TLabel",
        background=COLORS["sidebar"],
        foreground=COLORS["text"],
        font=("Segoe UI", 17, "bold"),
    )
    style.configure(
        "BrandMark.TLabel",
        background=COLORS["accent"],
        foreground=COLORS["accent_text"],
        font=("Segoe UI", 14, "bold"),
        padding=(11, 9),
    )

    style.configure(
        "TButton",
        background=COLORS["panel_soft"],
        foreground=COLORS["text"],
        bordercolor=COLORS["line"],
        lightcolor=COLORS["panel_soft"],
        darkcolor=COLORS["panel_soft"],
        padding=(11, 7),
        relief="flat",
    )
    style.map(
        "TButton",
        background=[
            ("pressed", COLORS["line"]),
            ("active", COLORS["line"]),
        ],
        foreground=[("disabled", COLORS["muted"])],
    )
    style.configure(
        "Accent.TButton",
        background=COLORS["accent"],
        foreground=COLORS["accent_text"],
        bordercolor=COLORS["accent"],
        font=("Segoe UI", 10, "bold"),
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
        foreground="#ffb4c1",
        bordercolor=COLORS["danger"],
    )
    style.map("Danger.TButton", background=[("active", "#3a1e29")])
    style.configure(
        "Nav.TButton",
        background=COLORS["sidebar"],
        foreground=COLORS["muted"],
        bordercolor=COLORS["sidebar"],
        anchor="w",
        padding=(14, 11),
    )
    style.map(
        "Nav.TButton",
        background=[("active", COLORS["panel_soft"])],
        foreground=[("active", COLORS["text"])],
    )
    style.configure(
        "NavActive.TButton",
        background=COLORS["panel_soft"],
        foreground=COLORS["accent"],
        bordercolor=COLORS["panel_soft"],
        anchor="w",
        padding=(14, 11),
        font=("Segoe UI", 10, "bold"),
    )

    field_options = {
        "fieldbackground": COLORS["panel_soft"],
        "background": COLORS["panel_soft"],
        "foreground": COLORS["text"],
        "bordercolor": COLORS["line"],
        "insertcolor": COLORS["text"],
        "lightcolor": COLORS["line"],
        "darkcolor": COLORS["line"],
        "padding": 7,
    }
    style.configure("TEntry", **field_options)
    style.configure("TSpinbox", **field_options)
    style.configure(
        "TCombobox",
        **field_options,
        arrowcolor=COLORS["muted"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["panel_soft"])],
        foreground=[("readonly", COLORS["text"])],
        selectbackground=[("readonly", COLORS["panel_soft"])],
        selectforeground=[("readonly", COLORS["text"])],
    )
    window.option_add("*TCombobox*Listbox.background", COLORS["panel_soft"])
    window.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    window.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
    window.option_add("*TCombobox*Listbox.selectForeground", COLORS["accent_text"])

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
        font=("Segoe UI", 9, "bold"),
    )

    style.configure(
        "Treeview",
        background=COLORS["panel"],
        fieldbackground=COLORS["panel"],
        foreground=COLORS["text"],
        bordercolor=COLORS["line"],
        rowheight=31,
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
        font=("Segoe UI", 9, "bold"),
        padding=(7, 8),
    )
    style.map("Treeview.Heading", background=[("active", COLORS["line"])])

    style.configure(
        "TCheckbutton", background=COLORS["bg"], foreground=COLORS["text"]
    )
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
        padx=8,
        pady=7,
    )
