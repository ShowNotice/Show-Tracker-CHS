"""Charleston Pour House (PH): The Events Calendar list pages + event pages.

/shows/ only covers ~6 weeks and its pagination uses a robots-blocked query string,
so this crawls the path-based /events/list/page/N/ pages (robots-allowed, Crawl-delay 3)
until one is empty. Event pages are fetched only for shows the caller asks about.
"""
import json
import re

from ..common import doors_and_show, event, local_time_str, prices, text
import datetime

VENUE = "PH"
LIST = "https://charlestonpourhouse.com/events/list/"
MAX_PAGES = 30
SKIP_WORDS = re.compile(r"\b(market|closed|drum circle|oyster roast)\b", re.I)


def parse_list(html):
    out = []
    for a in re.findall(r'<article\s+class="tribe-events-calendar-list__event\s.*?</article>', html, re.S):
        date = (re.search(r'datetime="(\d{4}-\d\d-\d\d)"', a) or [None, None])[1]
        title = text((re.search(r'event-title-link[^>]*>(.*?)</a>', a, re.S) or [None, ""])[1])
        page = (re.search(r'<h4.*?href="([^"]+)"', a, re.S) or [None, None])[1]
        stage = text((re.search(r'event-stage-tag--[^"]*">(.*?)</div>', a, re.S) or [None, ""])[1])
        sup = text((re.search(r'event-supporting-artists">(.*?)</div>', a, re.S) or [None, ""])[1])
        genre = text((re.search(r'event-genre">(.*?)</div>', a, re.S) or [None, ""])[1])
        tix = (re.search(r'href="([^"]+)"[^>]*>GET TICKETS', a) or [None, None])[1]
        if not date or not title:
            continue
        skip = None
        if SKIP_WORDS.search(title) or re.search(r"\bmarket\b", genre, re.I):
            skip = "market/closed/kids/food event"
        out.append(event(VENUE, date, title, "pourhouse-list", openers=sup, stage=stage, page=page,
                         url=tix or page, tags=[g.strip() for g in genre.split(",") if g.strip()], skip=skip))
    return out


def parse_event_page(html):
    """Times and prices from an event page's JSON-LD and description text."""
    info = {}
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            j = json.loads(m)
        except ValueError:
            continue
        j = j[0] if isinstance(j, list) and j else j
        if isinstance(j, dict) and j.get("@type") == "Event":
            sd = j.get("startDate")
            if sd:
                dt = datetime.datetime.fromisoformat(sd)
                info["show"] = local_time_str(dt)   # offset is correct Eastern time
                info["date"] = dt.date().isoformat()
            if j.get("eventStatus", "").endswith("EventCancelled"):
                info["status"] = "cancelled"
    i = html.find("tribe-events-single-event-description")
    desc = text(html[i:i + 4000]) if i >= 0 else ""
    doors, show = doors_and_show(desc)
    if doors:
        info["doors"] = doors
    if show and "show" not in info:
        info["show"] = show
    adv, dos = prices(desc[:600])
    if adv is not None:
        info["price"] = adv
    if dos is not None:
        info["price_dos"] = dos
    return info


def fetch(http, wants_details):
    events = []
    for n in range(1, MAX_PAGES + 1):
        url = LIST if n == 1 else f"{LIST}page/{n}/"
        page = parse_list(http.get(url))
        if not page:
            break
        events.extend(page)
    for e in events:
        if e.get("page") and not e.get("skip") and wants_details(e):
            e.update(parse_event_page(http.get(e["page"])))
    return {"events": events, "complete": True}
