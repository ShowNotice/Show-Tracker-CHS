#!/usr/bin/env python3
"""Validate shows.json, optionally against a base version (the file on main).

Usage:
  python3 scripts/validate_shows.py shows.json
  python3 scripts/validate_shows.py shows.json --base base-shows.json [--allow-review]

Errors (always fail): the file doesn't match docs/SHOWS_SCHEMA.md.
Review items (fail unless --allow-review): changes the weekly routine's rules say a
person should look at before merging — a big diff, mass removals for one venue, a
date moved more than 30 days, or a price outside $5–$200.
Exit code 0 = pass, 1 = errors, 2 = review items only.
"""
import argparse
import datetime
import json
import re
import sys
from collections import Counter, defaultdict

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME = re.compile(r"^(1[0-2]|[1-9]):[0-5]\d (AM|PM)$")
COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

SHOW_KEYS = {
    "id": str, "d": str, "e": str, "b": str, "v": str, "o": str, "s": str,
    "dr": str, "sh": str, "p": (int, float), "dop": (int, float), "u": str,
    "added": str, "flag": str, "soldOut": bool, "lowTix": bool,
}
VENUE_KEYS = {"name": str, "site": str, "type": str, "color": str, "address": str}
VENUE_TYPES = {"venue", "festival"}

BIG_DIFF = 40          # shows added or changed in one PR
MAX_REMOVALS = 5       # per venue, per PR
MAX_REMOVAL_SHARE = 0.25
MAX_DATE_SHIFT_DAYS = 30
PRICE_RANGE = (5, 200)  # 0 (free) is always fine


def key(s):
    return (s.get("v"), s.get("d"), s.get("b"))


def valid_date(v):
    if not isinstance(v, str) or not DATE.match(v):
        return False
    try:
        datetime.date.fromisoformat(v)
        return True
    except ValueError:
        return False


def check_file(raw):
    errors = []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, [f"not valid JSON: {e}"]

    canonical = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if raw != canonical:
        errors.append("formatting differs from the canonical format "
                      "(json.dumps(data, indent=2, ensure_ascii=False) + newline); "
                      "run: python3 scripts/format_shows.py")

    if set(data) != {"dataUpdatedAt", "venues", "shows"}:
        errors.append(f"top-level keys must be dataUpdatedAt, venues, shows (got {sorted(data)})")
        return data, errors
    if not valid_date(data["dataUpdatedAt"]):
        errors.append(f"dataUpdatedAt is not a YYYY-MM-DD date: {data['dataUpdatedAt']!r}")

    venues = data["venues"]
    for code, v in venues.items():
        where = f"venue {code}"
        for k, val in v.items():
            if k not in VENUE_KEYS:
                errors.append(f"{where}: unknown field {k!r}")
            elif not isinstance(val, VENUE_KEYS[k]):
                errors.append(f"{where}: {k} must be {VENUE_KEYS[k].__name__}")
        for k in ("name", "site", "type", "color"):
            if k not in v:
                errors.append(f"{where}: missing {k}")
        if v.get("type") not in VENUE_TYPES:
            errors.append(f"{where}: type must be one of {sorted(VENUE_TYPES)}")
        if "color" in v and not COLOR.match(v["color"]):
            errors.append(f"{where}: color must be #rrggbb")

    seen = Counter()
    ids = Counter()
    for i, s in enumerate(data["shows"]):
        where = f"show #{i} ({s.get('v')} {s.get('d')} {s.get('b')!r})"
        for k, val in s.items():
            if k not in SHOW_KEYS:
                errors.append(f"{where}: unknown field {k!r}")
            elif isinstance(val, bool) and SHOW_KEYS[k] is not bool:
                errors.append(f"{where}: {k} must not be true/false")
            elif not isinstance(val, SHOW_KEYS[k]):
                errors.append(f"{where}: {k} has the wrong type ({type(val).__name__})")
        for k in ("d", "b", "v"):
            if not s.get(k):
                errors.append(f"{where}: missing {k}")
        for k in ("d", "e", "added"):
            if k in s and not valid_date(s[k]):
                errors.append(f"{where}: {k} is not a YYYY-MM-DD date")
        if "e" in s and valid_date(s.get("d")) and valid_date(s["e"]) and s["e"] < s["d"]:
            errors.append(f"{where}: e (end date) is before d")
        if s.get("v") and s["v"] not in venues:
            errors.append(f"{where}: unknown venue code {s['v']!r}")
        for k in ("sh", "dr"):
            if k in s and not (isinstance(s[k], str) and TIME.match(s[k])):
                errors.append(f"{where}: {k} must look like '8:00 PM' (leave it out when unknown), got {s[k]!r}")
        for k in ("p", "dop"):
            if k in s and isinstance(s[k], (int, float)) and not isinstance(s[k], bool):
                if s[k] < 0:
                    errors.append(f"{where}: {k} is negative")
                if isinstance(s[k], float) and s[k] == int(s[k]):
                    errors.append(f"{where}: {k} should be a whole number ({int(s[k])}), not {s[k]}")
        if "u" in s and not re.match(r"^https?://\S+$", s["u"]):
            errors.append(f"{where}: u must be an http(s) URL (leave it out when there isn't one)")
        for k in ("b", "o", "s", "flag"):
            if k in s and isinstance(s[k], str) and s[k] != s[k].strip():
                errors.append(f"{where}: {k} has leading/trailing whitespace")
            if k in s and s[k] == "":
                errors.append(f"{where}: {k} is empty (leave it out instead)")
        if "id" in s:
            if not ID.match(s["id"]):
                errors.append(f"{where}: id must be lowercase letters, digits and hyphens")
            ids[s["id"]] += 1
        seen[key(s)] += 1

    for k, n in seen.items():
        if n > 1:
            errors.append(f"duplicate (venue, date, band) {k} appears {n} times")
    for k, n in ids.items():
        if n > 1:
            errors.append(f"duplicate id {k!r} appears {n} times")
    return data, errors


