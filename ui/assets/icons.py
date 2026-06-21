"""Векторные иконки в стиле Lucide, отрисованные через Pillow.

Иконки рисуются один раз в памяти и кешируются. Это избавляет от
необходимости поставлять PNG-файлы вместе с приложением и автоматически
адаптирует цвет к текущей теме.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Callable

from PIL import Image, ImageDraw
from customtkinter import CTkImage

from .. import theme


Painter = Callable[[ImageDraw.ImageDraw, int, str], None]


def _stroke(width: int, base: int = 24) -> int:
    return max(1, round(width * 2 / base))


def _shield(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    pad = size * 0.12
    cx = size / 2
    top = pad
    bottom = size - pad
    points = [
        (cx, top),
        (size - pad, top + size * 0.1),
        (size - pad, size * 0.55),
        (cx, bottom),
        (pad, size * 0.55),
        (pad, top + size * 0.1),
    ]
    draw.line(points + [points[0]], fill=color, width=s, joint="curve")


def _users(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    head_r = size * 0.115
    cx1, cx2 = size * 0.38, size * 0.64
    cy = size * 0.34
    draw.ellipse(
        [cx1 - head_r, cy - head_r, cx1 + head_r, cy + head_r],
        outline=color,
        width=s,
    )
    draw.ellipse(
        [cx2 - head_r * 0.9, cy - head_r * 0.9, cx2 + head_r * 0.9, cy + head_r * 0.9],
        outline=color,
        width=s,
    )
    draw.arc(
        [size * 0.2, size * 0.5, size * 0.58, size * 0.86],
        start=200,
        end=340,
        fill=color,
        width=s,
    )
    draw.arc(
        [size * 0.44, size * 0.54, size * 0.82, size * 0.86],
        start=210,
        end=330,
        fill=color,
        width=s,
    )


def _building(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    pad = size * 0.15
    draw.rectangle([pad, pad, size - pad, size - pad], outline=color, width=s)
    step = (size - pad * 2) / 4
    for i in range(1, 4):
        y = pad + step * i
        draw.line([pad, y, size - pad, y], fill=color, width=s)
    for i in range(1, 4):
        x = pad + step * i
        draw.line([x, pad, x, size - pad], fill=color, width=s)


def _key(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    r = size * 0.18
    cx, cy = size * 0.32, size * 0.32
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=s)
    draw.line([cx + r * 0.5, cy + r * 0.5, size - size * 0.12, size - size * 0.12], fill=color, width=s)
    draw.line([size * 0.65, size * 0.65, size * 0.78, size * 0.52], fill=color, width=s)
    draw.line([size * 0.55, size * 0.75, size * 0.7, size * 0.6], fill=color, width=s)


def _sparkles(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)

    def star(cx: float, cy: float, r: float) -> None:
        draw.line([cx, cy - r, cx, cy + r], fill=color, width=s)
        draw.line([cx - r, cy, cx + r, cy], fill=color, width=s)
        draw.line([cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6], fill=color, width=s)
        draw.line([cx - r * 0.6, cy + r * 0.6, cx + r * 0.6, cy - r * 0.6], fill=color, width=s)

    star(size * 0.42, size * 0.42, size * 0.22)
    star(size * 0.74, size * 0.7, size * 0.12)
    star(size * 0.72, size * 0.28, size * 0.1)


def _mail(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    pad = size * 0.16
    box = [pad, pad + size * 0.06, size - pad, size - pad - size * 0.06]
    draw.rounded_rectangle(box, radius=int(size * 0.07), outline=color, width=s)
    draw.line(
        [box[0], box[1], (box[0] + box[2]) / 2, box[3] - (box[3] - box[1]) * 0.35, box[2], box[1]],
        fill=color,
        width=s,
        joint="curve",
    )


def _gear(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    cx, cy = size / 2, size / 2
    r_out = size * 0.36
    r_in = size * 0.18
    teeth = 8
    import math
    pts = []
    for i in range(teeth * 2):
        angle = math.pi * 2 * i / (teeth * 2)
        r = r_out if i % 2 == 0 else r_out * 0.78
        pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    draw.line(pts + [pts[0]], fill=color, width=s, joint="curve")
    draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], outline=color, width=s)


def _activity(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    pad = size * 0.15
    pts = [
        (pad, size * 0.5),
        (size * 0.3, size * 0.5),
        (size * 0.4, size * 0.25),
        (size * 0.55, size * 0.78),
        (size * 0.65, size * 0.5),
        (size - pad, size * 0.5),
    ]
    draw.line(pts, fill=color, width=s, joint="curve")


def _grid(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    pad = size * 0.16
    cell = (size - pad * 2) / 2
    r = int(size * 0.08)
    for row in range(2):
        for col in range(2):
            x0 = pad + col * cell + (col * size * 0.03)
            y0 = pad + row * cell + (row * size * 0.03)
            draw.rounded_rectangle(
                [x0, y0, x0 + cell - size * 0.03, y0 + cell - size * 0.03],
                radius=r,
                outline=color,
                width=s,
            )


def _plus(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    pad = size * 0.22
    cx = size / 2
    draw.line([pad, cx, size - pad, cx], fill=color, width=s)
    draw.line([cx, pad, cx, size - pad], fill=color, width=s)


def _check(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    draw.line(
        [size * 0.2, size * 0.55, size * 0.42, size * 0.75, size * 0.8, size * 0.3],
        fill=color,
        width=s,
        joint="curve",
    )


def _close(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    pad = size * 0.25
    draw.line([pad, pad, size - pad, size - pad], fill=color, width=s)
    draw.line([size - pad, pad, pad, size - pad], fill=color, width=s)


def _copy(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    r = int(size * 0.08)
    draw.rounded_rectangle(
        [size * 0.32, size * 0.22, size * 0.78, size * 0.7], radius=r, outline=color, width=s
    )
    draw.rounded_rectangle(
        [size * 0.22, size * 0.32, size * 0.68, size * 0.8], radius=r, outline=color, width=s
    )


def _eye(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    draw.arc(
        [size * 0.12, size * 0.25, size * 0.88, size * 0.75], start=0, end=180, fill=color, width=s
    )
    draw.arc(
        [size * 0.12, size * 0.25, size * 0.88, size * 0.75], start=180, end=360, fill=color, width=s
    )
    r = size * 0.12
    cx, cy = size / 2, size / 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=s)


def _search(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    r = size * 0.26
    cx, cy = size * 0.42, size * 0.42
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=s)
    draw.line([cx + r * 0.7, cy + r * 0.7, size * 0.82, size * 0.82], fill=color, width=s)


def _bell(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    cx = size / 2
    draw.arc(
        [size * 0.2, size * 0.18, size * 0.8, size * 0.78], start=180, end=360, fill=color, width=s
    )
    draw.line([size * 0.2, size * 0.6, size * 0.8, size * 0.6], fill=color, width=s)
    draw.line([size * 0.3, size * 0.6, size * 0.3, size * 0.7], fill=color, width=s)
    draw.line([size * 0.7, size * 0.6, size * 0.7, size * 0.7], fill=color, width=s)
    draw.line([size * 0.3, size * 0.7, size * 0.7, size * 0.7], fill=color, width=s)
    draw.ellipse([cx - size * 0.05, size * 0.74, cx + size * 0.05, size * 0.84], outline=color, width=s)


def _power(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    cx = size / 2
    draw.line([cx, size * 0.18, cx, size * 0.5], fill=color, width=s)
    draw.arc(
        [size * 0.18, size * 0.25, size * 0.82, size * 0.9], start=30, end=150, fill=color, width=s
    )


def _refresh(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    draw.arc(
        [size * 0.18, size * 0.18, size * 0.82, size * 0.82], start=300, end=200, fill=color, width=s
    )
    draw.polygon(
        [
            (size * 0.78, size * 0.2),
            (size * 0.78, size * 0.42),
            (size * 0.6, size * 0.32),
        ],
        fill=color,
    )


def _arrow_right(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    draw.line([size * 0.2, size * 0.5, size * 0.78, size * 0.5], fill=color, width=s)
    draw.line([size * 0.55, size * 0.3, size * 0.78, size * 0.5], fill=color, width=s)
    draw.line([size * 0.55, size * 0.7, size * 0.78, size * 0.5], fill=color, width=s)


def _chevron_left(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    draw.line([size * 0.62, size * 0.25, size * 0.38, size * 0.5], fill=color, width=s)
    draw.line([size * 0.38, size * 0.5, size * 0.62, size * 0.75], fill=color, width=s)


def _alert(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    cx = size / 2
    pad = size * 0.12
    draw.polygon(
        [(cx, pad), (size - pad, size - pad), (pad, size - pad)],
        outline=color,
        width=s,
    )
    draw.line([cx, size * 0.4, cx, size * 0.62], fill=color, width=s)
    draw.ellipse([cx - size * 0.04, size * 0.7, cx + size * 0.04, size * 0.78], fill=color)


def _trash(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    pad = size * 0.2
    draw.line([pad - size * 0.05, size * 0.28, size - pad + size * 0.05, size * 0.28], fill=color, width=s)
    draw.rectangle([pad, size * 0.28, size - pad, size - pad], outline=color, width=s)
    draw.line([size * 0.42, size * 0.4, size * 0.42, size * 0.7], fill=color, width=s)
    draw.line([size * 0.58, size * 0.4, size * 0.58, size * 0.7], fill=color, width=s)
    draw.line([size * 0.38, size * 0.22, size * 0.62, size * 0.22], fill=color, width=s)


def _sun(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    cx = size / 2
    r = size * 0.18
    draw.ellipse([cx - r, cx - r, cx + r, cx + r], outline=color, width=s)
    for angle in range(0, 360, 45):
        import math
        a = math.radians(angle)
        x1 = cx + math.cos(a) * size * 0.3
        y1 = cx + math.sin(a) * size * 0.3
        x2 = cx + math.cos(a) * size * 0.42
        y2 = cx + math.sin(a) * size * 0.42
        draw.line([x1, y1, x2, y2], fill=color, width=s)


def _moon(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    cx, cy = size * 0.55, size * 0.5
    r = size * 0.32
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=40, end=320, fill=color, width=s)
    draw.line(
        [
            cx + r * 0.77, cy - r * 0.64,
            cx + r * 0.65, cy - r * 0.32,
            cx + r * 0.4, cy + r * 0.1,
        ],
        fill=color,
        width=s,
        joint="curve",
    )


def _help(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    cx = size / 2
    r = size * 0.36
    draw.ellipse([cx - r, cx - r, cx + r, cx + r], outline=color, width=s)
    draw.arc([size * 0.32, size * 0.22, size * 0.68, size * 0.58], start=180, end=360, fill=color, width=s)
    draw.line([cx, size * 0.5, cx, size * 0.65], fill=color, width=s)
    draw.ellipse([cx - size * 0.04, size * 0.72, cx + size * 0.04, size * 0.8], fill=color)


def _user(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    r = size * 0.16
    cx = size / 2
    draw.ellipse([cx - r, size * 0.22, cx + r, size * 0.22 + r * 2], outline=color, width=s)
    draw.arc([size * 0.18, size * 0.5, size * 0.82, size * 0.95], start=200, end=340, fill=color, width=s)


def _lock(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    draw.rounded_rectangle(
        [size * 0.22, size * 0.45, size * 0.78, size * 0.85],
        radius=int(size * 0.08),
        outline=color,
        width=s,
    )
    draw.arc(
        [size * 0.3, size * 0.18, size * 0.7, size * 0.6], start=180, end=360, fill=color, width=s
    )


def _logout(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    draw.line([size * 0.22, size * 0.22, size * 0.22, size * 0.78], fill=color, width=s)
    draw.line([size * 0.22, size * 0.22, size * 0.5, size * 0.22], fill=color, width=s)
    draw.line([size * 0.22, size * 0.78, size * 0.5, size * 0.78], fill=color, width=s)
    draw.line([size * 0.42, size * 0.5, size * 0.82, size * 0.5], fill=color, width=s)
    draw.line([size * 0.65, size * 0.32, size * 0.82, size * 0.5], fill=color, width=s)
    draw.line([size * 0.65, size * 0.68, size * 0.82, size * 0.5], fill=color, width=s)


def _menu(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    for y in (size * 0.3, size * 0.5, size * 0.7):
        draw.line([size * 0.2, y, size * 0.8, y], fill=color, width=s)


def _qr(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    s = _stroke(size)
    pad = size * 0.18
    cell = (size - pad * 2) / 5
    for r in range(5):
        for c in range(5):
            if (r + c) % 2 == 0 and not (1 < r < 3 and 1 < c < 3):
                x = pad + c * cell
                y = pad + r * cell
                draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=color)
    draw.rectangle([pad, pad, pad + cell * 2, pad + cell * 2], outline=color, width=s)
    draw.rectangle([size - pad - cell * 2, pad, size - pad, pad + cell * 2], outline=color, width=s)
    draw.rectangle([pad, size - pad - cell * 2, pad + cell * 2, size - pad], outline=color, width=s)


_REGISTRY: dict[str, Painter] = {
    "shield": _shield,
    "users": _users,
    "user": _user,
    "building": _building,
    "key": _key,
    "sparkles": _sparkles,
    "mail": _mail,
    "gear": _gear,
    "activity": _activity,
    "grid": _grid,
    "plus": _plus,
    "check": _check,
    "close": _close,
    "copy": _copy,
    "eye": _eye,
    "search": _search,
    "bell": _bell,
    "power": _power,
    "refresh": _refresh,
    "arrow_right": _arrow_right,
    "chevron_left": _chevron_left,
    "alert": _alert,
    "trash": _trash,
    "sun": _sun,
    "moon": _moon,
    "help": _help,
    "lock": _lock,
    "logout": _logout,
    "menu": _menu,
    "qr": _qr,
}


def _render(name: str, size: int, color: str) -> Image.Image:
    painter = _REGISTRY.get(name)
    if painter is None:
        raise KeyError(f"Иконка не зарегистрирована: {name}")
    scale = 3
    canvas = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    painter(draw, size * scale, color)
    return canvas.resize((size, size), Image.LANCZOS)


@lru_cache(maxsize=256)
def _cached(name: str, size: int, color_light: str, color_dark: str) -> CTkImage:
    light_img = _render(name, size, color_light)
    dark_img = _render(name, size, color_dark)
    return CTkImage(light_image=light_img, dark_image=dark_img, size=(size, size))


def icon(name: str, size: int = 20, tone: str = "text") -> CTkImage:
    """Возвращает CTkImage для использования в кнопках/метках.

    `tone` — атрибут палитры (text, text_muted, primary, success, danger, warning, info, on_primary).
    """
    light = getattr(theme.LIGHT, tone)
    dark = getattr(theme.DARK, tone)
    return _cached(name, size, light, dark)
