"""Fetch every source and write pipeline/out/report.md and pipeline/out/candidates.json.

  python3 -m pipeline.run                 # all sources
  python3 -m pipeline.run --venues PH,WJ  # just these
  python3 -m pipeline.run --all-details   # fetch event pages for every show, not just new ones

Exit code 0 even when some sources fail; failures are listed in the report.
"""
import argparse
import datetime
import json
import os
import sys
import traceback

from .compare import compare, report_markdown, same_act
from .net import Blocked, FetchError, Http
from .sources import CROSS_CHECKS, SOURCES


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--shows", default="shows.json")
    ap.add_argument("--out", default="pipeline/out")
    ap.add_argument("--venues", help="comma-separated venue codes (default: all)")
    ap.add_argument("--all-details", action="store_true")
    args = ap.parse_args(argv)

    today = datetime.date.today().isoformat()
    shows = json.load(open(args.shows, encoding="utf-8"))["shows"]
    wanted = set(args.venues.upper().split(",")) if args.venues else None
    http = Http()
    results, candidates = {}, {}

    def wants_details_for(venue):
        rows = [s for s in shows if s["v"] == venue]

        def wants(e):
            if args.all_details:
                return True
            row = next((s for s in rows if s["d"] == e.get("date") and same_act(s["b"], e["title"])), None)
            return row is None or "sh" not in row or "p" not in row
        return wants

    jobs = [(v, f, d, False) for v, (f, d) in SOURCES.items() if not wanted or v in wanted]
    jobs += [(k, f, d, True) for k, (f, d) in CROSS_CHECKS.items() if not wanted]
    for name, fetch, desc, is_cross in jobs:
        print(f"fetching {name} ({desc}) …", file=sys.stderr, flush=True)
        try:
            res = fetch(http, wants_details_for(name) if not is_cross else (lambda e: False))
        except (Blocked, FetchError) as e:
            results[name] = {"source": desc, "error": str(e)}
            continue
        except Exception as e:  # a parser bug shouldn't stop the other venues
            results[name] = {"source": desc, "error": f"{type(e).__name__}: {e}"}
            traceback.print_exc()
            continue
        events = res["events"]
        candidates[name] = events
        if is_cross:
            by_venue = {}
            for e in events:
                by_venue.setdefault(e["venue"], []).append(e)
            for v, evs in by_venue.items():
                results[f"{name}:{v}"] = {"source": desc, "complete": False, "count": len([e for e in evs if e["date"] >= today]),
                                          "comparison": compare(shows, v, evs, False, today)}
        else:
            results[name] = {"source": desc, "complete": res["complete"],
                             "count": len([e for e in events if e.get("date") and e["date"] >= today]),
                             "comparison": compare(shows, name, events, res["complete"], today)}

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "candidates.json"), "w", encoding="utf-8") as f:
        json.dump({"generated": today, "events": candidates}, f, indent=1, ensure_ascii=False)
    with open(os.path.join(args.out, "comparison.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, ensure_ascii=False, default=str)
    with open(os.path.join(args.out, "report.md"), "w", encoding="utf-8") as f:
        f.write(report_markdown(results, today))
    failed = [k for k, r in results.items() if r.get("error")]
    print(f"{len(results)} sources, {len(failed)} failed{': ' + ', '.join(failed) if failed else ''}; "
          f"{http.requests} requests. Report: {os.path.join(args.out, 'report.md')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
