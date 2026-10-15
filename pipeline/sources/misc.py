"""Smaller single-page sources: Firefly Distillery (FD), Gaillard Center (GC),
Credit One Stadium (C1S)."""
import datetime
import re

from ..common import event, find_date, links, local_time_str, parse_time, text, utc_to_local

FIREFLY = "https://fireflydistillery.com/upcoming-shows/"
GAILLARD = "https://gaillardcenter.org/buy-tickets/"
CREDITONE = "https://creditonestadium.com/events/"

GC_INCLUDE = {"music", "jazz", "country"}
GC_EXCLUDE = {"classical-cso", "broadway", "theater", "comedy", "dance", "authors-lectures"}


def parse_firefly(html):
    body = text(html)
    out = []
    for m in re.finditer(r"((?:January|February|March|April|May|June|July|August|September|October|November|"
                         r"December) \d{1,2}, 20\d\d) Live at Firefly with (.*?) Learn More", body):
        out.append(event("FD", find_date(m.group(1)), re.sub(r"\s+[–-]\s+.*$", "", m.group(2)), "firefly"))
    pages = links(html, r"https://fireflydistillery\.com/event/[^\"]+")
    for e, p in zip(out, pages):
        e["page"] = p
    return out


def parse_gaillard(html):
    out = []
    for blk in re.split(r'(?=<div class="column[^"]*performance-item)', html)[1:]:
        ts = re.search(r'data-timestamp="(\d+)"', blk)
        cats = (re.search(r'data-categories="([^"]*)"', blk) or [None, ""])[1].split()
        title = text((re.search(r'performance-item__title">(.*?)</div>', blk, re.S) or [None, ""])[1])
        tm = text((re.search(r'performance-item__time">(.*?)</div>', blk, re.S) or [None, ""])[1])
        where = text((re.search(r'performance-item__venue">(.*?)</div>', blk, re.S) or [None, ""])[1])
        page = (re.search(r'href="(https://gaillardcenter\.org/events/[^"]+)"', blk) or [None, None])[1]
        if not (ts and title):
            continue
        local = utc_to_local(datetime.datetime.fromtimestamp(int(ts.group(1)), datetime.timezone.utc))
        skip = None
        if re.match(r"CSO\b|Charleston Symphony", title):
            skip = "classical/CSO (title)"
        elif not cats:
            cats = ["uncategorized"]   # e.g. Shakey Graves — read the event page
        elif not set(cats) & GC_INCLUDE and cats != ["uncategorized"]:
            skip = "category: " + ", ".join(cats)
        elif set(cats) & {"classical-cso"} and not skip:
            skip = "classical/CSO"
        if "Gaillard" not in where and "95 Calhoun" not in where:
            skip = skip or f"elsewhere ({where})"
        out.append(event("GC", local.date().isoformat(), title, "gaillard",
                         show=parse_time(tm) or local_time_str(local), page=page, url=page, tags=cats, skip=skip))
    return out


def parse_creditone(html):
    out, seen = [], set()
    for page, date_s, title in re.findall(
            r'<a href="(https://creditonestadium\.com/event/[^"]+)"[^>]*class="item">.*?'
            r'<span class="date">(.*?)</span>\s*<p class="title">(.*?)</p>', html, re.S):
        if page in seen:
            continue
        seen.add(page)
        date = find_date(text(date_s).replace("Oct.", "Oct").replace("Sept.", "Sep"))
        out.append(event("C1S", date, text(title), "creditone", page=page, url=page))
    return out


def fetch_firefly(http, wants_details):
    return {"events": parse_firefly(http.get(FIREFLY)), "complete": True}


def fetch_gaillard(http, wants_details):
    return {"events": parse_gaillard(http.get(GAILLARD)), "complete": True}


def fetch_creditone(http, wants_details):
    events = parse_creditone(http.get(CREDITONE))
    for e in events:
        if wants_details(e):
            tm = links(http.get(e["page"]), r"https://www\.ticketmaster\.com/[^\"]+")
            if tm:
                e["url"] = tm[0]
    return {"events": events, "complete": True}
