"""Render the contribution heatmap from data/contributions.json.

Writes assets/contrib-dark.svg and assets/contrib-light.svg: 53 weeks x 7
days of rounded cells and a Less -> More legend. The cells appear once along
the diagonal. The stats go in their own narrow card, assets/stats-dark.svg
and assets/stats-light.svg.
"""
import json
from datetime import date
from pathlib import Path

from theme import (CARD_W, FONT_STACK, RADIUS, REDUCED_MOTION_CSS, TOTAL_W,
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
STATS_SIZE = 16
STATS_PAD = 20
STATS_KEY_COLS = 9  # longest key ("Best day") plus one space
STATS_PITCH = 28
CELL_DELAY_MS = 30  # (52 + 6) * 30 + 200 = 1.94 s in total
CELL_DURATION_MS = 200


def plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def short_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d:%b} {d.day}"


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

    heat_css = "".join(f".l{i}{{fill:var(--heat-{i})}}" for i in range(5))
    css = (
        root_css(variant, heat_tokens(variant))
        + f"svg{{font-family:{FONT_STACK}}}"
        + ".panel{fill:var(--surface);stroke:var(--border)}"
        + heat_css
        + f".labels{{font-size:{LABEL_SIZE}px;fill:var(--text-muted)}}"
        + ".muted{fill:var(--text-muted)}"
        + ".cell{transform-box:fill-box;transform-origin:center;"
        + f"animation:pop {CELL_DURATION_MS}ms ease-out both;"
        + f"animation-delay:calc(var(--d) * {CELL_DELAY_MS}ms)}}"
        + "@keyframes pop{from{opacity:0;transform:scale(.5)}}"
        + REDUCED_MOTION_CSS
    )

    label = f'Contribution graph of the last 12 months: {data["total"]} contributions'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{label}">\n'
        f"<title>Contribution graph</title>\n"
        f"<style>{css}</style>\n"
        f'<rect class="panel" x="0.5" y="0.5" width="{WIDTH - 1}" '
        f'height="{HEIGHT - 1}" rx="{RADIUS}"/>\n'
        f'<g class="labels">{months}{weekdays}</g>\n'
        + "\n".join(cells)
        + f"\n{legend}\n</svg>\n"
    )


def stats_rows(data: dict) -> list[tuple[str, str]]:
    best = data["best_day"]
    return [
        ("Total", f'{data["total"]} in the last 12 months'),
        ("Streak", plural(data["current_streak"], "day")),
        ("Longest", plural(data["longest_streak"], "day")),
        ("Best day", f'{best["count"]} on {short_date(best["date"])}'),
    ]


def build_stats_svg(data: dict, variant: str) -> str:
    """Stats card: same look as the profile card, narrow enough for a phone."""
    rows = stats_rows(data)
    value_x = STATS_PAD + STATS_KEY_COLS * STATS_SIZE * 0.6
    height = 2 * STATS_PAD + (len(rows) - 1) * STATS_PITCH + 12
    lines = "".join(
        f'<text class="key" x="{STATS_PAD}" y="{STATS_PAD + 14 + i * STATS_PITCH}">{key}</text>'
        f'<text class="value" x="{value_x:g}" y="{STATS_PAD + 14 + i * STATS_PITCH}">{value}</text>'
        for i, (key, value) in enumerate(rows)
    )
    css = (
        root_css(variant)
        + f"svg{{font-family:{FONT_STACK};font-size:{STATS_SIZE}px}}"
        + ".panel{fill:var(--surface);stroke:var(--border)}"
        + ".key{fill:var(--accent);font-weight:700}.value{fill:var(--text)}"
    )
    label = "Contribution stats: " + ", ".join(f"{k} {v}" for k, v in rows)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{height}" '
        f'viewBox="0 0 {CARD_W} {height}" role="img" aria-label="{label}">\n'
        f"<title>Contribution stats</title>\n"
        f"<style>{css}</style>\n"
        f'<rect class="panel" x="0.5" y="0.5" width="{CARD_W - 1}" '
        f'height="{height - 1}" rx="{RADIUS}"/>\n{lines}\n</svg>\n'
    )


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    ASSETS.mkdir(exist_ok=True)
    for variant in ("dark", "light"):
        for name, svg in (("contrib", build_svg(data, variant)),
                          ("stats", build_stats_svg(data, variant))):
            out = ASSETS / f"{name}-{variant}.svg"
            out.write_text(svg, encoding="utf-8")
            print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
