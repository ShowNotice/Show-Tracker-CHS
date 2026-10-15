# Weekly update instructions — Lowcountry Show Notice

This file is the weekly routine's instructions; the routine itself only says "follow
pipeline/INSTRUCTIONS.md". Changes go through a pull request like any other file, so
there's a diff and history. The routine must never edit this file — only an interactive
session or the owner does, and only when the owner asks.

The format of `shows.json` is defined in `docs/SHOWS_SCHEMA.md`, and
`scripts/validate_shows.py` enforces it (it also runs on every PR as the
"Validate shows.json" check).

_History: the rules below were carried over verbatim on 2026-10-15 from the routine's
stored prompt (last revised that day), then updated for the items marked "2026-10-15"._

## What this task does, every run

- Fetch every tracked venue's own calendar/schedule page (see the fetch-strategy table below).
- Diff the results against the current shows.json in the repo.
- Add genuinely new shows; backfill missing fields (time, price, opener, stage) on existing shows; correct dates where the venue's own site disagrees with the data. Remove a show when the venue has cancelled it or it is no longer on the venue's own site/source (see "Standing decisions").
- Apply every rule below without exception.
- Commit the updated shows.json (routines push to a claude/-prefixed branch and open a PR by default).
- If, and only if, every check in "Validation before committing" below passes cleanly, the PR's "Validate shows.json" check is green (wait for it: `gh pr checks <number> --watch`), and none of the "When NOT to auto-merge" conditions apply, merge the PR (gh pr merge --squash). Never add the `owner-approved` label yourself — only the owner, or an interactive session the owner directs, adds it. The repo deletes merged head branches automatically, so do not pass --delete-branch. If anything fails validation, or if anything about the diff seems unusual enough that a human should look first (see "When NOT to auto-merge" below), leave the PR open and unmerged instead — do not merge with a caveat, either merge cleanly or don't.
- For anything that doesn't cleanly resolve under these rules — a judgment call, not a lookup — leave a clear note in the PR description (or a flag field on the specific show) rather than guessing.
- Policy note (2026-10-01): a separate weekly check-in looks at any PR this leaves open and reviews it in plain language directly with the user, so leaving a PR open isn't a dead end — it just means a person looks at it within about a week.

## Standing decisions (owner, 2026-10-01)

- A show the venue has cancelled is removed from shows.json (e.g. the Pour House Monday Muse dates of 2026-10-05, 10-12 and 10-19). Changed 2026-10-15 (owner): a show that is no longer on the venue's own site/source is also removed, with or without a cancellation notice. Safeguards: (1) only when that venue's fetch fully succeeded this run — never on a failed, blocked, rate-limited or partial fetch; (2) only for dates inside the range the source actually covers (e.g. don't remove a Windjammer show dated after the last event on its 20-event list); (3) first rule out a rename, typo or move — the same act on another date is a date correction, and a misspelled title (e.g. Pour House's "Tuak" for TAUK) is the same show; (4) never for CHR (manual entry) or rows the owner entered or confirmed directly. List every removal in the PR description with the reason.
- YALL Fest (Charleston Music Hall, 2026-11-14) is excluded; do not re-raise it.
- Refinery events listed under its Events section that have a ticket link are included even when the lineup is unknown (e.g. "Open Air Halloween," 2026-10-30) — add them with the times left out and a flag if details can't be fetched.
- Owner confirmations (2026-10-15) — authoritative over any source; don't re-add the removed rows. SNOB: Connor Sage plays 10/21, not 10/20 (no Connor Sage row on 10/20); Krystal Halvorson is 10/28, and Ben Somerville is not playing 10/21 or 10/28. Uptown Social 10/16 is Moody Bridge, 9–11 PM; Grayson Little is not playing. Commonhouse has no show on 11/05; Backseat Company is 12/11. Pour House Monday Muse on 11/02 is off.
- Recheck this run: SNOB 10/27 lists both Connor Sage and Matt Vajdic at 6:00 PM, and the venue's website also showed both on 2026-10-15. Both rows stay flagged. In the PR description, say what livemusiccharleston.com/BeatGig show for that night now, and don't merge over it if both are still listed.

