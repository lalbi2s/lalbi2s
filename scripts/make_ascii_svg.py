"""Turn source-prepped.png into ASCII rows and SVG markup for them.

Used by make_profile_svg.py. One text color, no per-character color.
"""
from pathlib import Path
from xml.sax.saxutils import escape

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"

COLS, ROWS = 100, 53
RAMP = " .`:-=+*cs#%@"  # light to dark, the space is the background
GAMMA = 1.5  # above 1 keeps mid tones light so only real shadows get dense glyphs
POSITIVE_GAMMA = 1.2
LOW_PCT, HIGH_PCT = 2, 98  # tone range stretched over the whole ramp

CHAR_RATIO = 0.6  # monospace advance width / font size


def background_mask(gray) -> "np.ndarray":
    """True where the empty paper is: the white area connected to the top corners.

    White that is enclosed (forehead highlights, the shirt) belongs to the
    subject.
    """
    h, w = gray.shape
    white = (gray >= 250).astype(np.uint8)
    flooded = np.zeros((h + 2, w + 2), np.uint8)
    for seed in ((0, 0), (w - 1, 0)):
        if white[seed[1], seed[0]]:
            cv2.floodFill(white, flooded, seed, 2)
    return white == 2


def to_rows(path: Path, positive: bool = False) -> list[str]:
    """ASCII rows. With positive=True, light parts of the drawing get the
    dense glyphs (for a light-on-dark portrait that reads like the drawing)."""
    gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise SystemExit(f"Cannot read {path}, run prep_photo.py first")
    small = cv2.resize(gray, (COLS, ROWS), interpolation=cv2.INTER_AREA)
    if positive:
        bg = cv2.resize(background_mask(gray).astype(np.uint8) * 255, (COLS, ROWS),
                        interpolation=cv2.INTER_AREA) > 127
        return positive_rows(small, bg)

    # Stretch the tones of the subject (not the white background) over the
    # whole ramp.
    subject = small[small < 250]
    lo, hi = np.percentile(subject, [LOW_PCT, HIGH_PCT])

    rows = []
    for line in small:
        chars = []
        for value in line:
            if value >= 250:
                chars.append(RAMP[0])
                continue
            darkness = np.clip((hi - value) / (hi - lo), 0, 1) ** GAMMA
            chars.append(RAMP[1 + round(darkness * (len(RAMP) - 2))])
        rows.append("".join(chars))
    return rows


def positive_rows(small, bg) -> list[str]:
    subject = small[~bg]
    lo, hi = np.percentile(subject, [LOW_PCT, HIGH_PCT])
    rows = []
    for line, bg_line in zip(small, bg):
        chars = []
        for value, is_bg in zip(line, bg_line):
            if is_bg:
                chars.append(RAMP[0])
                continue
            light = np.clip((value - lo) / (hi - lo), 0, 1) ** POSITIVE_GAMMA
            # At least the faintest glyph, so dark hair keeps its outline.
            chars.append(RAMP[1 + round(light * (len(RAMP) - 2))])
        rows.append("".join(chars))
    return rows


def cell_size(width: float, height: float) -> tuple[float, float, float]:
    """Character cell (width, height) and font size for a grid fitted in a box."""
    cw = width / COLS
    lh = height / ROWS
    return cw, lh, cw / CHAR_RATIO


def rows_markup(rows: list[str], x0: float, y0: float, width: float, height: float) -> str:
    """SVG for the portrait rows, written left to right, top to bottom.

    Each row is a <text> with a cover rectangle (class "cover", filled by the
    stylesheet with the window color) that a CSS animation shrinks to the
    right. The delay of a row comes from its --i custom property.
    """
    cw, lh, _ = cell_size(width, height)
    parts = []
    for i, row in enumerate(rows):
        text = row.strip(" ")
        if not text:
            continue
        lead = len(row) - len(row.lstrip(" "))
        x = x0 + lead * cw
        y = y0 + i * lh
        text_w = len(text) * cw
        parts.append(
            f'<g style="--i:{i}">'
            f'<text x="{x:.2f}" y="{y + lh * 0.8:.2f}" textLength="{text_w:.2f}" '
            f'lengthAdjust="spacing" xml:space="preserve">{escape(text)}</text>'
            f'<rect class="cover" x="{x - 1:.2f}" y="{y:.2f}" '
            f'width="{text_w + 2:.2f}" height="{lh:.2f}"/></g>'
        )
    return "\n".join(parts)


def rows_for(variant: str) -> list[str]:
    """Light text on dark reads like the drawing when light areas are dense;
    dark text on light does the opposite."""
    return to_rows(SRC, positive=(variant == "dark"))
