from __future__ import annotations
from math import ceil, sqrt
from pathlib import Path
from typing import Iterable, Tuple
from PIL import Image


def build_collage(
    image_paths: Iterable[Path],
    out_path: Path,
    thumb_size: Tuple[int, int] = (320, 180),
    padding: int = 10,
    bg_color: Tuple[int, int, int] = (245, 245, 245),
) -> Path:
    paths = [p for p in image_paths if p.exists()]
    if not paths:
        raise ValueError("No images found for collage.")

    n = len(paths)
    cols = ceil(sqrt(n))
    rows = ceil(n / cols)

    tw, th = thumb_size
    canvas_w = cols * tw + (cols + 1) * padding
    canvas_h = rows * th + (rows + 1) * padding
    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)

    for idx, p in enumerate(paths):
        img = Image.open(p).convert("RGB")
        img.thumbnail((tw, th))

        x0 = padding + (idx % cols) * (tw + padding)
        y0 = padding + (idx // cols) * (th + padding)

        ox = x0 + (tw - img.width) // 2
        oy = y0 + (th - img.height) // 2
        canvas.paste(img, (ox, oy))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return out_path


def show_image(path: Path) -> None:
    Image.open(path).show()
