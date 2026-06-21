"""Заглушка-страница на время разработки."""
from __future__ import annotations

from ..widgets.empty_state import EmptyState
from .base import Page


class PlaceholderPage(Page):
    def __init__(self, master, app, *, title: str, description: str = "", icon: str = "sparkles"):
        super().__init__(master, app)
        self.title = title
        self.subtitle = description
        EmptyState(
            self,
            icon=icon,
            title=title,
            description=description or "Этот раздел появится в ближайшем обновлении.",
        ).pack(fill="both", expand=True, padx=24, pady=24)
