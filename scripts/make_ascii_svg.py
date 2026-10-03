"""
Convert a portrait photo into a clean, monochrome ASCII-art SVG.

The portrait types itself in like a terminal and then holds.
"""

from PIL import Image, ImageEnhance, ImageFilter
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Input image
SRC = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.path.join(HERE, "..", "data", "source-prepped.png")
)

# Output SVG
OUT = (
    sys.argv[2]
    if len(sys.argv) > 2
    else os.path.join(HERE, "..", "ascii-portrait.svg")
)

# ASCII settings
COLS = 100
ROWS = 53
CELL_W = 8
CELL_H = 15

RAMP = " .`:-=+*cs#%@"

# Image tuning
CONTRAST = 1.05
BRIGHTNESS = 1.0
GAMMA = 1.18
SHARPEN = False
WHITE_FLOOR = 0.80

# Layout
PAD = 20
TITLEBAR_H = 30
STATUS_H = 30

ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H

CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

# Colors
BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"

# Animation timing
ROW_DUR = 0.11
STAGGER = 0.11


# ---------------------------------------------------------
# 1. Read and process image
# ---------------------------------------------------------

im = Image.open(SRC).convert("L")

if SHARPEN:
    im = im.filter(
        ImageFilter.UnsharpMask(
            radius=2,
            percent=140,
            threshold=2
        )
    )

im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
im = ImageEnhance.Contrast(im).enhance(CONTRAST)

im = im.resize(
    (COLS, ROWS),
    Image.LANCZOS
)

px = im.load()

STATIC = bool(os.environ.get("STATIC"))


# ---------------------------------------------------------
# 2. Convert image to ASCII
# ---------------------------------------------------------

rows_txt = []

for y in range(ROWS):

    chars = []

    for x in range(COLS):

        lum = px[x, y] / 255.0

        lum = pow(lum, GAMMA)

        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue

        idx = int(
            (1.0 - lum)
            * (len(RAMP) - 1)
            + 0.5
        )

        idx = max(
            0,
            min(
                len(RAMP) - 1,
                idx
            )
        )

        chars.append(RAMP[idx])

    rows_txt.append(
        "".join(chars)
    )


# ---------------------------------------------------------
# 3. Build SVG
# ---------------------------------------------------------

art_top = TITLEBAR_H + PAD * 0.35

parts = []

parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{CANVAS_W}" '
    f'height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
)

# Background gradient
parts.append(
    '<defs>'
    f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/>'
    f'<stop offset="1" stop-color="{BG}"/>'
    f'</linearGradient>'
    '</defs>'
)

# Background
parts.append(
    f'<rect width="{CANVAS_W}" '
    f'height="{CANVAS_H}" '
    f'rx="12" '
    f'fill="url(#bg)"/>'
)

# Border
parts.append(
    f'<rect x="0.5" y="0.5" '
    f'width="{CANVAS_W - 1}" '
    f'height="{CANVAS_H - 1}" '
    f'rx="12" '
    f'fill="none" '
    f'stroke="{FRAME}" '
    f'stroke-width="1"/>'
)


# ---------------------------------------------------------
# 4. Terminal title bar
# ---------------------------------------------------------

parts.append(
    f'<line x1="0" '
    f'y1="{TITLEBAR_H}" '
    f'x2="{CANVAS_W}" '
    f'y2="{TITLEBAR_H}" '
    f'stroke="{FRAME}"/>'
)

# Mac-style terminal dots
for i, dotcol in enumerate(
    ["#ff5f56", "#ffbd2e", "#27c93f"]
):

    parts.append(
        f'<circle '
        f'cx="{PAD + i * 16}" '
        f'cy="{TITLEBAR_H / 2}" '
        f'r="5" '
        f'fill="{dotcol}"/>'
    )


# YOUR terminal title
parts.append(
    f'<text '
    f'x="{CANVAS_W / 2}" '
    f'y="{TITLEBAR_H / 2 + 4}" '
    f'fill="{TITLE_TEXT}" '
    f'font-size="12" '
    f'text-anchor="middle">'
    f'abh4y-rig@github: ~$ ./portrait.sh'
    f'</text>'
)


