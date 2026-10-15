#!/usr/bin/env python3
"""Give every show in shows.json that lacks one a permanent `id`, then rewrite the file
in canonical format. Existing ids are never changed.

An id looks like `ph-20261121-interstellar-echoes`: venue, date and name at the moment
the show was first added. It's only a readable label — if the show's date or name is
corrected later, the id stays as it was.
"""
import json
import re
import sys
import unicodedata


def slug(s, limit=40):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:limit].rstrip("-") or "show"


def new_id(show, taken):
    base = f"{show['v'].lower()}-{show['d'].replace('-', '')}-{slug(show['b'])}"
    cand, n = base, 2
    while cand in taken:
        cand, n = f"{base}-{n}", n + 1
    return cand


def assign(data):
    taken = {s["id"] for s in data["shows"] if "id" in s}
    added = 0
    for i, s in enumerate(data["shows"]):
        if "id" not in s:
            s_id = new_id(s, taken)
            taken.add(s_id)
            # Keep `id` first in each object so it's easy to spot in diffs.
            data["shows"][i] = {"id": s_id, **s}
            added += 1
    return added


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "shows.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    added = assign(data)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"assigned {added} new id(s)")


if __name__ == "__main__":
    main()
