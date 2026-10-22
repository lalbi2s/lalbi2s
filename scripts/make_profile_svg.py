"""Generate the whoami header: two terminal windows side by side in one SVG.

Writes assets/profile-dark.svg and assets/profile-light.svg. Left window: the
ASCII portrait and a prompt line. Right window: profile tiles and a stack
tile. Everything plays once (under 2 s) and respects prefers-reduced-motion.
"""
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from make_ascii_svg import cell_size, rows_for, rows_markup
from theme import FONT_STACK, REDUCED_MOTION_CSS, TOTAL_W, root_css

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

WIDTH = TOTAL_W
GAP = 16
WIN_W = (WIDTH - GAP) // 2
WIN_RX = 10
TITLEBAR_H = 34

LEFT_TITLE = "bilal@github: ~/portrait.sh"
RIGHT_TITLE = "bilal@github: ~/profile.sh"
PROMPT = "bilal@github:~$"
PROMPT_TEXT = "whoami: Bilal Saidi"

# (label, big text in accent color, small text below)
TILES = [
    ("role", "Junior developer", "C# / .NET & Python"),
    ("based", "Liège, BE", "open to Belgium & Luxembourg"),
    ("seeking", "R&D team", "back-end, test automation, AI apps"),
    ("now", "odoo-haccp", "Odoo module in Python"),
    ("prev", "Dev intern", "System QA, EVS, 2026"),
    ("certs", "AI-103 · AI-200", "ISTQB CTFL, in progress"),
]
STACK = ["C#", ".NET", "ASP.NET", "Python", "FastAPI", "Odoo", "PostgreSQL",
         "SQL Server", "Docker", "Azure", "k6", "pytest", "xUnit"]

CHAR_W = 0.6  # monospace advance width / font size
LABEL_SIZE, BIG_SIZE, SMALL_SIZE, CHIP_SIZE = 12, 16, 13, 12
TITLE_SIZE, PROMPT_SIZE = 12, 14

# Left window
PORTRAIT_X = 12
PORTRAIT_Y = TITLEBAR_H + 10
PORTRAIT_W = WIN_W - 2 * PORTRAIT_X
PORTRAIT_H = PORTRAIT_W / 100 * 2 * 53  # characters are twice as tall as wide
PROMPT_Y = PORTRAIT_Y + PORTRAIT_H + 30
LEFT_H = PROMPT_Y + 22

