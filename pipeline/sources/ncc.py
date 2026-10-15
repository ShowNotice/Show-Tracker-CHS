"""North Charleston Coliseum & PAC (NCC): the list page renders 12 events; its
"Load More Events" button pages the rest from /events/events_ajax/{offset}."""
import json
import re

from ..common import event, links, month_day, parse_time, text

VENUE = "NCC"
LIST = "https://www.northcharlestoncoliseumpac.com/events"
AJAX = ("https://www.northcharlestoncoliseumpac.com/events/events_ajax/{offset}"
        "?category=0&venue=0&team=0&exclude=&per_page=12&came_from_page=event-list-page")
NOT_MUSIC = re.compile(r"stingrays|disney on ice|monster jam|harlem globetrotters|wrestl|pbr\b|graduation|"
                       r"comedy|comedian|cirque|circus|broadway|pops\b|ballet|nutcracker|lucy darling|"
                       r"watch what happens|fan fest|seinfeld|shen yun|legends of laughter|symphony", re.I)


def parse_items(html, today=None):
    out = []
    for blk in re.split(r'<div class="eventItem', html)[1:]:
        page = (re.search(r'href="(https://www\.northcharlestoncoliseumpac\.com/events/detail/[^"]+)"', blk) or [None, None])[1]
        title = (re.search(r'title="More Info for ([^"]+)"', blk) or [None, ""])[1]
        body = text('<div class="eventItem' + blk)
        m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                      r" (\d{1,2})(?: - (\d{1,2}))?(?: / (20\d\d))?", body)
        if not (page and title and m):
            continue
        date = month_day(m.group(1), m.group(2), m.group(4), today)
        end = month_day(m.group(1), m.group(3), m.group(4), today) if m.group(3) else None
        hall = "Performing Arts Center" if "Performing Arts Center" in body else ("Coliseum" if "Coliseum" in body else None)
        hit = NOT_MUSIC.search(title + " " + body[:300])
        skip = None
        if hit:
            word = hit.group(0)
            skip = ("North Charleston POPS! production (orchestral exclusion)" if word.lower() == "pops"
                    else f"not music ({word!r} in listing)")
        e = event(VENUE, date, title, "ncc-list", stage=hall, page=page, skip=skip)
        if end and end != date:
            e["end"] = end
        if "RESCHEDULED" in body.upper():
            e["status"] = "rescheduled"
        out.append(e)
    return out


def parse_detail(html):
    body = text(html)
    info = {}
    starts = re.search(r"Event Starts\s+(\d{1,2}:\d{2}\s*[AP]M)", body, re.I)
    doors = re.search(r"Doors Open\s+(\d{1,2}:\d{2}\s*[AP]M)", body, re.I)
    if starts:
        info["show"] = parse_time(starts.group(1))
    if doors:
        info["doors"] = parse_time(doors.group(1))
    tix = links(html, r"https://www\.ticketmaster\.com/[^\"]+|https://www\.axs\.com/[^\"]+")
    if tix:
        info["url"] = tix[0]
    i = body.find("Event Details")
    desc = body[i:i + 700] if i >= 0 else ""
    if re.search(r"\bcomedian|stand-up|comedy special|\bcomedy\b", desc, re.I):
        info["skip"] = "comedy (detail page)"
    elif re.search(r"\bBroadway\b|the musical\b|Tony Award|live on stage", desc, re.I):
        info["skip"] = "Broadway/theatre (detail page)"
    resched = re.search(r"rescheduled to ([A-Z][a-z]+ \d{1,2})", body)
    if resched:
        info["note"] = "Rescheduled to " + resched.group(1)
    return info


def fetch(http, wants_details):
    events = parse_items(http.get(LIST))
    seen = {e["page"] for e in events}
    offset = 12
    while offset < 600:
        raw = http.get(AJAX.format(offset=offset), headers={"X-Requested-With": "XMLHttpRequest"})
        try:
            raw = json.loads(raw)
        except ValueError:
            pass
        page = [e for e in parse_items(raw if isinstance(raw, str) else str(raw)) if e["page"] not in seen]
        if not page:
            break
        for e in page:
            seen.add(e["page"])
        events.extend(page)
        offset += 12
    for e in events:
        if not e.get("skip") and wants_details(e):
            e.update(parse_detail(http.get(e["page"])))
    return {"events": events, "complete": True}
