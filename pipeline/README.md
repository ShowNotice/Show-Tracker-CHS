# pipeline/

Fetchers for the weekly update. Each one reads a venue's own listing the same way every
week and reports what changed. The routine still makes the judgment calls (pipeline/INSTRUCTIONS.md).

```sh
python3 -m pipeline.run                 # every source (a few minutes: polite delays)
python3 -m pipeline.run --venues PH,WJ  # just these venues
```

It writes, under `pipeline/out/` (not committed):

- `report.md` — per venue: new shows, date changes, field updates (times, prices, stage,
  status), shows in `shows.json` that the source no longer lists, and listings skipped as
  out of scope (with the reason)
- `comparison.json` — the same, as data
- `candidates.json` — everything each source returned

Nothing here edits `shows.json`.

## Sources

| Venue | Module | Reads |
|---|---|---|
| PH | `sources/pourhouse.py` | `/events/list/page/N/` until empty (robots-allowed; Crawl-delay 3) + event pages (JSON-LD start time, description doors/prices) |
| MF, CMH | `sources/tmcards.py` | the one-page calendar's event cards (Ticketmaster category classes) |
| NCC | `sources/ncc.py` | the list page + its "Load More" endpoint + detail pages |
| TR | `sources/tockify.py` | the tockify ICS feed |
| US, CHA, SNOB, NRB | `sources/lmc.py` | livemusiccharleston.com's events API |
| RA | `sources/squarespace.py` | the Squarespace schedule page |
| WJ | `sources/windjammer.py` | `/events/` (next 20) + `events-sitemap.xml` + event pages |
| FD, GC, C1S | `sources/misc.py` | each venue's own listing page |
| (cross-check) | `sources/squarespace.py` | Ear For Music's events page — never used for removals |

Not automated: REF (hand-built Wix page), CJF and RFP (festival sites; the High Water
lineup is an image), CHR (manual entry from Instagram).

## Rules the code follows

- Honest User-Agent, 1.5 s between requests to a host (3 s for Pour House), one retry for
  HTTP 429 (after 60 s or Retry-After) and for dropped connections.
- A CAPTCHA or bot challenge raises `Blocked`, and that venue is reported as failed — never
  retried or worked around.
- "complete: true" means the source lists every upcoming show it has, so a row it doesn't
  list (within its date range) is "no longer listed". Ear For Music is partial.

## Tests

`python3 -m unittest discover -s tests` — parsers run against trimmed copies of the real
pages in `tests/fixtures/` (saved 2026-10-15). When a venue redesigns its site, save a new
fixture, update the parser, and keep the test.
