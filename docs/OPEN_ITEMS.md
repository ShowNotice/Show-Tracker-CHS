# Open items

Current as of 2026-10-15. The older list from the pre-split notes is in
`docs/archive/project-notes-2026-10-15.md` ("Outstanding action items"); items from it
that may still apply but weren't re-checked are listed at the bottom.

## Owner actions

- **Require the "Validate shows.json" check before merging to `main`.** GitHub → repo
  Settings → Branches (or Rules) → add a rule for `main` that requires the
  "Validate shows.json / validate" status check. Until then the check reports a
  problem but can't physically block a merge; the routine is told not to merge
  unless it's green.
- **Allow `cdn.prod.website-files.com`** in the environment's network settings if you
  want the High Water Festival poster read automatically (it settles The Head and the
  Heart's day).

## Data questions

- **SNOB 2026-10-27:** Connor Sage and Matt Vajdic are both listed at 6:00 PM, on the
  venue's site too. Both rows are kept and flagged, and the 2026-10-22 run rechecks them.
- **Film screenings with a live orchestra:** in or out? "Ghostbusters in Concert"
  (Gaillard 10/25) is in the data; "Sonic Live in Concert" (Coliseum 10/28) was left out.
  Owner decision pending (see "Hybrid events" in pipeline/INSTRUCTIONS.md).
- **Flagged upcoming shows:** `scripts/validate_shows.py` lists them (50 on 2026-10-15),
  and the weekly PR now carries the list. Some are open questions, others just notes.
- **High Water Festival 2027:** the day split comes from press coverage, and The Head
  and the Heart's day is unconfirmed.
- **Refinery show times:** the venue's site doesn't publish them, and the backup source
  has had bad data, so many Refinery rows have no time.
- **Charleston Music Hall prices:** these come from Ticketmaster, which blocks our fetches.

## Engineering

- **Legacy star ids:** users who never revisit the site keep old-format ids in their
  account; the Worker translates them, so nothing breaks. `legacyShowId()` can be removed
  once no stored star still uses the old format.
- **No automated tests for the Worker** (`worker.js`); deploys are checked only for
  syntax, duplicate functions and cron/config agreement.
- **The digest's "already sent" guard isn't atomic** (Cloudflare KV has no atomic
  operations). Two guards make a duplicate unlikely, but not impossible.

## Carried over from the old notes, not re-checked

- Admin session expiry gives no advance warning (old item 9).
- The venue-suggestion rate limit is best-effort, not atomic (old item 10).
- The venue/festival pill directory at the page bottom "might be removed" (old item 13).
- Suggest a Venue is reachable only by scrolling since the 2026-09-12 nav redesign (old item 14).
- The cut-off "work on presentation for the [...]" request from 2026-09-12 was only
  partially addressed (old item 15).
