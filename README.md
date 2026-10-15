# Lowcountry Show Notice

Live-music listings for the Charleston, SC area: [chs.shownotice.com](https://chs.shownotice.com/).

- `index.html`, `admin.html` — the site and the owner's dashboard (static, served by GitHub Pages)
- `shows.json` — every show and venue ([format](docs/SHOWS_SCHEMA.md))
- `worker.js`, `wrangler.toml` — the Cloudflare Worker behind sign-in, My Shows and the weekly email
- `pipeline/INSTRUCTIONS.md` — how the weekly update routine finds and checks shows
- `scripts/` — `validate_shows.py` (run on every PR) and `format_shows.py`

Docs: [architecture](docs/ARCHITECTURE.md) · [data sources](docs/DATA_SOURCES.md) ·
[incidents](docs/INCIDENTS.md) · [open items](docs/OPEN_ITEMS.md)

Before committing a change to `shows.json`:

```sh
python3 scripts/format_shows.py
git show origin/main:shows.json > /tmp/base.json
python3 scripts/validate_shows.py shows.json --base /tmp/base.json
python3 -m unittest discover -s tests
```
