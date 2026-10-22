"""Generate the neofetch-style info card.

Writes assets/card-dark.svg and assets/card-light.svg. Keys use the accent
color, values the text color. Long values wrap onto several lines. Lines
fade in one after the other, once.
"""
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from theme import CARD_W, FONT_STACK, RADIUS, REDUCED_MOTION_CSS, root_css

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

TITLE = "bilal@lalbi2s"
ROWS = [
    ("Role", "Junior developer · C# / .NET & Python"),
    ("Based", "Liège, Belgium · open to Belgium & Luxembourg"),
    ("Seeking", "Junior role in an R&D team: back-end, test automation, AI apps"),
    ("Now", "Building odoo-haccp · preparing AI-103, AI-200, ISTQB CTFL"),
    ("Prev", "Developer intern, System QA · EVS (Feb–Apr 2026)"),
    ("Stack", "C# · .NET · ASP.NET · Python · FastAPI · Odoo"),
    ("Data", "PostgreSQL · SQL Server · SQLite"),
    ("Testing", "k6 · pytest · xUnit · Grafana · Jira / Xray"),
    ("Tools", "Git · GitHub · Docker · Azure"),
]

NBSP = "\u00a0"
FONT_SIZE = 16
CHAR_W = FONT_SIZE * 0.6  # monospace advance width
PAD = 20
KEY_COLS = 9  # longest key ("Seeking") plus two spaces
VALUE_X = PAD + KEY_COLS * CHAR_W
MAX_CHARS = int((CARD_W - PAD - VALUE_X) // CHAR_W)

TITLE_Y = 44
RULE_Y = 60
FIRST_ROW_Y = 94
LINE_PITCH = 22  # between wrapped lines of one value
ROW_GAP = 12  # extra space between two entries
BOTTOM_PAD = 24

LINE_DELAY_MS = 170  # 9 * 170 + 220 = 1.75 s in total
LINE_DURATION_MS = 220


def wrap(value: str, limit: int = MAX_CHARS) -> list[str]:
    """Break a value on word boundaries into lines of at most `limit` characters."""
    # Glue separators to their neighbors so a line never starts with "·" or
    # ends with a lone "/" or "&".
    glued = (value.replace(" · ", NBSP + "· ")
                  .replace(" / ", NBSP + "/" + NBSP)
                  .replace(" & ", " &" + NBSP))
    lines = textwrap.wrap(glued, limit, break_long_words=False, break_on_hyphens=False)
    return [line.replace(NBSP, " ") for line in lines]


def build_svg(variant: str) -> tuple[str, int]:
    lines = [
        f'<g class="line" style="--i:0"><text class="title" x="{PAD}" y="{TITLE_Y}">'
        f"{escape(TITLE)}</text></g>",
        f'<line class="rule" x1="{PAD}" y1="{RULE_Y}" x2="{CARD_W - PAD}" y2="{RULE_Y}"/>',
    ]
    y = FIRST_ROW_Y
    for i, (key, value) in enumerate(ROWS, start=1):
        wrapped = wrap(value)
        texts = "".join(
            f'<text class="value" x="{VALUE_X:g}" y="{y + n * LINE_PITCH}">{escape(line)}</text>'
            for n, line in enumerate(wrapped)
        )
        lines.append(
            f'<g class="line" style="--i:{i}">'
            f'<text class="key" x="{PAD}" y="{y}">{escape(key)}</text>{texts}</g>'
        )
        y += (len(wrapped) - 1) * LINE_PITCH + LINE_PITCH + ROW_GAP
    height = y - ROW_GAP + BOTTOM_PAD - LINE_PITCH + 8

    css = (
        root_css(variant)
        + f"svg{{font-family:{FONT_STACK};font-size:{FONT_SIZE}px}}"
        + ".panel{fill:var(--surface);stroke:var(--border)}"
        + ".title{fill:var(--accent);font-weight:700}"
        + ".rule{stroke:var(--border);stroke-width:1}"
        + ".key{fill:var(--accent);font-weight:700}"
        + ".value{fill:var(--text)}"
        + f".line{{animation:in {LINE_DURATION_MS}ms ease-out both;"
        + f"animation-delay:calc(var(--i) * {LINE_DELAY_MS}ms)}}"
        + "@keyframes in{from{opacity:0;transform:translateX(-8px)}}"
        + REDUCED_MOTION_CSS
    )

    full = "; ".join(f"{k}: {v}" for k, v in ROWS)
    label = f"Profile card {TITLE}. {full}"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{height}" '
        f'viewBox="0 0 {CARD_W} {height}" role="img" aria-label="{escape(label, {chr(34): "&quot;"})}">\n'
        f"<title>{escape(TITLE)}</title>\n"
        f"<style>{css}</style>\n"
        f'<rect class="panel" x="0.5" y="0.5" width="{CARD_W - 1}" '
        f'height="{height - 1}" rx="{RADIUS}"/>\n'
        + "\n".join(lines)
        + "\n</svg>\n"
    )
    return svg, height


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for variant in ("dark", "light"):
        out = ASSETS / f"card-{variant}.svg"
        svg, height = build_svg(variant)
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({CARD_W}x{height})")


if __name__ == "__main__":
    main()
