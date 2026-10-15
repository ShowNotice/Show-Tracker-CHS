# Lowcountry Show Notice

Live-music listings for the Charleston, SC area: [chs.shownotice.com](https://chs.shownotice.com/).

- `index.html`, `admin.html` — the site and the owner's dashboard (static, served by GitHub Pages)
- `shows.json` — every show and venue ([format](docs/SHOWS_SCHEMA.md))
- `worker.js`, `wrangler.toml` — the Cloudflare Worker behind sign-in, My Shows and the weekly email
- `pipeline/INSTRUCTIONS.md` — how the weekly update routine finds and checks shows
- `scripts/` — `validate_shows.py` (the data check on PRs), `format_shows.py`, `prune_past.py`,
  `assign_ids.py`, and `check_worker.js` (the Worker check on PRs and before each deploy)
- `CLAUDE.md` — working rules for Claude Code sessions in this repo

Docs: [architecture](docs/ARCHITECTURE.md) · [data sources](docs/DATA_SOURCES.md) ·
[incidents](docs/INCIDENTS.md) · [open items](docs/OPEN_ITEMS.md)

Before committing a change to `shows.json`:

```sh
python3 scripts/format_shows.py
python3 scripts/prune_past.py
python3 scripts/assign_ids.py
git show origin/main:shows.json > /tmp/base.json
python3 scripts/validate_shows.py shows.json --base /tmp/base.json
python3 -m unittest discover -s tests
```
