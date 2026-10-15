#!/usr/bin/env python3
"""Rewrite shows.json in its canonical format (2-space JSON, UTF-8, trailing newline)."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "shows.json"
with open(path, encoding="utf-8") as f:
    data = json.load(f)
with open(path, "w", encoding="utf-8") as f:
    f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
