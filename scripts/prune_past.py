#!/usr/bin/env python3
"""Remove shows that ended more than 5 days ago (owner decision, 2026-10-15), then
rewrite shows.json in canonical format.

The site and the digest already hide past shows; this keeps the file from growing
forever. "Today" is Charleston's date (America/New_York), and a multi-day show counts
from its end date `e`.
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from validate_shows import past_cutoff  # noqa: E402


def charleston_today():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:  # no tz database: fall back to UTC, at most a day off
        return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def prune(data, today):
    cutoff = past_cutoff(today)
    keep = [s for s in data["shows"] if (s.get("e") or s["d"]) >= cutoff]
    removed = len(data["shows"]) - len(keep)
    data["shows"] = keep
    return removed


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "shows.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    today = charleston_today()
    removed = prune(data, today)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"removed {removed} show(s) that ended before {past_cutoff(today)}")


if __name__ == "__main__":
    main()
