"""Полоска стойкости пароля 0-4."""
from __future__ import annotations

import customtkinter as ctk

from .. import theme


_LABELS = ("Очень слабый", "Слабый", "Средний", "Надёжный", "Сильный")
_TONES = ("danger", "danger", "warning", "success", "success")


def score_password(password: str) -> int:
    if not password:
        return 0
    score = 0
    length = len(password)
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1
    classes = sum(
        [
            any(ch.islower() for ch in password),
            any(ch.isupper() for ch in password),
            any(ch.isdigit() for ch in password),
            any(not ch.isalnum() for ch in password),
        ]
    )
    score += max(0, classes - 1)
    return max(0, min(4, score))


class StrengthMeter(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self._segments: list[ctk.CTkFrame] = []
        self._track = ctk.CTkFrame(self, fg_color="transparent")
        self._track.pack(fill="x")
        for i in range(5):
            seg = ctk.CTkFrame(
                self._track,
                height=6,
                corner_radius=3,
                fg_color=theme.palette_pair("surface_hi"),
            )
            seg.pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 4, 0))
            self._segments.append(seg)
        self._label = ctk.CTkLabel(
            self,
            text="",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="transparent",
            anchor="w",
        )
        self._label.pack(fill="x", pady=(6, 0))

    def update(self, password: str) -> None:
        score = score_password(password)
        tone = _TONES[score]
        tone_color = theme.palette_pair(tone)
        empty = theme.palette_pair("surface_hi")
        for i, seg in enumerate(self._segments):
            seg.configure(fg_color=tone_color if i <= score and password else empty)
        if password:
            self._label.configure(text=_LABELS[score], text_color=tone_color)
        else:
            self._label.configure(
                text="Пароль не задан", text_color=theme.palette_pair("text_muted")
            )
