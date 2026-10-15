# shows.json format

`shows.json` is the site's whole catalog. The site (`index.html`) and the weekly digest
(`worker.js`) both read it, and the weekly routine writes it. `scripts/validate_shows.py`
enforces everything on this page, and runs on every pull request that touches the file.

## File layout

```json
{
  "dataUpdatedAt": "2026-10-15",
  "venues": { "PH": { … }, … },
  "shows": [ { … }, … ]
}
```

The file is always written in one canonical format: `json.dumps(data, indent=2,
ensure_ascii=False)` plus a trailing newline. Use `python3 scripts/format_shows.py`
after any hand edit. Keeping one format means a PR diff shows only real changes.

## Venues

Keyed by a short uppercase code (`PH`, `MF`, `CHR`, …).

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | Display name |
| `site` | yes | Venue's own website (fallback link when a show has no `u`) |
| `type` | yes | `venue` or `festival` |
| `color` | yes | Accent color, `#rrggbb` |
| `address` | no | Street address |

## Shows

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Permanent identifier; never changes, even if the date or name is corrected. See below. |
| `d` | yes | Date, `YYYY-MM-DD` (first day for a multi-day event) |
| `e` | no | End date for a multi-day event, `YYYY-MM-DD` |
| `b` | yes | Headliner / event name |
| `v` | yes | Venue code (must exist in `venues`) |
| `o` | no | Openers, comma-separated, or a short note (e.g. a festival's lineup) |
| `s` | no | Stage or room (`Main Stage`, `Deck Stage`, …) |
| `dr` | no | Doors time, exactly like `7:00 PM` |
| `sh` | no | Show time, exactly like `8:00 PM` |
| `p` | no | Advance price in dollars (a number; `0` = free) |
| `dop` | no | Day-of-show price in dollars |
| `u` | no | Ticket or event link, `http(s)://…` |
| `added` | no | Date the show was first added, `YYYY-MM-DD` (drives "Added This Week") |
| `flag` | no | Internal note for an open question or judgment call; not shown on the site |
| `soldOut` | no | `true` when sold out |
| `lowTix` | no | `true` when the venue says tickets are low |
| `confirmed` | no | Date the owner entered or confirmed this show, `YYYY-MM-DD`. The routine won't remove or edit it because a source disagrees; removing it needs review. |

### Unknown values: leave the field out

When a time, price, link or note isn't known, **omit the field**. Don't write `"—"`,
`"TBA"`, `"see ticket link"`, `null` or an empty string. The site already shows
"Time TBD" for a missing time and a "Tickets" link for a missing price, and the email
does the same, so leaving a field out is the single way to say "unknown." Put any
explanation in `flag`.

Prices are whole numbers unless the venue really charges cents (e.g. `29.5`). Write
`10`, not `10.0`.

### Uniqueness

No two shows may share the same (`v`, `d`, `b`). Every `id` must be unique. No show may match an entry in `pipeline/do_not_add.json` (the owner's "not happening" list).

### Stable IDs

Users' starred shows (My Shows) and the digest's star links refer to shows by `id`.
An `id` is assigned once, when the show is first added (`python3 scripts/assign_ids.py`
fills in any missing ones), and is never edited afterwards — including when the date,
venue or name is corrected. It looks like `ph-20261121-interstellar-echoes`. The date
and name in it are just a readable label from the moment it was created, not data.

## Review rules

The checker compares a PR's file with `main` and flags these for a person to look at.
The PR's check fails until someone adds the `owner-approved` label.

- 40 or more shows added or changed
- More than 5 upcoming shows removed for one venue, or more than 25% of its upcoming shows
- A show's date moved by more than 30 days
- An owner-confirmed show removed
- A new or changed price outside $5–$200 (free is fine)
