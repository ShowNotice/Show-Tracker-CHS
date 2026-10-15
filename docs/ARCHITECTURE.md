# Architecture — Lowcountry Show Notice

How the system fits together. Current as of 2026-10-15.

- **Show data format:** `docs/SHOWS_SCHEMA.md`
- **Weekly update rules:** `pipeline/INSTRUCTIONS.md`
- **Source research background:** `docs/DATA_SOURCES.md`
- **Incident history:** `docs/INCIDENTS.md`
- **Open items:** `docs/OPEN_ITEMS.md`

The full pre-split notes file is archived unchanged at `docs/archive/project-notes-2026-10-15.md`.

## Weekly data pipeline (summary)

1. A scheduled Claude Code routine ("Show Notice CHS Weekly Update", Thursdays) follows `pipeline/INSTRUCTIONS.md`.
2. It fetches each venue's source, updates `shows.json` on a `claude/…` branch, and opens a PR.
3. The "Validate shows.json" GitHub check (`.github/workflows/validate-shows.yml`, running `scripts/validate_shows.py`) checks format, duplicates and venue codes, and applies the review rules against `main`.
4. The routine merges only when the check is green and no review rule fired. Otherwise a separate weekly check-in ("Review Show Notice routine PRs", Thursdays 13:00 UTC) walks the owner through the open PR. The owner approves a flagged change by adding the `owner-approved` label.
5. GitHub Pages serves the merged `shows.json` directly; there's no build step.

## What this is

