"""Аватар-кружок с инициалами и градиентом."""
from __future__ import annotations

import hashlib
from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
from customtkinter import CTkImage


_PALETTES = [
    ("#6366F1", "#8B5CF6"),
    ("#22D3EE", "#0EA5E9"),
    ("#F472B6", "#EC4899"),
    ("#34D399", "#10B981"),
    ("#FBBF24", "#F59E0B"),
    ("#A78BFA", "#7C3AED"),
    ("#60A5FA", "#3B82F6"),
    ("#FB7185", "#E11D48"),
]


def _palette_for(name: str) -> tuple[str, str]:
    digest = hashlib.md5(name.encode("utf-8")).digest()
    return _PALETTES[digest[0] % len(_PALETTES)]


def _initials(name: str) -> str:
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][:1] + parts[1][:1]).upper()


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


@lru_cache(maxsize=256)
def _avatar_image(name: str, size: int) -> CTkImage:
    initials = _initials(name)
    a, b = _palette_for(name)
    scale = 3
    big = size * scale
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    ra = _hex_to_rgb(a)
    rb = _hex_to_rgb(b)
    for y in range(big):
        t = y / big
        r = int(ra[0] + (rb[0] - ra[0]) * t)
        g = int(ra[1] + (rb[1] - ra[1]) * t)
        bl = int(ra[2] + (rb[2] - ra[2]) * t)
        draw.line([(0, y), (big, y)], fill=(r, g, bl, 255))
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big, big), fill=255)
    rounded = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    rounded.paste(img, mask=mask)

    try:
        font = ImageFont.truetype("seguibd.ttf", int(big * 0.42))
    except OSError:
        font = ImageFont.load_default()
    bbox = font.getbbox(initials)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw_top = ImageDraw.Draw(rounded)
    draw_top.text(
        ((big - text_w) / 2 - bbox[0], (big - text_h) / 2 - bbox[1]),
        initials,
        font=font,
        fill=(255, 255, 255, 255),
    )
    rounded = rounded.resize((size, size), Image.LANCZOS)
    return CTkImage(light_image=rounded, dark_image=rounded, size=(size, size))


class Avatar(ctk.CTkLabel):
    def __init__(self, master, name: str, *, size: int = 36, **kwargs):
        kwargs.setdefault("text", "")
        kwargs.setdefault("fg_color", "transparent")
        kwargs["image"] = _avatar_image(name or "?", size)
        super().__init__(master, **kwargs)
