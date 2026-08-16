#!/usr/bin/env python3
"""
make_ascii_svg.py — turn a photo into a monochrome, self-typing ASCII portrait SVG.

Usage:
    pip install pillow numpy
    python make_ascii_svg.py your-photo.jpg -o chris-ascii.svg

Design principles (matching the blog post's approach):
  - One density ramp, light->dark, leading space = background disappears
  - Monochrome fill only (no per-character rainbow -- that's what makes most
    ASCII art look noisy)
  - Each row wipes in left-to-right, staggered top-to-bottom, plays once,
    freezes (no looping)
  - Pure CSS/SMIL animation inside the SVG -- GitHub strips <script> and most
    inline CSS, but it DOES run SVG animations, so all motion lives in the SVG
"""

import argparse
import sys
from PIL import Image, ImageOps
import numpy as np

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space = background


def image_to_grid(path, cols=100, char_aspect=2.0):
    """Load an image and downsample it into a cols x rows brightness grid."""
    img = Image.open(path).convert("L")  # grayscale
    img = ImageOps.autocontrast(img, cutoff=1)  # cheap CLAHE-ish contrast boost

    w, h = img.size
    # characters are taller than they are wide, so compress rows accordingly
    rows = max(1, int(cols * (h / w) / char_aspect))
    img = img.resize((cols, rows))

    arr = np.asarray(img, dtype=np.float32) / 255.0  # 0 = black, 1 = white
    return arr


def grid_to_ascii(arr):
    """Map each brightness value to a ramp character. Bright -> sparse/space."""
    n = len(RAMP) - 1
    lines = []
    for row in arr:
        line = "".join(RAMP[int(round((1 - v) * n))] for v in row)
        lines.append(line)
    return lines


def build_svg(lines, char_w=7, char_h=13, fill="#c9d1d9", font="ui-monospace, Menlo, monospace"):
    rows = len(lines)
    cols = max(len(l) for l in lines) if lines else 0
    width = cols * char_w + 20
    height = rows * char_h + 20

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="{font}" font-size="{char_h}">',
        "<style>",
        "  .row { opacity: 0; }",
        "  @keyframes typein { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }",
        "  @keyframes fadein { to { opacity: 1; } }",
    ]

    for i in range(rows):
        delay = i * 0.045
        svg_parts.append(
            f"  .row-{i} {{ animation: typein 0.35s steps(24) {delay:.3f}s forwards, "
            f"fadein 0.01s {delay:.3f}s forwards; }}"
        )

    svg_parts.append("</style>")

    for i, line in enumerate(lines):
        y = 10 + (i + 1) * char_h
        escaped = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        svg_parts.append(
            f'  <text class="row row-{i}" x="10" y="{y}" fill="{fill}" '
            f'xml:space="preserve">{escaped}</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo", help="path to your input photo")
    ap.add_argument("-o", "--out", default="chris-ascii.svg")
    ap.add_argument("--cols", type=int, default=100, help="character columns (width)")
    args = ap.parse_args()

    grid = image_to_grid(args.photo, cols=args.cols)
    lines = grid_to_ascii(grid)
    svg = build_svg(lines)

    with open(args.out, "w") as f:
        f.write(svg)

    print(f"Wrote {args.out}  ({len(lines)} rows x {args.cols} cols)")


if __name__ == "__main__":
    main()