A live-music show tracker for the Charleston, SC area, branded **Show Notice**.
- **Site:** [chs.shownotice.com](https://chs.shownotice.com/) — static frontend, served via GitHub Pages.
- **API:** [api.chs.shownotice.com](https://api.chs.shownotice.com/) — Cloudflare Worker backend.
- **Repo:** [github.com/ShowNotice/Show-Tracker-CHS](https://github.com/ShowNotice/Show-Tracker-CHS).
- **Admin panel:** `admin.html`, served from the same site, owner-only (Turnstile + magic-link + `OWNER_EMAIL` check).

Static frontend + a Cloudflare Worker backend for accounts, subscriptions, a weekly digest email, and (as of 2026-09-11) a full admin analytics dashboard. Show data is refreshed by a separate automated research routine that pushes `shows.json` updates via PR.

**Former identity, retired 2026-09-11:** this project was previously "GigAlert CHS," served from `gigalertchs.com` (repo `GigAlertCHS/Show-Tracker`) and the Worker's `*.workers.dev` fallback URL. See "Domain migration" below — `gigalertchs.com` now 301-redirects to `chs.shownotice.com` (confirmed working on both desktop and mobile) rather than being decommissioned outright, so old links/bookmarks keep working.

## Files

| File | Role |
|---|---|
| `index.html` | The public site. Static HTML/CSS/vanilla JS, no build step. Fetches `shows.json` client-side and renders it. Served via GitHub Pages (custom domain via `CNAME`). |
| `worker.js` | Cloudflare Worker backend: passwordless sign-in, My Shows/Favorite Artists storage, digest email, admin stats (incl. Cloudflare zone analytics), venue suggestions. Deployed via `.github/workflows/deploy-worker.yml`. |
| `admin.html` | Owner-only stats dashboard. Talks to the Worker's `/api/admin/stats`; calls it at `api.chs.shownotice.com` directly (not the `*.workers.dev` fallback — see Domain migration). Also static, no build step. |
| `shows.json` | The show data itself: `{ dataUpdatedAt, venues, shows }`. Updated by the weekly automated research routine, not hand-edited. |
| `wrangler.toml` | Worker deploy config: KV binding, Secrets Store bindings, cron trigger, custom domain route, observability, plain vars. Source of truth for `wrangler deploy` — see the warning comment at the top of the file about what gets silently stripped if this file is wrong/missing. |
| `scripts/validate_shows.py` | Checks `shows.json` against `docs/SHOWS_SCHEMA.md` and the review rules (added 2026-10-15). |
| `scripts/format_shows.py` | Rewrites `shows.json` in its canonical format. |
| `.github/workflows/validate-shows.yml` | Runs the unit tests and the shows.json check on every PR that touches the data or tools. |
| `pipeline/INSTRUCTIONS.md` | The weekly routine's instructions (moved into the repo 2026-10-15). |
| `tests/` | Unit tests (`python3 -m unittest discover -s tests`). |
| `docs/` | This file, the schema, data-source research, incidents, open items, and the archived old notes. |
| `CNAME` | GitHub Pages custom domain — now `chs.shownotice.com` (moved 2026-09-11, was `gigalertchs.com`). |
| `.github/workflows/deploy-worker.yml` | Auto-deploys `worker.js` to Cloudflare on every push to `main` that touches `worker.js` or `wrangler.toml`. Runs `node --check` plus a duplicate-top-level-function-declaration scan as a sanity check before deploying. No test suite, no required review — see "Deploy process" below. |

`index.html`/`admin.html`/`shows.json` need no separate deploy step — GitHub Pages serves them straight from the repo.

## Data model

### `shows.json`

```
{
  "dataUpdatedAt": "YYYY-MM-DD",
  "venues": { "<CODE>": { "name", "site", "type": "venue"|"festival", "color", "address"? } },
  "shows": [ { "d", "b", "v", "sh", "dr", "o"?, "s"?, "p"?, "dop"?, "u"?, "e"?, "added"?, "flag"?, "soldOut"?, "lowTix"? } ]
}
```

Show fields:
- `d` — date (`YYYY-MM-DD`). `e` — optional end date for multi-day events.
- `b` — band/event name. `o` — opener(s), comma-separated if a list. A single opener now renders inline on one line ("Band w/ Opener"), wrapping naturally — this replaced an earlier format where the opener sat on its own line below the band name. Multiple comma-separated openers still render as separate pill chips below the band name (that part is unchanged).
- `v` — venue code, must be a key in `venues`. Known codes as of this writing: `PH` (Pour House), `REF` (The Refinery), `CMH` (Music Hall), `WJ` (Windjammer), `C1S` (Credit One Stadium), `NCC` (N. Charleston Coliseum), `MF` (Music Farm), `FD` (Firefly Distillery), `GC` (Gaillard Center), `NRB` (New Realm Brewing), `TR` (Tin Roof), `RA` (The Royal American), plus festival/park entries `CJF` (Charleston Jazz Festival) and `RFP` (Riverfront Park — hosts both Riverfront Revival and Low Tide Festival; neither gets its own venue code, since both are festivals held at this venue rather than independent venues). `CHR` (Charleston Harbor Resort & Marina, added 2026-10-13 — manual entry only, see "Charleston Harbor Resort & Marina" below). A standalone `RFR` (Riverfront Revival) venue code existed briefly but was removed 2026-09-10 — Riverfront Revival isn't its own venue, it's an event at Riverfront Park.
- `sh`/`dr` — show/doors time, exactly like `"7:00 PM"`; left out when unknown (normalized 2026-10-15 — see `docs/SHOWS_SCHEMA.md`, which is the authoritative field reference).
- `s` — stage name, when a venue has multiple stages.
- `p` — advance price (number, `0` = free). Always the advance price when a show has one — stored and shown by default up through the day before the show. Many venues list both an advance and day-of price (e.g. "$25 advance / $30 day of show," or "$13 – $15") — always store the lower/advance figure in `p`, never the day-of figure or an average.
  - **Tiered/multi-day festival pricing fallback (decided 2026-09-10):** some festivals (multi-day passes, GA/GA+/VIP/Stage Access tiers, prices that visibly increase over time via presale windows) don't reduce to one honest "advance price" number — picking any single tier would misrepresent the others. When pricing is this fragmented, omit `p` entirely and rely on `u` (ticket link) alone rather than forcing a single figure. Reserve this for genuine multi-tier/multi-day spreads, not as a shortcut when a single advance price is knowable but just requires an extra fetch.
- `dop` — optional day-of price, only used once the show's actual date has arrived (compares the visitor's local date to `d`). Both the site (`priceOrTicketsHTML()` in `index.html`) and the digest email (`buildDigestEmailHTML` in `worker.js`) apply this rule identically — if one changes, the other needs the same change.
- `u` — ticket URL. Validated as `http(s)://` before ever being put in an `href`, both client-side (`safeUrl()` in `index.html`) and server-side (`worker.js`), since `shows.json` is written by an automated scraping agent and its URLs aren't implicitly trusted.
- `added` — date this show was first added to the data. Drives the site's "Added This Week" section and the digest email's equivalent (cutoff: added within the last 7–10 days depending on which surface).
- `flag` — a one-line human-readable note for genuinely ambiguous cases (e.g. hybrid non-music/music events — see exclusion rules below). Shown as-is in the data, but **not rendered anywhere on the live site** (confirmed by checking the code — the CSS class exists but nothing ever creates an element with it); it's an internal/editorial note only.
- `soldOut` / `lowTix` — booleans, independent of `flag`, and the only fields that actually drive visible ticket-status UI. `soldOut: true` is set when the venue's own page explicitly shows "Sold Out" — the site shows a muted-red "Sold Out" label (`--sold-out: #c96a6a`) in place of the price/Tickets link, not a link, since there's nothing to click through to. `lowTix: true` is set when the venue shows a low-inventory status (e.g. Music Farm's "LOW TIX") — tickets are still purchasable, so the site shows a gold "Low Tix" label that's still a working link. Both must be respected everywhere a price/ticket link renders — `index.html`'s `priceOrTicketsHTML()` and `worker.js`'s `buildDigestEmailHTML`/`showRowHtml` price block are the two implementations and must stay in sync (this was out of sync until the 2026-09-10 fix — see Incident history).
- `"g": "classical"` should not be used at all going forward (classical/orchestral is excluded entirely — see exclusion rules). As of the last full audit, zero shows in the dataset carry this tag. An earlier design (hide-by-default with a per-venue reveal toggle) was removed from the code entirely, not just left dormant.

`showId(s)` — since 2026-10-15 every show has a permanent `id` (see `docs/SHOWS_SCHEMA.md`), and `showId(s)` returns it in both `index.html` and `worker.js`. Stars saved earlier used the legacy `[v, d, b].join('|').toLowerCase().replace(/\s+/g, '_')` form: the site translates them in a visitor's browser and account on their next visit (`migrateLegacyIds()`), and the Worker translates any still stored (`normalizeShowIds()`) for the digest and admin stats. `legacyShowId()` must stay identical in both files until every stored star has been migrated.

### Cloudflare KV (`SHOW_TRACKER_KV`)

| Key pattern | Value | Notes |
|---|---|---|
| `token:<uuid>` | `{ email }` | Magic-link sign-in token. 15 min TTL, one-time use (deleted on verify). |
| `session:<uuid>` | `{ email }` | Session token, sent as `Authorization: Bearer`. 30-day TTL. |
| `subscriber:<email>` | `{ subscribedAt, unsubscribeToken }` | Presence = actively subscribed to the digest. |
| `unsubtoken:<uuid>` | `<email>` (plain string) | Reverse lookup from a subscriber's unsubscribe token to their email. Reused as the auth credential for `/api/star-show` too — same trust level either way, since whoever holds it can already unsubscribe the person. |
| `unsubscribed:<email>` | `{ unsubscribedAt }` | Permanent marker so a later sign-in doesn't silently re-subscribe someone who opted out. No TTL. |
| `user:<email>` | `{ myShows: [showId...], favorites: [artistName...], createdAt?, myShowsAddedAt?, favoritesAddedAt? }` | Both arrays length/count-capped (`MAX_SHOW_ID_LENGTH` = 150, favorites item cap 100 chars, both arrays capped to `MAX_MY_SHOWS` = 300) since this is written from unauthenticated-by-anything-but-a-token paths (`/api/star-show`) as well as the authenticated `/api/user/data`. The three `*At` timestamp fields were added 2026-09-11 to drive the admin panel's week/month/year/all rolling-window stats; they self-heal via a one-time backfill on first read for any record created before this change, rather than needing a migration script — `myShows`/`favorites` themselves stay plain string arrays throughout (a deliberate side-channel design, not a schema change) so none of the extensive existing client-side code touching those two fields needed to change. |
| `suggestion:<uuid>` | `{ submitterEmail, venueName, notes, submittedAt }` | From "Suggest a Venue." |
| `contact:<uuid>` | `{ email, message, submittedAt }` | From the Contact Us form (added 2026-09-12). `email` is optional — a visitor can submit with none. |
| `ratelimit:<email>` | `'1'`, 60s TTL | One sign-in link request per email per minute. |
| `ratelimit-ip:<ip>` | request count string, 1hr TTL | Best-effort per-IP cap (10/hr) on sign-in requests — not atomic; KV has no atomic increment, so a burst of simultaneous requests can overshoot the cap. A hard guarantee would need Durable Objects. Treated as a best-effort volume brake, with the per-email limit and Turnstile as the tighter controls. |
| `suggest-ratelimit:<email>` | `'1'`, 60s TTL | One venue suggestion per person per minute. |
| `contact-ratelimit:<ip>` | request count string, TTL matches the other rate limits | Per-IP cap on Contact Us submissions (added 2026-09-12) — same best-effort/non-atomic caveat as `ratelimit-ip` above; Turnstile is the tighter control in front of it. |

`listAllKeys(env, prefix)` pages through `KV.list()`'s cursor — added 2026-09-10 after noticing every list-all call site was using a single unpaginated `list()`, which silently truncates past 1000 keys. Use it for any new "every key with this prefix" need instead of calling `KV.list()` directly.

## Worker API routes

| Route | Method | Auth |
|---|---|---|
| `/api/auth/request-link` | POST | none (rate-limited + Turnstile if configured) |
| `/api/auth/verify` | GET | magic-link token (query) |
| `/api/user/data` | GET/POST | session Bearer token |
| `/api/unsubscribe` | GET | unsubscribe token (query) + `confirm=1` |
| `/api/star-show` | GET | unsubscribe token (query, reused) + `confirm=1` |
| `/api/subscribe` | POST | session Bearer token |
| `/api/digest-preview` | GET | session Bearer token (preview your own digest) |
| `/api/test-send-digest-now` | GET | session Bearer token, owner-only |
| `/api/report-conflicts` | POST | `COWORK_API_SECRET` shared secret (Bearer), timing-safe compare |
| `/api/suggest-venue` | POST | session Bearer token |
| `/api/contact` | POST | none (rate-limited + Turnstile) — added 2026-09-12 |
| `/api/admin/stats` | GET | session Bearer token, owner-only |

`/api/unsubscribe` and `/api/star-show` both require an explicit `confirm=1` click past a summary page rather than acting on a bare GET — added so a mail-security scanner or link-prefetcher auto-fetching a link straight out of the email body can't silently unsubscribe someone or star a show on their behalf.

## Secrets & environment variables

Set in Cloudflare (dashboard or Secrets Store), **never** committed:
- `RESEND_API_KEY` — Resend email API key. Until set, `/api/auth/request-link` runs in "test mode" and returns the magic link directly in the JSON response instead of emailing it.
- `TURNSTILE_SECRET_KEY` — Cloudflare Turnstile bot-protection secret. **Fails open** (skips verification) if absent — deliberate, so frontend/backend can be deployed slightly out of order without locking out sign-in, but means bot protection is silently off until this is actually set.
- `COWORK_API_SECRET` — shared secret for the automated research routine's `/api/report-conflicts` calls.
- `RESEND_WEBHOOK_SECRET` (added 2026-09-11) — verifies Resend's delivery/open/click webhook callbacks using the Svix signing scheme (HMAC-SHA256 over `{svix-id}.{svix-timestamp}.{body}`, compared timing-safe). Feeds the admin panel's digest-engagement stats.
- `CLOUDFLARE_ANALYTICS_TOKEN` (added 2026-09-11) — a Cloudflare API token scoped to Analytics/GraphQL read access, used by `fetchCloudflareZoneAnalytics()` to pull traffic/threat/cache/country data from Cloudflare's GraphQL Analytics API (`httpRequests1dGroups`) into the admin panel. Needs Secrets Store permissions specifically, not just an Analytics-read template — see "Deploy process" below for the same caveat on the CI deploy token.

Plain vars (in `wrangler.toml`, safe to commit): `RESEND_FROM_ADDRESS`, `SITE_URL`, `WORKER_BASE_URL`, `OWNER_EMAIL`, `CLOUDFLARE_ZONE_ID` (added 2026-09-11 — not secret, just identifies which zone `fetchCloudflareZoneAnalytics` queries).

**Secrets Store secret names do not match their binding names** (cost real debugging time): bindings are uppercase (what `worker.js` reads off `env`), but the actual secret names in the store are `RESEND_API_KEY` (uppercase), `turnstile-secret-key` (lowercase, hyphenated), `cowork-api-secret` (lowercase, hyphenated), `resend-webhook-secret` (lowercase, hyphenated), `cloudflare-analytics-token` (lowercase, hyphenated). Store ID is `30c772729ee04e95b2d1ee57b4be87fd`. KV namespace is `SHOW_TRACKER_KV`, id `d6ce7eeb579342ddaab94ae9560ddfc2`.

`wrangler.toml` is the deploy source of truth — anything a deploy needs that isn't declared there gets silently dropped. This has happened twice: once stripping the KV binding (broke sign-in entirely) and once stripping the Secrets Store bindings (broke magic-link email and silently disabled Turnstile). Read the comments at the top of that file before touching it.

## Deploy process

`.github/workflows/deploy-worker.yml` runs on every push to `main` touching `worker.js` or `wrangler.toml` (or manual `workflow_dispatch`). Steps: sanity-check → `wrangler deploy --dry-run` → `wrangler deploy`. **No required review, no test suite** — a push to `main` that touches those files goes live automatically. No branch-protection/required-review rule exists on `main` as of this writing (a GitHub repo setting, not fixable via a commit) — worth turning on if that's not already in place.

The sanity-check step (added 2026-09-10) runs `node --check worker.js` plus a script that fails the build if any top-level `function`/`async function` name is declared more than once — added specifically because `wrangler deploy --dry-run` did **not** catch the corruption incident below (the duplicated file was still syntactically valid, just semantically broken).

Other deploy notes:
- `worker.js` is tracked in git and deploys automatically via this workflow — manual pasting into Cloudflare's Edit Code UI still works as a fallback but is no longer required.
- `cloudflare/wrangler-action` swallows Wrangler's own output and reports only "exit code 1," which made two separate failures impossible to diagnose. The workflow now calls `npx wrangler@4 deploy` directly as a plain `run:` step, plus a `--dry-run` validation step first — keep it that way, since the visible error output is what finally solved those failures.
- The `CLOUDFLARE_API_TOKEN` used by GitHub Actions needs Secrets Store permissions, not just Workers Scripts. A token made from the "Edit Cloudflare Workers" template alone fails with error 10021 on any deploy touching Secrets Store bindings.
- The Cowork automation path (for the weekly data-update routine) was abandoned — its GitHub connector fails OAuth against the official GitHub MCP server. Weekly data updates instead run through a **Claude Code Routine**: cloud-hosted, scheduled, pushes to a `claude/`-prefixed branch and opens a PR for review rather than committing straight to main.
- `test_worker.js` (a 30-test suite referenced in older notes) is not in the repo and has never been located. **No automated test suite exists** — every deploy this session was validated manually (`node --check`, the duplicate-declaration scan, and the `code-review` skill) rather than by a test run. Worth building a small smoke-test suite for the Worker's request handlers eventually; flagged as an open suggestion, not yet actioned.
- **Workers Logs + Traces observability** (added 2026-09-11, `[observability.logs]`/`[observability.traces]` in `wrangler.toml`, `head_sampling_rate = 1`, `persist = true` on both) is declared in config for the same reason every other binding is — turning it on in the dashboard alone wouldn't survive the next deploy. Optional; nothing in the Worker depends on it to function.


## Security posture (audited and fixed)

- **All rendered data is escaped.** `index.html` and `admin.html` both have an `escapeHtml()` helper applied to every interpolated value — this matters more than it used to, since `shows.json` is now written by an automated agent scraping venue websites, making a malformed venue listing a plausible injection path, not a hypothetical one.
- **URLs are validated before reaching an `href`.** `safeUrl()` in `index.html` (and an equivalent inline check in `worker.js`'s digest email builder) rejects anything that isn't `http://` or `https://`, blocking `javascript:`/`data:` URLs.
- **Input validation is applied on both sides.** Favorite artist names, venue suggestions, and (added 2026-09-12) Contact Us messages reject angle brackets and enforce length limits in both the browser and the Worker. Server-side is the real gate; client-side just prevents the value from rendering locally before any round-trip.
- **Contact Us is the one fully public, unauthenticated write endpoint added since the initial audits** (`/api/contact` — no session required, unlike venue suggestions) — gated the same way sign-in requests are: Turnstile + a per-IP rate limit (see KV table above), plus the same length/angle-bracket validation as everything else. No email address is exposed anywhere in the page for a bot to scrape in the first place, which was the actual motivation for adding this form.
- **Admin authorization is server-enforced** (`handleAdminStats` checks the session email against `OWNER_EMAIL`), not merely hidden in the UI — correct and should stay that way, since that endpoint exposes other users' email addresses.
- The per-IP sign-in rate limit's non-atomic KV race (see KV table above) is a known, accepted limitation, not an oversight.

## Domain migration (2026-09-11): gigalertchs.com → CHS.ShowNotice.com

The project rebranded from "GigAlert CHS" to **Show Notice** and moved off `gigalertchs.com` onto `chs.shownotice.com`, following a pre-written migration plan. Summary of what changed:

- **GitHub Pages custom domain**: `CNAME` updated from `gigalertchs.com` to `chs.shownotice.com` (PR #27).
- **Site/Worker config**: `SITE_URL`, `WORKER_BASE_URL`, and every hardcoded reference in `index.html`/`admin.html` repointed at the new domain (PR #28).
- **Worker custom domain route**: `api.chs.shownotice.com` wired via `[[routes]]` in `wrangler.toml` (`custom_domain = true`, `zone_name = "shownotice.com"`) so the API isn't dependent on the `*.workers.dev` fallback.
- **Old domain kept alive as a redirect, not decommissioned**: `gigalertchs.com` now 301-redirects to the new domain via a Cloudflare Redirect Rule — confirmed working via a direct `curl -I` test (301 status, correct `Location` header) and confirmed by the user on both desktop and mobile browsers, so existing bookmarks/links/search results keep working.
- **Email sender identity**: `RESEND_FROM_ADDRESS` updated to `Lowcountry Show Notice <shows@shownotice.com>` (PR #31); owner contact address is `admin@ShowNotice.com`.
- **Stale infrastructure removed**: the old `show-tracker-api.gigalertchs.workers.dev` Worker route/domain entry was confirmed no longer needed (everything now goes through `api.chs.shownotice.com`) and removed from the Worker's Domains panel in the Cloudflare dashboard — a dashboard-side cleanup step, not a `wrangler.toml` change.
- **Cloudflare Web Analytics and Zone-level features** (bot detection, WAF, etc.) enabled on the new `shownotice.com` zone as part of the same session — see "Admin analytics panel & Cloudflare integration" below for what actually got wired into the app itself.

If a future session finds any remaining `gigalertchs` references (in code comments, email templates, or elsewhere), that's leftover from the old identity and should be updated to match — the redirect exists so *external* links keep working, not so the codebase can keep referencing the old name internally.

## Admin analytics panel & Cloudflare integration (2026-09-11)

`admin.html` was substantially built out from a bare stats page into a full analytics dashboard, driven by the user's "what else of use can we track without getting too esoteric or nosy" → "add them all" → "add week/month/year/all columns" progression. Everything below is server-computed in `handleAdminStats` (`worker.js`) and rendered in `admin.html`; **no client-side tracking/cookies were added** — all app-level numbers are derived from existing KV records (subscribers, users, suggestions) plus the timestamp-backfill fields described in the KV table above, and the Cloudflare numbers come from Cloudflare's own edge/zone data, not client-side beacons.

**App-level stats, each broken out by rolling week/month/year/all-time windows** (a `windowCounts`/`windowGroupedCounts` helper pattern — last 7/30/365 days from *now*, not calendar periods):
- Subscribers (signups, unsubscribes, net).
- Accounts created, and per-account My Shows/Favorite Artists counts.
- Digest email engagement (opens/clicks), sourced from Resend's webhook via `RESEND_WEBHOOK_SECRET` (see Secrets section) — this is why that secret and its Svix-signature verification exist.
- Top favorited artists and venues.
- Top starred shows.
- Venue suggestions submitted.

**Cloudflare zone data** (via `fetchCloudflareZoneAnalytics()`, `worker.js`, using `CLOUDFLARE_ANALYTICS_TOKEN` and `CLOUDFLARE_ZONE_ID` against Cloudflare's GraphQL Analytics API, `httpRequests1dGroups`):
- Requests / page views.
- Threats blocked.
- Cache hit ratio and error rate.
- Top countries by traffic — rendered with full country names, not ISO codes.
- The query window is deliberately capped at 358 days, not the full year, to stay under Cloudflare's 52-week-1-day-1-hour query-span limit — querying a full calendar year would occasionally exceed it depending on leap-year/DST alignment.

**Layout**: reworked from a flat stat dump into grouped sections with wider numeric columns (so larger numbers don't get clipped as the dataset grows) and click-to-sort tables.

**What this doesn't cover** (deliberately, per the "not too esoteric or nosy" framing that shaped this feature): no per-user browsing/click tracking, no IP-level user profiling, no third-party analytics/ad trackers. Everything shown is either an app-necessary record (who's subscribed, what they starred) or Cloudflare's own aggregate edge telemetry.

## Digest email

Sent weekly via Cron Trigger (`sendDigestToAllSubscribers`, called from the Worker's `scheduled()` handler — cron schedule lives in `wrangler.toml`, currently `0 17 * * thu` = 17:00 UTC Thursdays (1pm ET), changed 2026-09-12 from the earlier `0 19 * * wed` = 19:00 UTC Wednesdays, which was itself a fix for an even earlier `0 18 * * 3` that would have silently shifted the send time by an hour on deploy). Changed together with the separate weekly research routine's own schedule (not part of this repo — see "Show data collection" below), which now runs 3am ET Thursdays, a few hours ahead of this send, so a fresh data pull is in `shows.json` before that week's digest goes out. Personalized per subscriber: pulls their `myShows` from KV, renders a dedicated "My Shows" section above "Added This Week" and "Everything Else Coming Up," with a one-click star/unstar link on every card (`/api/star-show`, reusing their unsubscribe token as auth).

Header uses a double amber-border treatment matching the site's `.b2-frame` CSS, reproduced with nested `<table>`s since HTML email doesn't support `clip-path` (site's cut corners → square) or reliably render `rgba()` in old Outlook (site's translucent inner border → solid `--amber-dim` `#8a672a`). Font is Georgia (web-safe serif), deliberately not the site's Google Font. (Note: an earlier *draft mockup* of the main site's time display had also used Georgia and caused AM/PM to wrap — that was a bug and was fixed in `index.html`'s own card display, which now uses a condensed font for the time number with AM/PM as a smaller inline suffix on the same line. The digest email's use of Georgia for its header is a separate, deliberate, and still-current choice — don't conflate the two.)

`/api/digest-preview` (session-gated, your own digest) and `/api/test-send-digest-now` (session-gated, owner-only, fires a real send to every subscriber) exist for manual testing without waiting on the Cron Trigger.

## Account model: sign-in, subscribe/unsubscribe & Contact Us (2026-09-12, PRs #66–#68)

Driven by the user's explicit request to stop putting a plain email address on the page ("I don't want that much spam") and to make subscribe/unsubscribe state track the sign-in checkbox exactly, rather than an earlier implicit-subscribe behavior.

- **Combined "About & Contact" footer panel.** The old separate "Show details" disclaimer note, the privacy-details toggle, and (new) a Contact Us form are now one panel behind a single `#privacy-toggle-btn` labeled "About & Contact." No visible admin/owner email address anywhere on the page — Contact Us is now the only way a visitor reaches the owner from the site itself.
- **`POST /api/contact` (new, `handleContactUs` in `worker.js`)** — public, unauthenticated, Turnstile-gated, per-IP rate-limited (`contact-ratelimit:<ip>`, same pattern as the other rate limits in the KV table above). Body: `{ email?, message, turnstileToken }` — `message` required, ≤2000 chars, rejects `<`/`>` (same input-validation convention as favorite names/venue suggestions); `email` optional (a visitor can send a note without giving one — stored as `(no email provided)` where displayed). Stores `contact:<uuid>` → `{ email, message, submittedAt }` in KV and emails the owner (`buildContactEmailHTML`/`sendContactEmail`, subject "New Contact Us message").
- **Admin panel mirrors this** — `handleAdminStats` now also returns `contactMessages: { count, list, window }` (parallel to the existing `suggestions` block), and `admin.html` renders a "Contact Us messages" block in the Community section right alongside "Venue suggestions."
- **Explicit subscribe/unsubscribe semantics, replacing an implicit `ensureSubscribed()`.** The sign-in form has a `#signin-subscribe-check` checkbox ("Send me a once-a-week email of new shows"), checked by default. `subscribe: boolean` now flows end to end: `POST /api/auth/request-link` accepts it and stores it on the token (`JSON.stringify({ email, ...(returnTo?{returnTo}:{}), subscribe })` — an `undefined` value here is simply dropped by `JSON.stringify`, so an older/no-checkbox client degrades safely to "leave subscribe state untouched"); `GET /api/auth/verify` reads it back off the token and calls one of two new helpers:
  - **`subscribeEmail(email, env)`** — writes `subscriber:<email>`, always clears any `unsubscribed:<email>` marker (an explicit opt-in overrides a past unsubscribe, same as clicking "Subscribe to email updates" directly).
  - **`markUnsubscribed(email, env)`** — looks up `subscriber:<email>` first so it can delete that record's own `unsubtoken:<uuid>` too (not just the `subscriber:` key itself), then sets the permanent `unsubscribed:<email>` marker. Shared by three call sites now: the sign-in checkbox (when unchecked), `/api/unsubscribe`'s confirmed click, and (indirectly) anywhere else that used to call the old `ensureSubscribed()` — which no longer exists.
  - `handleSubscribe`/`handleUnsubscribe` (the standalone `/api/subscribe` POST and `/api/unsubscribe` GET-with-confirm routes) were refactored to call these same two helpers rather than duplicating the KV writes.
  - **The visible "Unsubscribe" note/link in the sign-in UI was removed** — unsubscribing is now just "sign in and uncheck the box," not a separate control. The digest email's own footer "Unsubscribe" link (`buildDigestEmailHTML`, confirmed already present at the time of this change, not newly added) remains the mechanism for someone who wants to unsubscribe without ever signing in again.
  - **"No spam, ever." note** sits next to the sign-in control (`#no-spam-note`, toggled by `renderAccountUI()` — hidden once actually signed in, since at that point it's not a standing claim about the account, just reassurance about the act of giving out an email address in the first place).
- **Past-show cutoff fixed to drop same-day, not with a 1-day grace period.** `pastCutoff`/`upcomingShows()` in both `index.html` and `worker.js` now use `new Date().toISOString().slice(0,10)` directly as the inclusive-today boundary (was previously `Date.now() - 1*24*60*60*1000`-style logic that kept yesterday's shows visible for one extra day) — a real off-by-one, duplicated identically in both files per the existing "these must match" convention (see `showId()` note in Data model above), fixed in both at once.
- **Magic-link email copy** (found undocumented while writing this section, folded in here since it's the same account-flow surface): subject is "Your Show Notice sign-in link," body says "sign in to your Show Notice account," and the link itself is anchored as "Sign In Here" rather than displaying the raw URL — matches the "Website" link-text convention adopted for venue pages in the nav redesign below (display a label, not a bare URL, wherever a link's destination is already obvious from context).

## Filter bar (browse view) — superseded, see "Nav/layout redesign" below

**This section describes filter mechanics that no longer exist in the code as of the PR #19 header/nav redesign** (confirmed 2026-09-12 by searching `index.html` for its date-range/toggle markup — none found) but were never corrected here at the time. Left below, struck through in spirit, for history; do not treat it as current behavior.

~~Controls: date range (This week / This month / All), a single-venue selector (no "exclude this venue" mode — tried and explicitly removed as unnecessary), and a "Favorite artists only" toggle. Default on load: all dates, all venues, favorites off. Applies only to the browse views, never My Shows/Favorite Artists.~~

**Current reality (2026-09-12, PR #70):** there is no date-range or favorites-only filter. The only calendar-narrowing control is the **All Shows venue filter** — see "Nav/layout redesign" below — a multi-select venue/festival picker scoped to the All Shows section only, same as the old bar's stated scope. A show that's in My Shows still appears normally in All Shows too — there is still no exclusion logic anywhere that removes a show from the full list just because it's also in My Shows.

## UI dialogs (custom modals)

As of PR #17, `index.html` has **zero native `alert()`/`confirm()` calls** — every one was replaced with a small custom modal system so buttons can say "Yes"/"No"/"OK" (a browser's native `confirm()` is always "OK"/"Cancel" and can't be relabeled) and everything stays visually consistent with the site's own styling (same panel look as the filter sheet, same `filter-btn-clear`/`filter-btn-apply` button classes).

Three reusable, Promise-based helpers (defined near `attachWatchHandlers()`):
- **`showAlert(message)`** — single "OK" button. Used for: the blocked-localStorage warning, favorite-name validation, every sign-in-flow message (empty email, request errors, test-mode magic link, "Check your email," invalid/expired link), the subscribe flow, and the venue-suggestion flow.
- **`confirmYesNo(message)`** — "Yes"/"No" buttons, resolves `true`/`false`. Dismissing via the backdrop counts as No. Used for the single-artist star-to-favorite prompt (see below).
- **`pickArtistsToFavorite(candidates)`** — a checklist of artist names (all pre-checked), "Add Selected"/"Skip" buttons, resolves the array of names left checked (`[]` on Skip or backdrop-dismiss). Used for the multi-artist star-to-favorite prompt (see below).

Each has its own `#<x>-overlay` div in the HTML (`confirm-overlay`, `alert-overlay`, `artist-picker-overlay`), sharing `.modal-overlay`/`.modal-box`/`.modal-message` CSS classes. If a new confirmation/input dialog is ever needed, extend this pattern rather than reaching for a native `alert()`/`confirm()`/`prompt()`.

## Header layout & mobile responsiveness (PRs #12–#14, #16–#17, #19, #21–#24, #69–#70)

A same-day 2026-09-10 session made several changes to the page header and utility links, mostly driven by live mobile screenshots — culminating in a full redesign (#19) that replaced most of the earlier iterations outright. History, oldest first:

- **Riverfront Park venue-page mobile overflow (PR #12).** Riverfront Park's venue-site URL (`northcharleston.org/visitors/attractions_points_of_interest/riverfront_park/index.php`, ~97 chars) is far longer than any other venue's (next longest ~64 chars) and had no `overflow-wrap` rule — the unbroken `<a>` text forced the whole page wider than a mobile viewport instead of wrapping, squishing the visible layout to the left. Fixed with `overflow-wrap:anywhere` on both `.venue-site-link` and `.venue-address`. Still current.
- **Utility-row reorg (PR #13), sizing (PR #14), alignment fix (PR #16), and mobile-columns fix (PR #17) — all superseded by #19, see below.** These introduced and then repaired a two-column `.utility-cols`/`.utility-col` jump-link layout (My Shows/Full List left, Manage favorite artists/Suggest a venue right) plus a `.utility-row` wrapper for sign-in/Last-Updated. None of those classes exist anymore as of #19 — kept here only as history in case an old branch/PR references them.

### Full redesign (PR #19): sticky banner, sticky section headers, nav pills

- **Sticky title banner.** `.b2-frame`/`.tagline` live in a new `.banner-sticky` div, now a **direct child of `.wrap`**, positioned *before* `<header class="top">` rather than inside it — a `position:sticky` element can only stay pinned as long as it hasn't scrolled past the bottom of its own containing block, and `header.top` is short, so nesting it there caused it to un-stick after a short scroll. `.wrap` spans the whole page, so that's its containing block now. A `--banner-h` CSS custom property, kept in sync by `updateBannerHeight()` (re-run on load, `window resize`, and `document.fonts.ready` — Bebas Neue loads async and can shift the banner's height slightly after first paint), tells every section header exactly how far down to pin itself.
- **Sticky section headers.** `.sticky-head` (`top:var(--banner-h)`) wraps the title + links row of five sections — Added This Week, My Shows, All Shows, Favorite Artists, Suggest a Venue — so each section's own heading stays visible while its content scrolls underneath, directly below the still-pinned title banner.
- **"Full List" renamed to "All Shows," now a real section.** `#main-list` (previously a bare `<div>` with no heading at all) is now wrapped in `<section id="all-shows-section">` with its own `.section-title`. The header nav pill (see below) and jump-to-all-shows logic were renamed to match.
- **Chained "Back to top" + "next section" links.** Every one of the five sections above gets a `.section-title-links` block: a `.back-to-top-link` (existing generic handler) plus — except on the last one, Suggest a Venue — a `.jump-next-link` with `data-jump-next="<next-section-id>"`, chained Added This Week → My Shows → All Shows → Favorite Artists → Suggest a Venue. One generic `[data-jump-next]` click handler drives all of them.
- **Header nav pills.** The old two-column jump-link layout is gone. In its place: a single horizontally-scrollable row (`.nav-chip-row`) of 4 pills (`.nav-chip`, styled like `.venue-chip` but with a fixed teal border/text instead of per-venue color) — **My Shows**, **All Shows**, **Favorite Artists**, **Suggest a Venue** (note the renamed/recapitalized labels — no longer "Manage favorite artists" or "Suggest a venue"). On mobile the row is `justify-content:flex-start` (not centered) specifically so nothing before the visible viewport becomes unreachable — you can't scroll left past position 0, so centering a row wider than the screen would strand its start.
- **Status row.** Sign-in/out and Last Updated moved into their own `.status-row` below the nav pills, with its own hairline top border and `justify-content:space-between` — this is also what let the `align-self:flex-start` overrides from PR #16 finally get removed entirely; the flex layout doesn't need them.
- **Last Updated itself is unchanged** — still reads `data.dataUpdatedAt` from `shows.json` as-is (the date the file was last edited, whatever the reason); no separate "last full redesign/update" field was added.

### Rounding out the redesign (PRs #21–#24)

A second same-day 2026-09-10 pass, driven by more live mobile screenshots and follow-up requests against the #19 redesign:

- **Divider + sticky venue name (PR #21).** `.nav-chip-row` got the same `border-top`/`padding-top` divider convention the old `.utility-row` used, separating the venue/festival pills above it from the 4 nav pills below. Separately, a venue's own show page (`showVenueView`) wraps its `<h2>` venue name in `.sticky-head` (same class every section header uses), so it pins below the title banner while that venue's shows scroll underneath.
- **Mobile nav pill sizing (PR #22).** `.nav-chip`/`.nav-chip-row` sized down on mobile only (`font-size` 12px→11px, `padding` 6px 14px→5px 11px, `gap` 8px→6px) so the first 3 pills (My Shows, All Shows, Favorite Artists) fit on a 375px-wide screen with the 4th (Suggest a Venue) left off-screen but reachable via the row's existing horizontal scroll. Desktop untouched — it already fit all 4.
- **Sticky date headers (PR #23, extended to every list in PR #24).** `.day-head` (the "Saturday, September 12"-style date banner above a group of same-day shows) is now `position:sticky` everywhere shows are grouped by date, so the date stays visible while that day's shows scroll by, handing off to the next date at the right moment. This now covers **all four** show lists:
  - All Shows and a venue's own page (#23)
  - My Shows and Added This Week (#24) — both were flat lists (an inline date per card, via a `flatDate` mode on `cardHTML` that's now been **removed entirely**, along with its `.flat-date` CSS, since nothing calls it anymore) rather than day-grouped; switched to the same day-grouped rendering as the other two, via a new shared `groupByDayHTML()` helper (the grouping/sorting logic used to live only in the All Shows render step, now used by all four lists instead of being copy-pasted).

  Each context's `.day-head` pins at `calc(var(--banner-h) + <that context's own .sticky-head height>)` so it stacks directly below the still-pinned banner and section/venue header rather than overlapping it. Four parallel CSS vars track those heights, same pattern as `--banner-h` itself: `--added-this-week-head-h`, `--my-shows-head-h`, `--all-shows-head-h`, `--venue-head-h`. `.day-head` also switched from a `background` shorthand (whose gradient fades to fully transparent on the right) to a solid `background-color` with the gradient layered on top as `background-image` — sticky content needs an opaque backdrop or cards scrolling underneath show through the transparent tail.

  **A real bug worth remembering:** `showVenueView()` originally measured `--venue-head-h` *before* `viewEl.style.display` was set to `'block'`, so `offsetHeight` read `0` — anything inside a `display:none` ancestor measures zero regardless of its own size. Same class of bug nearly recurred for `--added-this-week-head-h`, since that section also starts `display:none` and only switches on inside `render()` when there's something recent to show — its height is measured from inside `render()` itself, right after the display flip, rather than from the page-load/resize/`fonts.ready` handlers the other three heights use (which run before that section is necessarily visible). **Any future sticky-height measurement on an element that can start or become `display:none` needs to happen after it's confirmed visible, not just after its markup exists.**
- **Sticky "← Back" link on venue pages (PR #24).** Used to sit above `.sticky-head` as a separate block, so scrolling into a venue's show list scrolled it out of reach. Moved inside `.sticky-head` alongside the venue name (same `.section-title-row` layout the rest of the redesign uses for title+links rows), label shortened to "← Back" to fit compactly.

**Takeaway for future layout work:** screenshot-test at actual mobile widths (375px/390px/430px covers the common range) before considering a responsive layout change done — several items in this section's history (#12, #17, #22) were regressions/gaps that only surfaced in a real mobile screenshot, not in desktop-width review. For anything involving `position:sticky`, verify the containing block is tall enough to hold the pin for the whole scroll range you expect (the #19 banner fix), measure heights only after the element is confirmed visible — not just present in the DOM (the `display:none` bug above, twice), and test at real scroll depth, not just a quick scroll-and-glance — a scripted test that fires `window.scrollTo` and screenshots too soon can catch a smooth-scroll animation mid-flight and look like a bug that isn't one (use `behavior:'instant'` or wait long enough, and cross-check the element's actual `getBoundingClientRect()` before trusting a screenshot alone).

### Nav/layout redesign, 2026-09-12 (PRs #69–#70)

Two rounds against the same user request, run back to back the same session: PR #69 did the structural reshuffle (moved sections/controls around, first cut of a venue filter as a native `<select>`); PR #70 was pure follow-up polish once the user reviewed #69 live (underline the sign-in link, relocate Last Updated, restyle the filter as a pill matching the other jump-links, make it multi-select, re-center the top pills). Both merged; treat this as the current, final state — don't reconstruct #69's single-select `<select>` version, it no longer exists.

- **Top nav pills reordered and reduced to three:** All Shows, My Shows, Favorite Artists (previously My Shows, All Shows, Favorite Artists, Suggest a Venue). **Suggest a Venue pill removed from the top nav** — the section itself (`#suggest-venue-section`) still exists and still works (Contact Us, added the same day per the account-model section above, is a related but separate feature — Suggest a Venue is specifically for requesting a venue be added to the tracker, still session-gated), it's just no longer pinned to the top nav or cross-linked from Favorite Artists' section header; reachable only by scrolling to it. Centered via `justify-content:center` in both the desktop rule and the (previously `flex-start`, now also `center`) mobile media-query override — the old `flex-start` was deliberate back when a 4th pill could overflow off-screen with no way to scroll left to it (see PR #22 above); with only 3 pills that constraint no longer applies.
- **Venue/festival pill directory (`#venue-links`/`#festival-links`) moved from the page header down to a new `#venue-directory-section` at the very bottom of the page**, just above the footer — user's own framing: "the venue pill list is getting large... might remove that... we'll see," so this is treated as a temporary/reversible relocation, not a permanent design decision. No title/heading was added to this section — kept exactly as minimal as it was in the header, just relocated.
- **Sign-in relocated into My Shows.** The `#account-btn` (sign-in/sign-out button), the `#no-spam-note` reassurance text next to it, and the entire sign-in form (`#sign-in-section` — email input, subscribe checkbox, Turnstile, submit button) all moved out of the page header and into the top of the My Shows section, above `#watch-list`. `renderAccountUI()` needed no changes — it still targets these elements purely by ID, which didn't change, only their position in the DOM. `#account-btn` also picked up `text-decoration:underline` (PR #70) so it reads as a link/control rather than just colored text, in both its signed-out and signed-in ("Signed in as X · Sign out") states.
- **"Last updated" moved out of the header entirely, down into the footer** (PR #70) — now the very last thing on the page before the footer's own buttons, rather than sharing a header status row with the (now-relocated) sign-in line.
- **My Shows' own section-header pills changed to "All Shows ↓" and "Favorite Artists ↓"** (jump-links, `data-jump-next`), replacing what used to be "Back to top ↑" + "All Shows ↓" — since the top nav (now 3 pills, always visible) already covers "back to top," a dedicated pill for it here was redundant.
- **All Shows' section-header pills reduced to just "Back to top ↑"** — its old "Favorite Artists ↓" jump-link was dropped since Favorite Artists is now reachable both from My Shows (above) and the top nav.
- **Favorite Artists' section-header pill reduced to just "Back to top ↑"** — its old "Suggest a Venue ↓" jump-link was dropped along with Suggest a Venue's top-nav prominence (see above); nothing else links to Suggest a Venue anymore, it's scroll-reachable only.
- **All Shows venue filter — a multi-select checkbox panel, not a native `<select>`.** Sits between the "All Shows" title and the "Back to top" pill in that section's `.section-title-row` (a `.venue-filter-dd` wrapper, `position:relative`). Collapsed state is a pill (`.venue-filter-toggle`) styled identically to `.back-to-top-link`/`.jump-next-link` (same shared CSS selector, extended to include it) — label shows "Show all venues ▾" when nothing's selected, the single venue's name when exactly one is, or "`N` venues selected ▾" for more than one. Clicking it toggles a `.venue-filter-panel` (`position:absolute`, `z-index:20`, opaque background) open — **it deliberately overlaps and visually covers the Back to top pill next to it rather than pushing the row's layout around**, per the user's own spec ("it can widen out to cover up the Back to Top pill until collapsed"); collapses again on re-clicking the toggle or on any click outside `.venue-filter-dd` (a document-level click listener checks `dd.contains(e.target)`). Selection state lives in a module-level `VENUE_FILTER` (a `Set` of venue/festival codes, empty = show all) plus `VENUE_FILTER_OPEN` (open/closed, tracked separately from the Set so an unrelated `render()` call — e.g. from a star toggle elsewhere on the page — doesn't slam the panel shut mid-selection). Filtering itself is a plain `VENUE_FILTER.size ? sorted.filter(s => VENUE_FILTER.has(s.v)) : sorted` inside `render()`, applied only to `#main-list` (All Shows), same scope the old dead filter-bar docs above claimed. **Gotcha for anyone testing this with Playwright/automation:** each checkbox's own `change` handler calls `render()`, which rebuilds the panel's entire `innerHTML` — a stale element handle to a checkbox (e.g. from an earlier `$$()` call) will be detached by the time a second interaction runs against it, and Playwright's `.check()` specifically fails on this (it re-verifies checked state against the same handle after the click); `.click()` doesn't have that extra verification step and works fine. Re-query fresh handles between interactions rather than reusing one across multiple state changes.
- **Venue pages: site link text changed from the raw URL to "Website."** `showVenueView()`'s `siteLine` now renders `<a href="${venueSite}">Website ↗</a>` instead of printing the URL itself as the link text — same href, just a label instead of exposing the raw address inline (mirrors the magic-link email's "Sign In Here" convention noted in the account-model section above).
- **Venue pages now pick up that venue's own accent color** (the same `color` field already driving that venue's pill border/text in the directory) for its `<h2>` name, the "← Back" link, the site-link text, the address-link hover state, and a 3px top border strip on the whole `.venue-view` block — replacing what was previously a uniform amber treatment on every venue page regardless of which venue it was (raised by the user as "the colors at the top seem too uniform"). Implemented via a `--vc` CSS custom property set with `viewEl.style.setProperty('--vc', venue.color)` inside `showVenueView()`, referenced throughout `.venue-view` CSS as `var(--vc, var(--amber))` so a venue with no `color` set still falls back to the original amber look. **Gotcha:** when a venue has no color, the code calls `viewEl.style.removeProperty('--vc')` rather than setting it to `''` — a CSS custom property explicitly set to an empty string still counts as "set" for `var()`'s fallback logic (the fallback only kicks in when the property is genuinely absent), so setting it to `''` would have made the color rule resolve to nothing/inherit instead of falling back to amber as intended.
- **One small sitewide polish item, deliberately minimal:** a slightly richer glow on the title banner text (`text-shadow`, two layers instead of one) — added in response to a mid-message aside ("need to work on presentation for the entire site... need just a little more energy. Not too much tho") that was otherwise interpreted narrowly (as being about the venue-page color fix above) since the rest of that sentence was never completed. Explicitly flagged to the user as an inference, not a confirmed instruction — if a broader sitewide visual pass is actually wanted, get specifics rather than assuming this covers it.

## My Shows / Favorite Artists model

- Two independent lists, deliberately decoupled. Favoriting an artist (Favorite Artists) always surfaces their upcoming shows in My Shows automatically. Favoriting a single show does not add the artist to Favorite Artists, and vice versa (this reversed an earlier, coupled behavior that used to exist in production).
- Un-favoriting an artist does not retroactively remove shows already auto-added to My Shows because of that artist — those stay until manually removed. Deliberate, not an oversight.
- Storage keys were renamed from `watchlist` to `my-shows` (client-side key, and the wire/KV field sent to the Worker, now `myShows`) — done deliberately while there were few enough users that no data migration was needed. Any future schema rename needs to touch `index.html`, `worker.js`, AND `admin.html` together (`admin.html` reads a `myShowsCount` field derived from this).
- **Favorite matching checks openers, not just the headliner (PR #10).** `matchesFavorite(bandName)` does substring-containment matching (both sides normalized: lowercased, non-alphanumeric collapsed to spaces) — a favorite matches if it's a substring of the show's artist name, e.g. favoriting "Trombone Shorty" matches "Trombone Shorty & Orleans Avenue." This originally only ever checked a show's `b` field, which meant a favorited artist buried in a multi-artist show's `o` field (festivals put the event name in `b` and the real lineup in `o`) never matched anything — favoriting "Darius Rucker" didn't pick up Riverfront Revival. Fixed via `showMatchesFavorite(s)`, which checks `b` first, then splits `o` the same way `cardHTML()` does for rendering and checks each name individually. Both the "Favorite artists only" filter and the auto-add-to-My-Shows logic in `render()` use `showMatchesFavorite`, not a raw `b`-only check, going forward.
- **Storage-reliability fixes (PR #11).** Two gaps in the signed-out storage path (localStorage is the *only* persistence layer when not signed in — no server round-trip):
  1. `saveMap()` used to swallow `localStorage.setItem` failures silently (`catch(e){}`). Some browser contexts — Safari Private Browsing chief among them — block all localStorage writes. The UI still showed the change as saved regardless (it renders off the in-memory array before the write even runs), with zero indication it hadn't actually persisted. Now warns once per page load via `showAlert()` and points at signing in as a fallback (a signed-in user's data also round-trips to the server, so it isn't dependent on localStorage working).
  2. The initial load of `MY_SHOWS`/`FAVORITES` from storage only ever ran inside `render()`'s first call, behind the `shows.json` fetch — but `#fav-input`/`#fav-add-btn` are wired up immediately at parse time, so a click on a slow connection could theoretically race the load. Consolidated into a single memoized `loadStorageOnce()` that `render()`, `addFavorite()`, and the star-toggle handler all await, so there's one source of truth instead of independent loads that could clobber each other.
- **Star-to-favorite-artist prompt (PRs #15, #17).** Starring a show (adding it to My Shows) now offers a one-tap way to also add the artist to Favorite Artists — opt-in, never asked when un-starring, and skipped entirely for an artist that already matches an existing favorite (via `matchesFavorite`, so no repeat prompts). Wired through two new attributes on the star button in `cardHTML()`: `data-band` (`extractArtistName(s.b)`) and `data-lineup` (the raw `s.o` field). Two paths:
  - **Single-artist shows:** `confirmYesNo()` — `Also add "<artist>" to your Favorite Artists?`
  - **Multi-artist/festival shows** (same "is this actually a list" check `cardHTML()` already uses to decide between opener chips and inline "w/ opener" — `o` splits into more than one comma-separated part, each ≤60 chars): `pickArtistsToFavorite()` shows a checklist of the event name (`b`) plus every individual lineup artist parsed from `o`, all pre-checked, with any already-favorited names excluded from the list entirely. Selecting a subset and confirming adds only those. This is what lets a show like Riverfront Revival (`b`: "Riverfront Revival", `o`: 17 comma-separated artist names) offer each artist individually, rather than only the event name itself.


## Repo notes

- `cowork-task-instructions.md` was rewritten from scratch in an earlier session.
- **Branch hygiene is now clean.** "Automatically delete head branches" is enabled and confirmed working (every PR from #18 on had its branch auto-deleted on merge). The 13 legacy branches that predated the setting (`digest-email-header-border`, `fav-storage-race-fix`, `favorite-match-openers`, `header-size-tweak`, `notes-and-festival-data`, `project-notes-consolidated`, `project-notes-update-2`, `rfp-venue-url-wrap`, `riverfront-revival-venue-fix`, `star-favorite-prompt`, `star-modal-and-columns`, `utility-row-alignment-fix`, `utility-row-jump-links`) were deleted manually as of 2026-09-10 — `main` is now the only branch in the repo. (Note for any future automated session: git push credentials here get an HTTP 403 specifically on branch **deletion**, confirmed 2026-09-10 — a deliberate scope restriction, not a bug, and no GitHub MCP tool exists for it either — so an automated session still can't do this cleanup itself if it's ever needed again; it has to be done manually.)
- **A single long remote session (2026-09-11) reused one branch name, `claude/kind-brahmagupta-wmw4ya`, across ~26 sequential PRs (#26–#51)** — each PR merged, then the same branch name was recreated from the new `main` tip for the next round of work, rather than a fresh branch per change. This is a property of that session's designated-branch setup, not a hygiene regression; branch auto-delete-on-merge still applies normally between rounds. A future session picking up work here should still create/reuse its own designated branch per its own instructions rather than assuming a fixed name.