# ---------------------------------------------------------
# 5. ASCII rows + typing animation
# ---------------------------------------------------------

font_size = CELL_H * 0.86

for ry, line in enumerate(rows_txt):

    y = (
        art_top
        + ry * CELL_H
        + CELL_H * 0.74
    )

    row_y = (
        art_top
        + ry * CELL_H
    )

    delay = ry * STAGGER

    safe = html.escape(line)

    text = (
        f'<text '
        f'xml:space="preserve" '
        f'x="{PAD}" '
        f'y="{y:.1f}" '
        f'fill="{INK}" '
        f'font-size="{font_size:.1f}" '
        f'textLength="{ART_W}" '
        f'lengthAdjust="spacing">'
        f'{safe}'
        f'</text>'
    )

    if STATIC:

        parts.append(text)
        continue

    # Reveal mask
    parts.append(
        f'<clipPath id="r{ry}">'
        f'<rect '
        f'x="{PAD}" '
        f'y="{row_y:.1f}" '
        f'height="{CELL_H}" '
        f'width="0">'

        f'<animate '
        f'attributeName="width" '
        f'from="0" '
        f'to="{ART_W}" '
        f'begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" '
        f'fill="freeze"/>'

        f'</rect>'
        f'</clipPath>'
    )

    # ASCII text
    parts.append(
        f'<g clip-path="url(#r{ry})">'
        f'{text}'
        f'</g>'
    )

    # Cursor
    parts.append(
        f'<rect '
        f'y="{row_y + 1:.1f}" '
        f'width="{CELL_W}" '
        f'height="{CELL_H - 2}" '
        f'fill="{CURSOR}" '
        f'opacity="0">'

        f'<animate '
        f'attributeName="x" '
        f'from="{PAD}" '
        f'to="{PAD + ART_W}" '
        f'begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" '
        f'fill="freeze"/>'

        f'<set '
        f'attributeName="opacity" '
        f'to="0.85" '
        f'begin="{delay:.3f}s"/>'

        f'<set '
        f'attributeName="opacity" '
        f'to="0" '
        f'begin="{delay + ROW_DUR:.3f}s"/>'

        f'</rect>'
    )


# ---------------------------------------------------------
# 6. Bottom terminal/status bar
# ---------------------------------------------------------

status_line_y = (
    TITLEBAR_H
    + ART_H
    + PAD * 0.35
)

status_y = status_line_y + 19

parts.append(
    f'<line '
    f'x1="0" '
    f'y1="{status_line_y:.1f}" '
    f'x2="{CANVAS_W}" '
    f'y2="{status_line_y:.1f}" '
    f'stroke="{FRAME}"/>'
)

# YOUR username + name
parts.append(
    f'<text '
    f'x="{PAD}" '
    f'y="{status_y:.1f}" '
    f'fill="{TITLE_TEXT}" '
    f'font-size="13">'
    f'abh4y-rig@github:~$ whoami '
    f'<tspan fill="{INK}">Abhay</tspan>'
    f'</text>'
)

# Blinking cursor
parts.append(
    f'<rect '
    f'x="{PAD + 196}" '
    f'y="{status_y - 12:.1f}" '
    f'width="8" '
    f'height="14" '
    f'fill="{INK}">'

    f'<animate '
    f'attributeName="opacity" '
    f'values="1;1;0;0" '
    f'keyTimes="0;0.5;0.51;1" '
    f'dur="1s" '
    f'repeatCount="indefinite"/>'

    f'</rect>'
)


# ---------------------------------------------------------
# 7. Finish SVG
# ---------------------------------------------------------

parts.append("</svg>")

svg = "".join(parts)

with open(
    OUT,
    "w",
    encoding="utf-8"
) as f:

    f.write(svg)

print(
    "wrote",
    OUT,
    len(svg),
    "bytes;",
    CANVAS_W,
    "x",
    CANVAS_H
)