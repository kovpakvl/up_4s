"""Дизайн-система SecureOffice.

Палитра, типографика, токены отступов и скруглений. Поддерживает
переключение light/dark. Используется всеми виджетами и страницами
нового UI-слоя.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import customtkinter as ctk


@dataclass(frozen=True)
class Palette:
    name: str

    # фоны
    bg: str
    surface: str
    surface_soft: str
    surface_hi: str
    overlay: str

    # текст
    text: str
    text_soft: str
    text_muted: str
    text_inverse: str

    # линии
    line: str
    line_strong: str

    # бренд / CTA
    primary: str
    primary_hover: str
    primary_soft: str
    on_primary: str

    # семантика
    success: str
    success_soft: str
    warning: str
    warning_soft: str
    danger: str
    danger_soft: str
    info: str
    info_soft: str

    # фокус
    focus_ring: str

    # бренд-градиент
    brand_a: str
    brand_b: str


LIGHT = Palette(
    name="light",
    bg="#F4F6FB",
    surface="#FFFFFF",
    surface_soft="#F0F2F8",
    surface_hi="#E7EAF3",
    overlay="#0B0D12",
    text="#0F172A",
    text_soft="#334155",
    text_muted="#64748B",
    text_inverse="#FFFFFF",
    line="#E2E8F0",
    line_strong="#CBD5E1",
    primary="#6366F1",
    primary_hover="#4F46E5",
    primary_soft="#E0E7FF",
    on_primary="#FFFFFF",
    success="#16A34A",
    success_soft="#DCFCE7",
    warning="#D97706",
    warning_soft="#FEF3C7",
    danger="#DC2626",
    danger_soft="#FEE2E2",
    info="#0EA5E9",
    info_soft="#E0F2FE",
    focus_ring="#A5B4FC",
    brand_a="#6366F1",
    brand_b="#8B5CF6",
)


DARK = Palette(
    name="dark",
    bg="#0B0E14",
    surface="#12161F",
    surface_soft="#171C27",
    surface_hi="#1F2533",
    overlay="#000000",
    text="#E6EAF2",
    text_soft="#B4BCCC",
    text_muted="#7E8597",
    text_inverse="#0B0E14",
    line="#262C3A",
    line_strong="#374151",
    primary="#818CF8",
    primary_hover="#6366F1",
    primary_soft="#1E2240",
    on_primary="#0B0E14",
    success="#22C55E",
    success_soft="#0F2A1B",
    warning="#F59E0B",
    warning_soft="#2A1F0A",
    danger="#F87171",
    danger_soft="#2C1117",
    info="#38BDF8",
    info_soft="#0B2434",
    focus_ring="#6366F1",
    brand_a="#818CF8",
    brand_b="#A78BFA",
)


@dataclass(frozen=True)
class Spacing:
    xxs: int = 4
    xs: int = 8
    sm: int = 12
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 48


@dataclass(frozen=True)
class Radius:
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 22
    pill: int = 999


@dataclass(frozen=True)
class Typography:
    family: str = "Segoe UI Variable Display"
    family_fallback: str = "Segoe UI"
    family_mono: str = "JetBrains Mono"
    family_mono_fallback: str = "Consolas"

    display: tuple = ("Segoe UI Variable Display", 28, "bold")
    title: tuple = ("Segoe UI Variable Display", 22, "bold")
    h2: tuple = ("Segoe UI Variable Display", 18, "bold")
    h3: tuple = ("Segoe UI Variable Display", 15, "bold")
    body: tuple = ("Segoe UI", 13, "normal")
    body_strong: tuple = ("Segoe UI", 13, "bold")
    caption: tuple = ("Segoe UI", 11, "normal")
    caption_strong: tuple = ("Segoe UI", 11, "bold")
    mono: tuple = ("Consolas", 13, "normal")
    button: tuple = ("Segoe UI", 13, "bold")
    nav: tuple = ("Segoe UI", 13, "normal")


SPACING = Spacing()
RADIUS = Radius()
TYPO = Typography()


@dataclass
class ThemeState:
    palette: Palette = field(default_factory=lambda: DARK)
    listeners: list[Callable[[Palette], None]] = field(default_factory=list)


_state = ThemeState()


def palette() -> Palette:
    return _state.palette


def is_dark() -> bool:
    return _state.palette.name == "dark"


def set_theme(name: str) -> None:
    new = DARK if name == "dark" else LIGHT
    if new.name == _state.palette.name:
        return
    _state.palette = new
    ctk.set_appearance_mode("Dark" if new.name == "dark" else "Light")
    for listener in list(_state.listeners):
        try:
            listener(new)
        except Exception:
            pass


def toggle_theme() -> None:
    set_theme("light" if is_dark() else "dark")


def on_theme_change(listener: Callable[[Palette], None]) -> Callable[[], None]:
    _state.listeners.append(listener)

    def detach() -> None:
        try:
            _state.listeners.remove(listener)
        except ValueError:
            pass

    return detach


def init(appearance: str = "dark", color_theme: str | None = None) -> None:
    """Инициализирует CustomTkinter и палитру.

    Вызывается ровно один раз при старте приложения.
    """
    ctk.set_appearance_mode("Dark" if appearance == "dark" else "Light")
    if color_theme:
        ctk.set_default_color_theme(color_theme)
    _state.palette = DARK if appearance == "dark" else LIGHT


def color_pair(light_value: str, dark_value: str) -> tuple[str, str]:
    """Возвращает кортеж (light, dark) для fg_color CustomTkinter."""
    return (light_value, dark_value)


def palette_pair(attr: str) -> tuple[str, str]:
    return (getattr(LIGHT, attr), getattr(DARK, attr))
