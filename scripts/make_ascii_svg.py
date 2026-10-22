"""Turn source-prepped.png into animated ASCII portraits.

Writes assets/portrait-dark.svg and assets/portrait-light.svg. One text
color, no per-character color. Each row is written from left to right, from
top to bottom, once; then the portrait stays still.
"""
from pathlib import Path
from xml.sax.saxutils import escape

import cv2
import numpy as np

from theme import (FONT_STACK, PORTRAIT_H, PORTRAIT_W, RADIUS,
                   REDUCED_MOTION_CSS, root_css)

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
ASSETS = ROOT / "assets"

COLS, ROWS = 100, 53
RAMP = " .`:-=+*cs#%@"  # light to dark, the space is the background
GAMMA = 1.5  # above 1 keeps mid tones light so only real shadows get dense glyphs
POSITIVE_GAMMA = 1.2
LOW_PCT, HIGH_PCT = 2, 98  # tone range stretched over the whole ramp

PAD = 12
CHAR_RATIO = 0.6  # monospace advance width / font size
ROW_DELAY_MS = 32.5  # 52 * 32.5 + 250 = 1.94 s in total
ROW_DURATION_MS = 250


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


def build_svg(rows: list[str], variant: str) -> str:
    cw = (PORTRAIT_W - 2 * PAD) / COLS
    lh = (PORTRAIT_H - 2 * PAD) / ROWS
    font_size = cw / CHAR_RATIO

    parts = []
    for i, row in enumerate(rows):
        text = row.strip(" ")
        if not text:
            continue
        lead = len(row) - len(row.lstrip(" "))
        x = PAD + lead * cw
        y = PAD + i * lh
        width = len(text) * cw
        parts.append(
            f'<g class="row" style="--i:{i}">'
            f'<text x="{x:.2f}" y="{y + lh * 0.8:.2f}" textLength="{width:.2f}" '
            f'lengthAdjust="spacing" xml:space="preserve">{escape(text)}</text>'
            f'<rect class="cover" x="{x - 1:.2f}" y="{y:.2f}" '
            f'width="{width + 2:.2f}" height="{lh:.2f}"/></g>'
        )

    css = (
        root_css(variant)
        + f"svg{{font-family:{FONT_STACK}}}"
        + ".panel{fill:var(--surface);stroke:var(--border)}"
        + f".art{{font-size:{font_size:.2f}px;fill:var(--text)}}"
        + ".cover{fill:var(--surface);transform-box:fill-box;transform-origin:right;"
        + "transform:scaleX(0);"
        + f"animation:write {ROW_DURATION_MS}ms linear both;"
        + f"animation-delay:calc(var(--i) * {ROW_DELAY_MS}ms)}}"
        + "@keyframes write{from{transform:scaleX(1)}to{transform:scaleX(0)}}"
        + REDUCED_MOTION_CSS
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PORTRAIT_W}" height="{PORTRAIT_H}" '
        f'viewBox="0 0 {PORTRAIT_W} {PORTRAIT_H}" role="img" '
        f'aria-label="ASCII portrait of Bilal">\n'
        f"<title>ASCII portrait of Bilal</title>\n"
        f"<style>{css}</style>\n"
        f'<rect class="panel" x="0.5" y="0.5" width="{PORTRAIT_W - 1}" '
        f'height="{PORTRAIT_H - 1}" rx="{RADIUS}"/>\n'
        f'<g class="art">\n' + "\n".join(parts) + "\n</g>\n</svg>\n"
    )


def main() -> None:
    # Light text on dark reads like the drawing when light areas are dense;
    # dark text on light does the opposite.
    art = {"dark": to_rows(SRC, positive=True), "light": to_rows(SRC)}
    ASSETS.mkdir(exist_ok=True)
    for variant, rows in art.items():
        out = ASSETS / f"portrait-{variant}.svg"
        out.write_text(build_svg(rows, variant), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