def review_items(new, base, today):
    """Changes that need a person's look before merging, per the routine's rules."""
    items = []
    old_by_key = {key(s): s for s in base["shows"]}
    new_by_key = {key(s): s for s in new["shows"]}
    old_by_id = {s["id"]: s for s in base["shows"] if "id" in s}

    added = [k for k in new_by_key if k not in old_by_key]
    removed = [k for k in old_by_key if k not in new_by_key]
    changed = [k for k in new_by_key if k in old_by_key and new_by_key[k] != old_by_key[k]]

    # A row whose id survived but whose venue/date/band changed is a change, not an
    # add + remove (only possible once every show has an id).
    moved = []
    for s in new["shows"]:
        o = old_by_id.get(s.get("id"))
        if o and key(o) != key(s):
            moved.append((o, s))
    moved_old = {key(o) for o, _ in moved}
    moved_new = {key(s) for _, s in moved}
    added = [k for k in added if k not in moved_new]
    removed = [k for k in removed if k not in moved_old]

    total = len(added) + len(changed) + len(moved)
    if total >= BIG_DIFF:
        items.append(f"{total} shows added or changed (review threshold is {BIG_DIFF})")

    upcoming_by_venue = Counter(s["v"] for s in base["shows"] if s["d"] >= today)
    removed_upcoming = defaultdict(list)
    for k in removed:
        if k[1] >= today:
            removed_upcoming[k[0]].append(k)
    for v, ks in removed_upcoming.items():
        share = len(ks) / max(1, upcoming_by_venue[v])
        if len(ks) > MAX_REMOVALS or share > MAX_REMOVAL_SHARE:
            items.append(f"{v}: {len(ks)} upcoming shows removed ({share:.0%} of its upcoming rows)")

    for o, s in moved:
        try:
            shift = abs((datetime.date.fromisoformat(s["d"]) - datetime.date.fromisoformat(o["d"])).days)
        except ValueError:
            continue
        if shift > MAX_DATE_SHIFT_DAYS:
            items.append(f"{s['v']} {s['b']!r}: date moved {shift} days ({o['d']} → {s['d']})")

    lo, hi = PRICE_RANGE
    for k in added + changed:
        s = new_by_key[k]
        for f in ("p", "dop"):
            val = s.get(f)
            if isinstance(val, (int, float)) and val != 0 and not (lo <= val <= hi):
                if old_by_key.get(k, {}).get(f) != val:
                    items.append(f"{k}: {f} = {val} is outside ${lo}–${hi}")
    return items, dict(added=len(added), removed=len(removed), changed=len(changed), moved=len(moved))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--base", help="the shows.json this change is compared against (e.g. main's)")
    ap.add_argument("--allow-review", action="store_true",
                    help="report review items without failing (a person has approved them)")
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    args = ap.parse_args()

    raw = open(args.path, encoding="utf-8").read()
    data, errors = check_file(raw)
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        print(f"\n{len(errors)} error(s).")
        return 1

    shows = data["shows"]
    print(f"OK: {len(shows)} shows across {len(data['venues'])} venues; format and schema checks passed.")

    if args.base:
        base_raw = open(args.base, encoding="utf-8").read()
        base = json.loads(base_raw)
        items, counts = review_items(data, base, args.today)
        print("Compared with base: " + ", ".join(f"{n} {k}" for k, n in counts.items()) + ".")
        for it in items:
            print(f"REVIEW: {it}")
        if items and not args.allow_review:
            print("\nNeeds a person's review before merging (add the 'owner-approved' label to override).")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
