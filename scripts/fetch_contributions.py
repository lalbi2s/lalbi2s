"""Fetch the public contribution calendar and write data/contributions.json.

Reads https://github.com/users/<user>/contributions (public HTML, no token).
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = "lalbi2s"
URL = f"https://github.com/users/{USER}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

COUNT_RE = re.compile(r"^(\d+)\s+contribution")


def fetch_days() -> list[dict]:
    resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tips = {
        tip.get("for"): tip.get_text(strip=True)
        for tip in soup.find_all("tool-tip")
    }

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        text = tips.get(cell.get("id"), "")
        match = COUNT_RE.match(text)
        days.append({
            "date": cell["data-date"],
            "count": int(match.group(1)) if match else 0,
            "level": int(cell.get("data-level", 0)),
        })

    days.sort(key=lambda d: d["date"])
    if not days:
        raise RuntimeError("No contribution cells found in the page")
    return days


def streaks(days: list[dict]) -> tuple[int, int]:
    """Return (current streak, longest streak) in days."""
    longest = run = 0
    prev = None
    for day in days:
        d = date.fromisoformat(day["date"])
        if day["count"] > 0:
            run = run + 1 if prev and d - prev == timedelta(days=1) else 1
            longest = max(longest, run)
            prev = d
        else:
            run = 0
            prev = None

    # Current streak: walk back from the last day. A zero on the last day
    # (today, still in progress) does not break it.
    current = 0
    for i, day in enumerate(reversed(days)):
        if day["count"] > 0:
            current += 1
        elif i == 0:
            continue
        else:
            break
    return current, longest


def main() -> None:
    days = fetch_days()
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])

    data = {
        "user": USER,
        "from": days[0]["date"],
        "to": days[-1]["date"],
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    print(f"{len(days)} days, {data['total']} contributions, "
          f"streak {current} (longest {longest}), best {best['count']} on {best['date']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"fetch_contributions failed: {exc}")
