"""Render the contribution heatmap from data/contributions.json.

Writes assets/contrib-dark.svg and assets/contrib-light.svg: 53 weeks x 7
days of rounded cells, a Less -> More legend and one line with the total.
The cells appear once along the diagonal.
"""
import json
from datetime import date
from pathlib import Path

from theme import (FONT_STACK, RADIUS, REDUCED_MOTION_CSS, TOTAL_W,
                   heat_tokens, root_css)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
ASSETS = ROOT / "assets"

WEEKS, DAYS = 53, 7
CELL = 12
GAP = 3
PITCH = CELL + GAP
CELL_RX = 3

WIDTH = TOTAL_W
PAD = 20
LABEL_W = 34  # room for the Mon / Wed / Fri labels
GRID_W = WEEKS * PITCH - GAP
GRID_X = (WIDTH - GRID_W + LABEL_W) // 2  # grid centered, labels to its left
MONTHS_Y = 30
GRID_Y = 42
GRID_H = DAYS * PITCH - GAP
LEGEND_Y = GRID_Y + GRID_H + 28
HEIGHT = LEGEND_Y + CELL + 20

LABEL_SIZE = 12
TOTAL_SIZE = 16
CELL_DELAY_MS = 30  # (52 + 6) * 30 + 200 = 1.94 s in total
CELL_DURATION_MS = 200


def month_labels(first: date) -> list[tuple[int, str]]:
    """(week index, month name) where a new month starts, if there is room."""
    labels = []
    last_month = None
    for week in range(WEEKS):
        start = date.fromordinal(first.toordinal() + week * 7)
        if start.month != last_month:
            labels.append((week, f"{start:%b}"))
            last_month = start.month
    # A label squeezed against the next one would overlap it: drop it.
    return [l for i, l in enumerate(labels)
            if i + 1 == len(labels) or labels[i + 1][0] - l[0] >= 3]


def build_svg(data: dict, variant: str) -> str:
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])  # a Sunday: GitHub weeks start on Sunday

    cells = []
    for day in days:
        d = date.fromisoformat(day["date"])
        offset = (d - first).days
        week, dow = divmod(offset, 7)
        x = GRID_X + week * PITCH
        y = GRID_Y + dow * PITCH
        cells.append(
            f'<rect class="cell l{day["level"]}" style="--d:{week + dow}" '
            f'x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{CELL_RX}"/>'
        )

    months = "".join(
        f'<text x="{GRID_X + week * PITCH}" y="{MONTHS_Y}">{name}</text>'
        for week, name in month_labels(first)
    )
    weekdays = "".join(
        f'<text x="{GRID_X - 8}" y="{GRID_Y + row * PITCH + CELL - 2}" '
        f'text-anchor="end">{name}</text>'
        for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    # Legend, right-aligned with the grid: Less [5 cells] More.
    legend_cells_w = 5 * PITCH - GAP
    more_w = 4 * LABEL_SIZE * 0.6
    grid_right = GRID_X + GRID_W
    more_x = grid_right - more_w
    cells_x = more_x - 6 - legend_cells_w
    less_x = cells_x - 6 - 4 * LABEL_SIZE * 0.6
    legend = (
        f'<g class="muted" font-size="{LABEL_SIZE}">'
        f'<text x="{less_x:g}" y="{LEGEND_Y + CELL - 2}">Less</text>'
        + "".join(
            f'<rect class="l{i}" x="{cells_x + i * PITCH:g}" y="{LEGEND_Y}" '
            f'width="{CELL}" height="{CELL}" rx="{CELL_RX}"/>'
            for i in range(5)
        )
        + f'<text x="{more_x:g}" y="{LEGEND_Y + CELL - 2}">More</text></g>'
    )

    total = (
        f'<text class="total" x="{GRID_X}" y="{LEGEND_Y + CELL - 0.5}">'
        f'<tspan class="num">{data["total"]}</tspan> contributions in the last year</text>'
    )

    heat_css = "".join(f".l{i}{{fill:var(--heat-{i})}}" for i in range(5))
    css = (
        root_css(variant, heat_tokens(variant))
        + f"svg{{font-family:{FONT_STACK}}}"
        + ".panel{fill:var(--surface);stroke:var(--border)}"
        + heat_css
        + f".labels{{font-size:{LABEL_SIZE}px;fill:var(--text-muted)}}"
        + ".muted{fill:var(--text-muted)}"
        + f".total{{font-size:{TOTAL_SIZE}px;fill:var(--text)}}"
        + ".num{fill:var(--accent);font-weight:700}"
        + ".cell{transform-box:fill-box;transform-origin:center;"
        + f"animation:pop {CELL_DURATION_MS}ms ease-out both;"
        + f"animation-delay:calc(var(--d) * {CELL_DELAY_MS}ms)}}"
        + "@keyframes pop{from{opacity:0;transform:scale(.5)}}"
        + REDUCED_MOTION_CSS
    )

    label = f'Contribution graph: {data["total"]} contributions in the last year'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{label}">\n'
        f"<title>Contribution graph</title>\n"
        f"<style>{css}</style>\n"
        f'<rect class="panel" x="0.5" y="0.5" width="{WIDTH - 1}" '
        f'height="{HEIGHT - 1}" rx="{RADIUS}"/>\n'
        f'<g class="labels">{months}{weekdays}</g>\n'
        + "\n".join(cells)
        + f"\n{legend}\n{total}\n</svg>\n"
    )


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    ASSETS.mkdir(exist_ok=True)
    for variant in ("dark", "light"):
        out = ASSETS / f"contrib-{variant}.svg"
        out.write_text(build_svg(data, variant), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