# Right window
TILE_PAD = 12
TILE_GAP = 10
TILE_X = 14
TILES_W = WIN_W - 2 * TILE_X
TILE_W = (TILES_W - TILE_GAP) / 2
SMALL_COLS = int((TILE_W - 2 * TILE_PAD) // (SMALL_SIZE * CHAR_W))
SMALL_PITCH = 17
CHIP_H, CHIP_GAP, CHIP_PAD = 22, 6, 8
CHIP_W = lambda text: len(text) * CHIP_SIZE * CHAR_W + 2 * CHIP_PAD  # noqa: E731

# Animation
ROW_DELAY_MS, ROW_DURATION_MS, ROW_START_MS = 27, 250, 200  # last row ends at 1.85 s
TILE_DELAY_MS, TILE_DURATION_MS, TILE_START_MS = 160, 220, 250  # last tile ends at 1.43 s
PROMPT_DELAY_MS = 1600  # ends at 1.8 s

NBSP = " "


def wrap_small(text: str) -> list[str]:
    glued = text.replace(" & ", " &" + NBSP).replace("in progress", "in" + NBSP + "progress")
    lines = textwrap.wrap(glued, SMALL_COLS, break_long_words=False, break_on_hyphens=False)
    return [line.replace(NBSP, " ") for line in lines]


def chip_rows() -> list[list[tuple[str, float]]]:
    """Greedy layout of the stack chips: rows of (text, x offset)."""
    inner = TILES_W - 2 * TILE_PAD
    rows, row, x = [], [], 0.0
    for text in STACK:
        w = CHIP_W(text)
        if row and x + w > inner:
            rows.append(row)
            row, x = [], 0.0
        row.append((text, x))
        x += w + CHIP_GAP
    rows.append(row)
    return rows


def window(x: float, height: float, title: str, index: int) -> str:
    cx = x + WIN_W / 2
    return (
        f'<g class="win" style="--w:{index}">'
        f'<rect class="panel" x="{x + 0.5}" y="0.5" width="{WIN_W - 1}" '
        f'height="{height - 1:g}" rx="{WIN_RX}"/>'
        f'<line class="rule" x1="{x + 0.5}" y1="{TITLEBAR_H}" x2="{x + WIN_W - 0.5}" y2="{TITLEBAR_H}"/>'
        + "".join(f'<circle class="dot" cx="{x + 18 + 14 * i}" cy="{TITLEBAR_H / 2}" r="4"/>'
                  for i in range(3))
        + f'<text class="wtitle" x="{cx}" y="{TITLEBAR_H / 2 + 4}" text-anchor="middle">'
        f"{escape(title)}</text></g>"
    )


def tiles_markup(height: float) -> str:
    small_lines = [wrap_small(small) for _, _, small in TILES]
    content_h = [TILE_PAD + 10 + 22 + 8 + (len(lines) - 1) * SMALL_PITCH + 12 + 6
                 for lines in small_lines]
    row_h = [max(content_h[i], content_h[i + 1]) for i in (0, 2, 4)]

    chips = chip_rows()
    stack_h = 22 + 12 + len(chips) * CHIP_H + (len(chips) - 1) * CHIP_GAP + TILE_PAD + 4

    y0 = TITLEBAR_H + 12
    natural = y0 + sum(row_h) + 3 * TILE_GAP + stack_h + 14
    extra = max(0, height - natural) / 3
    row_h = [h + extra for h in row_h]

    out = []
    y = y0
    for r in range(3):
        for c in range(2):
            n = 2 * r + c
            label, big, _ = TILES[n]
            x = WIN_W + GAP + TILE_X + c * (TILE_W + TILE_GAP)
            used = max(content_h[2 * r], content_h[2 * r + 1])
            top = y + (row_h[r] - used) / 2  # same text baseline for both tiles of a row
            small = "".join(
                f'<text class="small" x="{x + TILE_PAD:g}" y="{top + TILE_PAD + 10 + 22 + 8 + k * SMALL_PITCH + 3:g}">'
                f"{escape(line)}</text>"
                for k, line in enumerate(small_lines[n])
            )
            out.append(
                f'<g class="tile" style="--i:{n}">'
                f'<rect class="tilebox" x="{x:g}" y="{y:g}" width="{TILE_W:g}" '
                f'height="{row_h[r]:g}" rx="6"/>'
                f'<text class="label" x="{x + TILE_PAD:g}" y="{top + TILE_PAD + 9:g}">$ {label}</text>'
                f'<text class="big" x="{x + TILE_PAD:g}" y="{top + TILE_PAD + 10 + 22:g}">{escape(big)}</text>'
                f"{small}</g>"
            )
        y += row_h[r] + TILE_GAP

    x = WIN_W + GAP + TILE_X
    chip_y = y + 22 + 12 - 6
    chip_parts = []
    for r, row in enumerate(chips):
        for text, dx in row:
            cx = x + TILE_PAD + dx
            cy = chip_y + r * (CHIP_H + CHIP_GAP)
            chip_parts.append(
                f'<rect class="chip" x="{cx:g}" y="{cy:g}" width="{CHIP_W(text):g}" '
                f'height="{CHIP_H}" rx="4"/>'
                f'<text class="chiptext" x="{cx + CHIP_W(text) / 2:g}" y="{cy + CHIP_H / 2 + 4:g}" '
                f'text-anchor="middle">{escape(text)}</text>'
            )
    out.append(
        f'<g class="tile" style="--i:6">'
        f'<rect class="tilebox" x="{x:g}" y="{y:g}" width="{TILES_W:g}" height="{stack_h:g}" rx="6"/>'
        f'<text class="label" x="{x + TILE_PAD:g}" y="{y + TILE_PAD + 9:g}">$ stack</text>'
        + "".join(chip_parts) + "</g>"
    )
    return "\n".join(out)


def alt_text() -> str:
    """All the text of the tiles, for the alt attribute in the README."""
    return ("Two terminal windows. Left: ASCII portrait of Bilal Saidi with the prompt "
            "'whoami: Bilal Saidi'. Right: "
            + "; ".join(f"{label}: {big} | {small}" for label, big, small in TILES)
            + "; stack: " + ", ".join(STACK))


def build_svg(variant: str) -> str:
    height = round(LEFT_H)
    right_x = WIN_W + GAP

    prompt_w = (len(PROMPT) + 1 + len(PROMPT_TEXT)) * PROMPT_SIZE * CHAR_W
    prompt = (
        f'<g class="late"><text class="prompt" x="{PORTRAIT_X + 2}" y="{PROMPT_Y:g}" '
        f'textLength="{prompt_w:g}" lengthAdjust="spacing" xml:space="preserve">'
        f'<tspan class="acc">{PROMPT}</tspan> {PROMPT_TEXT}</text>'
        f'<rect class="cursor" x="{PORTRAIT_X + 2 + prompt_w + 4:g}" y="{PROMPT_Y - 12:g}" '
        f'width="8" height="16"/></g>'
    )

    _, _, font_size = cell_size(PORTRAIT_W, PORTRAIT_H)
    portrait = rows_markup(rows_for(variant), PORTRAIT_X, PORTRAIT_Y, PORTRAIT_W, PORTRAIT_H)

    css = (
        root_css(variant)
        + f"svg{{font-family:{FONT_STACK}}}"
        + ".panel{fill:var(--surface);stroke:var(--border)}"
        + ".rule{stroke:var(--border)}"
        + ".dot{fill:var(--text-muted);opacity:.45}"
        + f".wtitle{{font-size:{TITLE_SIZE}px;fill:var(--text-muted)}}"
        + f".art{{font-size:{font_size:.2f}px;fill:var(--text)}}"
        + f".prompt{{font-size:{PROMPT_SIZE}px;fill:var(--text)}}.acc{{fill:var(--accent)}}"
        + ".cursor{fill:var(--accent)}"
        + ".tilebox{fill:var(--bg);stroke:var(--border)}"
        + f".label{{font-size:{LABEL_SIZE}px;fill:var(--text-muted)}}"
        + f".big{{font-size:{BIG_SIZE}px;font-weight:700;fill:var(--accent)}}"
        + f".small{{font-size:{SMALL_SIZE}px;fill:var(--text)}}"
        + ".chip{fill:var(--surface);stroke:var(--border)}"
        + f".chiptext{{font-size:{CHIP_SIZE}px;fill:var(--text)}}"
        # animations: each plays once and keeps its end state
        + ".win{animation:fade 200ms ease-out both}"
        + ".cover{fill:var(--surface);transform-box:fill-box;transform-origin:right;"
        + "transform:scaleX(0);"
        + f"animation:write {ROW_DURATION_MS}ms linear both;"
        + f"animation-delay:calc({ROW_START_MS}ms + var(--i) * {ROW_DELAY_MS}ms)}}"
        + f".tile{{animation:rise {TILE_DURATION_MS}ms ease-out both;"
        + f"animation-delay:calc({TILE_START_MS}ms + var(--i) * {TILE_DELAY_MS}ms)}}"
        + f".late{{animation:fade 200ms ease-out both;animation-delay:{PROMPT_DELAY_MS}ms}}"
        + "@keyframes fade{from{opacity:0}}"
        + "@keyframes write{from{transform:scaleX(1)}to{transform:scaleX(0)}}"
        + "@keyframes rise{from{opacity:0;transform:translateY(6px)}}"
        + REDUCED_MOTION_CSS
    )

    alt = escape(alt_text(), {'"': "&quot;"})

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{alt}">\n'
        f"<title>bilal@github ~ $ whoami</title>\n"
        f"<style>{css}</style>\n"
        + window(0, height, LEFT_TITLE, 0) + "\n"
        + window(right_x, height, RIGHT_TITLE, 1) + "\n"
        + f'<g class="art">\n{portrait}\n</g>\n{prompt}\n'
        + tiles_markup(height) + "\n</svg>\n"
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for variant in ("dark", "light"):
        out = ASSETS / f"profile-{variant}.svg"
        out.write_text(build_svg(variant), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
