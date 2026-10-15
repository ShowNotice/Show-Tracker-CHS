"""The Windjammer (WJ): /events/ shows only the next 20 events, so the event sitemap
(every event page, with lastmod dates) is read too, and recently changed pages that
aren't on the list are fetched for their dates. Together they're complete."""
import datetime
import re

from ..common import doors_and_show, event, find_date, prices, text

VENUE = "WJ"
LIST = "https://the-windjammer.com/events/"
SITEMAP = "https://the-windjammer.com/events-sitemap.xml"
RECENT_DAYS = 120


def stage_of(title):
    if re.search(r"beach stage", title, re.I):
        return "Beach Stage"
    if re.search(r"inside stage", title, re.I):
        return "Inside Stage"
    return None


def short(title):
    return re.sub(r"\s+on the (?:NÜTRL |NUTRL )?(?:beach|inside) stage.*$", "", title, flags=re.I).strip()


def parse_list(html):
    out = []
    for day, month, year, page, title in re.findall(
            r"<b>\s*(\d{1,2})\s*</b>\s*([A-Za-z]+),\s*(20\d\d).*?<h2><a href=\"([^\"]+)\">(.*?)</a>", html, re.S):
        t = text(title)
        date = find_date(f"{month} {day}, {year}")
        if date:
            out.append(event(VENUE, date, short(t), "windjammer-list", stage=stage_of(t), page=page, url=page))
    return out


def parse_sitemap(xml, since):
    return [loc for loc, lm in re.findall(r"<url>\s*<loc>([^<]+)</loc>\s*(?:<lastmod>([^<]+)</lastmod>)?", xml)
            if "/event/" in loc and (lm or "") >= since]


def parse_event_page(html, url):
    body = text(html)
    m = re.search(r"Buy Tickets Buy Tickets (.*?) (\$[\d.]+|Free|FREE)? ?((?:January|February|March|April|May|June|"
                  r"July|August|September|October|November|December) \d{1,2}, 20\d\d)(.{0,160})", body)
    if not m:
        return None
    title = m.group(1)
    adv, dos = prices(m.group(2) or "")
    doors, show = doors_and_show(m.group(4))
    tix = (re.search(r'href="(https://whollyticket\.com/paymentpage/[^"]+)"', html) or [None, None])[1]
    return event(VENUE, find_date(m.group(3)), short(title), "windjammer-page", stage=stage_of(title),
                 doors=doors, show=show, price=adv, price_dos=dos, page=url, url=tix or url)


def fetch(http, wants_details, today=None):
    today = today or datetime.date.today()
    events = parse_list(http.get(LIST))
    on_list = {e["page"] for e in events}
    since = (today - datetime.timedelta(days=RECENT_DAYS)).isoformat()
    for url in parse_sitemap(http.get(SITEMAP), since):
        if url in on_list:
            continue
        e = parse_event_page(http.get(url), url)
        if e and e["date"] and e["date"] >= today.isoformat():
            events.append(e)
    # Times and prices for the list's own events come from their pages.
    for e in events:
        if e["source"] == "windjammer-list" and wants_details(e):
            d = parse_event_page(http.get(e["page"]), e["page"])
            if d:
                for k in ("doors", "show", "price", "price_dos", "url"):
                    if k in d:
                        e[k] = d[k]
    return {"events": events, "complete": True}