## Per-venue fetch strategy

### Charleston Pour House (PH)

**Source:** charlestonpourhouse.com/events/list/ + /events/list/page/N/

Full HTML, all fields inline, but /shows/ covers only ~6 weeks, and its own "next page" links carry a ?shortcode= query that robots.txt blocks (Disallow: /*?). Corrected 2026-10-15: crawl the path-based list pages instead — charlestonpourhouse.com/events/list/, then /events/list/page/2/, /page/3/ and so on until a page has no events. These have no query string, so robots.txt allows them; respect its Crawl-delay: 3. On 2026-10-15 this reached 99 upcoming events across 9 pages, through May 2027, and turned up 26 real shows (late Nov 2026 onward) the old method had missed. Each list entry has the date, title, stage tag, supporting acts and ticket link. For doors/show times and price, fetch each new show's own /event/... page: its schema.org Event JSON-LD has startDate with a correct Eastern offset (the show time) and offers.price, and the description text gives doors time and advance/day-of prices. Descriptions sometimes carry a stale year or weekday (e.g. "2026" on 2027 shows) — trust the list date and JSON-LD startDate, and flag a weekday mismatch. An event page that returns 404 and is gone from the list is removed (see Standing decisions). The "Subscribe to calendar" iCal feed (?ical=1) covers only ~2.5 weeks and is robots-blocked — don't use it. This is a method change, so the first run using it must not auto-merge. Multiple stages, checked separately: Pour House runs Main Stage, Deck Stage, and an outdoor Back Lot Stage, each capable of an independent show on the same date — a date with a marquee Main Stage act often also has an unrelated Deck Stage show that won't show up if you stop looking once you've found one show for that date. Deck Stage shows are typically ticketed via aftontickets.com (a real, confirmed ticketing platform for this venue, not resale) rather than the venue's own generic ticket flow — an aftontickets.com link on a Pour House show is expected and should be used as the u field like any other legitimate direct ticket link, not treated as a secondary/resale source. Known schema limitation (confirmed 2026-09-17): the same band can genuinely play two different stages on the same date (e.g. Main Stage early set + Deck Stage late set) — the (venue, date, band) uniqueness this routine validates against cannot represent that as two rows. When this happens, add whichever one isn't already present and note the schema limitation in the PR description rather than dropping either or overwriting the existing row. Cross-check only (don't outrank): axs.com/venues/130583. Vendor/market events are excluded outright, even with an explicit live-music mention (confirmed 2026-09-17) — e.g. "Pop-Up Market," "PoHo Night Market." Don't include-and-flag these; exclude them the same as any other non-music event.

### Music Farm (MF)

**Source:** musicfarm.com/calendar/

Full HTML, all fields inline including "LOW TIX"/"Sold Out"/"On Sale Soon" status labels. One page lists every upcoming event (39 through 2027-04-29 on 2026-10-15) as <article class="event-card …"> blocks; each card's tm_classifications-* classes give the Ticketmaster category — comedy, dance (DJ parties such as Club 90s / Emo Night Brooklyn), food-drink and podcast entries are excluded, but cards with no category can still be music (e.g. "Songs to Save the Edisto Finale w/ Shovels & Rope"), so read the title. A 2026-10-15 audit found 3 music shows earlier runs had missed (Benny The Butcher, Des Rocs, Songs to Save the Edisto) — go through every card, not just new-looking ones. On HTTP 429, wait ~60s and retry once before giving up on the venue. Cross-check only (don't outrank): axs.com/venues/124602 — event count fluctuates, don't trust a cached count

### The Royal American (RA)

**Source:** theroyalamerican.com/schedule

Full HTML, one page covers many months, all fields inline. No AXS page exists for this venue; other secondaries only catch ticketed touring dates, not the near-nightly local shows — venue's own site is decisively the most complete source.

### The Windjammer (WJ)

**Source:** the-windjammer.com/events/

Full HTML, all fields inline. The list page carries no prices; each event's own page has price and door/show times. Caution: day-of-week label and trailing date stamp on each card are not always internally consistent — if a date looks wrong, verify against the date badge + weekday label + URL slug together before trusting it (this venue has shown repeated real date/stage corrections across multiple runs, not one-off scrape errors). The list includes nightly Inside Stage bands as well as Beach Stage shows — check both. The /events/ list shows only the next 20 events, and /events/page/N/ returns the same 20 (confirmed 2026-10-15). Every run, also read the-windjammer.com/events-sitemap.xml (the full catalog of ~800 event pages with lastmod dates; robots.txt allows it) and fetch each /event/ page with a lastmod in the last ~120 days that isn't on the list or already in shows.json. Each event page gives title, price, date ("October 16, 2026") and "Doors at … Show at …". Keep the ones dated today or later. On 2026-10-15 this found exactly the same 20 upcoming events as the list (140 recent pages checked), so the two together are complete; a Windjammer row found in neither is no longer on the venue's site. whollyticket.com/upcomingEvents/?id=67 (the venue's ticketing page) is behind a Cloudflare bot challenge ("Just a moment…") as of 2026-10-15 — treat it as blocked and don't try to get past it. Cross-check only (don't outrank): axs.com/venues/130171 — note Bandsintown has duplicate venue pages for this venue, don't conflate them.

### Credit One Stadium (C1S)

**Source:** creditonestadium.com/events/

Full HTML, date/time/ticket-link, no price. Confirmed Ticketmaster/Seated as of multiple 2026-09 runs — do not treat SeatGeek as primary here (an earlier "changed to SeatGeek" claim was a research-pass error). axs.com/venues/120907 has a listings page as a secondary cross-check only.

### Firefly Distillery (FD)

**Source:** fireflydistillery.com/upcoming-shows/ (own site), cross-checked against earformusic.com/events (the promoter)

Updated 2026-10-15: the venue's own page loads again (HTTP 200, no sg-captcha header, full HTML) and is primary. It lists each upcoming concert as "Month D, YYYY" + "Live at Firefly with …" + a /event/… link; it doesn't give times. It listed exactly the same two upcoming shows as Ear For Music on 2026-10-15.

Ear For Music (earformusic.com/events) is the promoter that books Firefly's concerts (and many Refinery shows) — use it as the cross-check, and as the source if the venue's CAPTCHA comes back. Squarespace HTML: each <article class="eventlist-event …"> has the date (datetime="YYYY-MM-DD"), title ("Act at Venue"), venue name and a TICKETS link (Ticketmaster for Firefly). The page lists past events too — keep only dates from today on. Its start/end times (almost always 6:00–10:00 PM) are a site-wide placeholder: leave dr/sh out unless the venue or ticket page gives real times. robots.txt allows /events (the AI user-agents it names share the default rules, which block only /config, /search, /account, /api/ and similar), but ?format=json and ?format=ical are disallowed, so read the HTML only. Also cross-check The Refinery (REF) and Gaillard (GC) entries against it; it found nothing missing there on 2026-10-15. Events at venues not in this document (e.g. Holy City Brewing) are ignored. A promoter page may not list every Firefly event, so don't remove an FD row just because it's missing from Ear For Music — only when it's gone from the venue's own page too.

History: fireflydistillery.com was CAPTCHA-blocked (SiteGround sg-captcha challenge) from 2026-09-17 until at least 2026-10-08. If the challenge returns (an sg-captcha response header or a redirect to /.well-known/sgcaptcha/), stop — don't retry or work around it — and use Ear For Music. The first run after this source change must not auto-merge.

### North Charleston Coliseum & PAC (NCC)

**Source:** northcharlestoncoliseumpac.com/events

List has no times/price; individual /events/detail/... pages do. Plain curl may need --compressed and a browser-like User-Agent, and detail pages can return HTTP 406 to curl even when the list works — if so, fetch the detail page with WebFetch instead. Mixes in lots of non-music events (comedy, hockey, ice shows, Broadway, POPS orchestral) — filter per rules below. AXS is a genuine co-primary here, not just a cross-check — the venue's own FAQ names it alongside Ticketmaster for select events. Two separate AXS pages exist: Coliseum and PAC. If AXS hits a 403, fall back to Ticketmaster/the venue's own event-detail pages without further investigation. The venue's own list page only server-renders the first 12 events (about 2 weeks). Corrected 2026-10-15: its "Load More Events" button pulls the rest from northcharlestoncoliseumpac.com/events/events_ajax/{offset}?category=0&venue=0&team=0&exclude=&per_page=12&came_from_page=event-list-page — step offset by 12 (12, 24, 36…) until a response has no eventItem blocks. robots.txt allows it. On 2026-10-15 this returned 80 events through April 2027 and turned up 2 missed music shows (KC & The Sunshine Band 2027-01-28; Travis Tritt rescheduled from 9/26 to 11/14). Detail pages returned 200 to curl on 2026-10-15 and give doors/show times and the Ticketmaster link. "Sonic Live in Concert" (Sonic Symphony, a full orchestra) falls under the orchestral exclusion.

### Charleston Music Hall (CMH)

**Source:** charlestonmusichall.com/calendar/ (own site) or Ticketmaster

The venue's own site has a full calendar (through several months out, at /calendar/ — the homepage shows only a few) and is primary — a full pull from it does not need Ticketmaster at all. Same event-card markup and tm_classifications-* categories as Music Farm (104 cards through 2027-09-11 on 2026-10-15); sc-ballet, dance, comedy, charleston-comedy-week and lecture-seminar are excluded. A 2026-10-15 audit found 2 missed music shows (MICO 2027-02-21, Stayin' Alive 2027-09-11) — go through every card. On HTTP 429, wait ~60s and retry once. Many entries are comedy/lectures/kids' shows — exclude per rules below; skip entries labeled "CANCELLED:". Price capture is still known-blocked by Ticketmaster bot detection. AXS confirmed bot-blocked for this routine's fetch client as of 2026-09-09 — do a single cheap check per run, stop immediately on a 403.

### Charleston Gaillard Center (GC)

**Source:** gaillardcenter.org/buy-tickets/ (own site; gaillardcenter.org/events/ redirects there)

Updated 2026-10-15: the site loads again with no CAPTCHA, and robots.txt allows it (it only disallows /wp-admin/). The page lists every upcoming event with date, weekday, time, venue and genre tags (Authors & Lectures, Broadway, Classical & CSO, Comedy, Country, Dance, Family & Education, Holiday, Jazz, Music, Theater), and each event links to a gaillardcenter.org/events/<slug>/ page. Include events tagged Music, Jazz or Country (and Holiday when it's a music act). Exclude Classical & CSO — out of scope entirely, including CSO Pops — plus Broadway, Theater, Comedy, Dance and Authors & Lectures. Family & Education events count only when they're also tagged Music (Black Violin and Ghostbusters in Concert are already in shows.json on that basis). Shows sourced only from a web search must not be added. This is a source change, so the first run using it must not auto-merge.

### New Realm Brewing (NRB)

**Source:** livemusiccharleston.com, slug newrealmbrewingcharleston

Source changed 2026-10-01. Query /api/events/global and filter venue.slug == newrealmbrewingcharleston. Apply the same artist.configuration filter as below (Solo/Duo/Trio/Full Band = include; DJ = exclude; null → read description). Also exclude trivia nights, and skip entries whose "artist name" is placeholder text rather than a real act (e.g. "Artist will perform outside. Artist must bring own equipment/run sound"). Unnamed "pre-party" sets tied to nearby stadium shows have no named act — don't add them. Do NOT fetch newrealmbrewing.com/charleston/live-music-events/ (SiteGround captcha challenge AND an empty JS-rendered shell). Bandsintown confirmed bot-blocked. Eventbrite is reachable but returns only an empty JS shell.

### Charleston Tin Roof (TR)

**Source:** tockify.com/api/feeds/ics/tinroofschedule

Fetch as plain text/ICS — no bot-protection, standard format, and its DTSTART/DTEND values are genuinely correct UTC (confirmed 2026-09-17 by direct comparison against the feed's own stated door/show times). Parse VEVENT blocks: SUMMARY, DTSTART/DTEND (UTC, X-WR-TIMEZONE is America/New_York, convert accordingly), URL. Most of the feed (~90%+) is recurring non-music filler events extended ~2 years out — any SUMMARY repeating more than twice is filler, exclude without individual review. Door/show times and prices are usually embedded in SUMMARY text (e.g. "Door @ 7. Show @ 8. $10 21+"), always PM for this venue; prefer SUMMARY text over DTSTART when both are present. "Closed For Private Party" entries are not shows. DJ/vinyl nights with vendors (e.g. "Deep Crates"), comedy, karaoke and open mics are excluded.

### The Refinery (REF)

**Source:** therefinerychs.com

Wix site. Band names/dates render as plain visible text in a hand-built content block on the homepage, not in the site's Wix Events JSON (that's an unrelated market/fitness calendar). Read the full visible text near each event image — openers sometimes only appear in the fuller title text. Ticket links are ticketweb.com (some events use posh.vip, which may be unreachable from this environment — then leave the times out and flag). Fitness classes and vintage markets are not shows. No show times published on this page. Secondary source for times: charlestonlivemusic.com/venue/the-refinery/ — has a startDate/endDate schema.org JSON-LD field per event, but requires careful handling (corrected 2026-09-17): fetch each event's own page's raw JSON-LD directly via curl/plain HTTP (a markdown-converting fetch tool hallucinates times from boilerplate text instead — don't trust it here). Before using the value, check it isn't 1970-01-01T00:00:00 — that's a placeholder meaning no real date was ever entered; if you see it, there is no usable time from this source, leave sh/dr out. If it's a real date: read the date/time digits literally as America/New_York local time — do NOT apply a UTC-to-Eastern conversion, even though the field carries a +00:00 suffix suggesting UTC. That suffix is simply wrong on this site; treating it as true UTC and converting shifts an already-correct local time 4 hours too early. A real (non-placeholder) value here has only ever been observed to equal the actual show start time — never use it to infer a doors time; if doors time isn't stated anywhere, leave it unconfirmed. Never treat a previously-stored value in shows.json as independent confirmation of a new inference about this source — always re-derive from the primary source. A time the owner has supplied directly (e.g. 12/10 Caleb Lee Hutchinson: doors 7 PM, show 8 PM) is authoritative.

### Uptown Social (US)

**Source:** uptownsocialchs.com/entertainment/

Venue's own page has zero direct listings and explicitly defers to livemusiccharleston.com as its actual source.

### Commonhouse Aleworks (CHA)

**Source:** commonhousealeworks.com/events/

Own site returns HTTP 200 but zero real content — embeds a beatgig.com widget. Use livemusiccharleston.com or the BeatGig API directly (slug commonhousealeworks) — both return identical data. Market, block-party and "National ___ Day" promo listings are not shows.

### Slightly North of Broad (SNOB)

**Source:** snobcharleston.com/...

Same situation as Commonhouse Aleworks. BeatGig slug: slightlynorthbroadrestaurant. Same slug works for the livemusiccharleston.com fallback.

### Charleston Jazz Festival (CJF)

**Source:** charlestonjazz.com/performance/charleston-jazz-festival/

Not a weekly-cadence venue — check occasionally. As of 2026-09-17, "Save the Date" placeholder only ("April 11–20, 2027"), no lineup. Store as a single multi-day entry with no dr/sh and a note in o.

### Riverfront Park (RFP)

**Source:** northcharleston.org/visitors/attractions_points_of_interest/riverfront_park/index.php

Static city page with no event listings at all. Hosts named festivals (Riverfront Revival, Low Tide/High Tide, High Water Festival) with their own separate sites — fetch those directly instead. High Water Festival (source added 2026-10-13 at the owner's request): highwaterfest.com/lineup. The 2027 edition is Sat–Sun April 17–18, 2027 (lineup announced 2026-10-13). Store one row per festival day — b "High Water Festival", v RFP, d the day's date — with that day's full lineup in o, headliner first. Use the festival's own ticket page for u; leave dr/sh out unless the site states times. Take day assignments only from the festival's own site: as of 2026-10-13 press coverage disagreed on which day The Head and the Heart plays (Bandsintown: Saturday; Relix: Sunday) — if the official site doesn't settle it, flag it. Update 2026-10-15: both day rows are now in shows.json (entered at the owner's request from multi-outlet press coverage), with tickets at highwaterfest.frontgatetickets.com/event/442grwzrmvp6p6eg. highwaterfest.com is reachable, but /lineup shows the lineup only as a poster image ("HW27_Admat") hosted on cdn.prod.website-files.com, which this environment's network filter blocked on 2026-10-15 — there's no text lineup anywhere on the site. Don't remove or rewrite these rows because the lineup isn't in the page text. If the poster can be read, check the day split and resolve The Head and the Heart's day (update o and the flag), and note any difference from the press lineup in the PR description; if it can't, leave the rows as they are and don't re-report it. No other next-edition dates announced as of 2026-09-17 — check occasionally.

### Charleston Harbor Resort & Marina (CHR)

**Source:** (none — manual entry only)

Added 2026-10-13. Its "Oysters on the Point" series (oyster roast + live music, Saturdays Dec 2026–Mar 2027) is announced only on Instagram, which is never scraped. The owner enters these shows by hand: don't fetch for this venue, don't add CHR shows from web search, and don't remove or edit CHR rows because they're missing from any fetch.

## Venues removed 2026-09-17 (explicit user request — do not re-add)

- Tommy Condon's (TC), The Dinghy (DIN), Rita's Seaside Grille (RSG), The Tattooed Moose — Park Circle (TMPC), The Tattooed Moose — Johns Island (TMJI). (Note: livemusiccharleston.com still returns events for these and many other venues — ignore every slug not listed in this document.)

## livemusiccharleston.com — how to query it

GET https://livemusiccharleston.com/api/venues/names → confirmed slugs: uptownsocial (US), commonhousealeworks (CHA), slightlynorthbroadrestaurant (SNOB), newrealmbrewingcharleston (NRB).
GET https://livemusiccharleston.com/api/events/global → every booked event, no auth/pagination (~1,000 events, ~1 MB). Fields: start/end (genuinely correct UTC — confirmed 2026-09-17 against known-correct local times; convert normally), venue.slug, artist.name, artist.configuration, artist.genres, category, stage, description.
- Use artist.configuration to filter, not is_live_music (confirmed unreliable). Solo/Duo/Trio/Full Band = include; DJ = exclude. null → read description and judge. Market/vendor events excluded outright even with a live-music mention, same as the Pour House rule.
- Trusted source as of 2026-10-01 for US, CHA, SNOB and NRB (owner decision) — data from it no longer blocks auto-merge by itself. Still flag individual ambiguous entries.

## BeatGig API — how to query it (undocumented/reverse-engineered)

Real API at backend.beatgig.com/api/v1/graphql:

```graphql
query T($start: DateTime!, $offset: Int!, $limit: Int!, $slugs: [String!]!) {
  calendarBookings(start: $start, limit: $limit, offset: $offset, organizationSlugs: $slugs) {
    canFetchMore
    bookings: calendarBookings {
      bandConfiguration artistCategory publicEventDescription artistName
      venueSlug venueName startTime bookingType id
    }
  }
}
```
Trusted on the same footing as livemusiccharleston.com (it returns identical data).

## Non-music events — exclude, don't include-and-flag

- Exclude outright, no flag needed: DJ sets/dance parties/raves, themed nightlife nights with no booked act and no live-music mention, podcast tapings/talk shows/game-show-style events, markets/vendor events, burlesque/variety revues with no live band as headliner, comedy, Broadway/theatre, lectures, kids' shows, pure sports, ice shows, orchestral "Pops" concerts, classical. Signal words: DJ, Dance Party, Rave, Market, Podcast, Burlesque, POPS, Comedy, Trivia, Karaoke, Open Mic. Applies equally to AXS and Ticketmaster listings.

## Validation before committing (non-negotiable)

- After editing, run `python3 scripts/format_shows.py` (canonical formatting), then `python3 scripts/assign_ids.py` if it exists (gives new shows their permanent id), then `git show origin/main:shows.json > /tmp/base.json && python3 scripts/validate_shows.py shows.json --base /tmp/base.json`.
- Exit code 1 means the file is invalid: fix it; if you can't, don't commit — explain in the PR description instead.
- Exit code 2 means a review rule fired (big diff, mass removals, a big date move, an odd price): open the PR but don't merge it, and say at the top of the description which rule fired and why.
- The same check runs on GitHub as "Validate shows.json". Don't merge unless it's green.
- Unknown times, prices, links and notes are left out, never written as "—", "TBA", "see ticket link", null or "" (see docs/SHOWS_SCHEMA.md).

## When NOT to auto-merge (even if validation passes)

Leave the PR open for manual review instead of merging if any of these apply:

- 40 or more shows added or changed in a single run. A diff this large is more likely to reflect a fetch or parsing problem than a genuinely quiet week — worth a human glance before it goes to main. This still applies even to a run explicitly scoped broadly (e.g. "catch up every backfill item for venue X") — a big diff being expected doesn't exempt it from review, it just means the PR description should say clearly, at the top, that the size is expected and why.
- Any date correction that moves a show by more than 30 days from its previously recorded date. Small corrections (wrong day of week, off-by-one) are routine; a month-plus shift is more likely a parsing error than a real venue reschedule.
- Removals for a single venue of more than 5 rows, or more than 25% of its upcoming rows, in one run — that pattern is more likely a fetch or parsing problem than real cancellations.
- Any price recorded above $200 or below $5. Both ends are more often a scraping error than a real ticket price for these venues.
- Any show sourced from web search alone, with no actual fetch of the venue's own page or a real secondary source (e.g. a venue whose site is blocked that run). A web search summary is not a citable source — it isn't the same as confirming a show against a real page.
- Any source that failed, errored, returned unexpected data, or contradicted itself this run — note it in the PR description and leave the PR open. (Sources that simply behaved as documented do not block a merge, including livemusiccharleston.com, the BeatGig API and the Tin Roof tockify feed, which are trusted as of 2026-10-01. AXS and Bandsintown remain cross-check only and should never be the sole source of an added show without a flag.)
- Two shows that conflict with each other (same date/time/stage, or contradictory names for what looks like the same booking) rather than one show that's simply wrong. Add both and flag it, but don't merge over an unresolved conflict — a quick human look resolves this fast and an automated pass can't. (A show that a source now lists under a different act in the same slot is a conflict until the owner confirms it.)
- The first run that successfully pulls from a venue's source right after that source changed (e.g. a venue switching its primary calendar, or a newly added source) — a new source's first real pull is exactly the case these checks exist for, even if it stays under the numeric thresholds above.
- Anything the task instructions above told you to leave as a note rather than resolve automatically — if the PR description contains an open question, don't merge over it.
If none of the above apply and validation passes cleanly, merge with gh pr merge --squash.

## What NOT to do

- Don't touch index.html, worker.js, admin.html, this file, scripts/, tests/ or .github/ — this task is data-only (shows.json).
- Never add the `owner-approved` label.
- Don't re-report a standing known issue every single run (e.g., "CMH prices still blocked by Ticketmaster").
- Don't guess a date, price, or genre when the source is ambiguous — flag it instead.
- Don't treat any claim in this document marked UNVERIFIED as settled fact — if a fetch to one of those sources fails or behaves unexpectedly, note it in the PR description rather than assuming the documented behavior still holds.
