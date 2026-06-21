import tkinter as tk
from tkinter import messagebox

from database import ensure_database


def main() -> None:
    try:
        ensure_database()
        from ui_login import LoginWindow

        app = LoginWindow()
        app.mainloop()
    except RuntimeError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка запуска", str(exc))
        root.destroy()


if __name__ == "__main__":
    main()
