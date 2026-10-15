"""Squarespace event lists: The Royal American (RA) and Ear For Music (the promoter
behind Firefly's concerts). Read the HTML only — ?format=json is robots-disallowed."""
import re

from ..common import event, links, parse_time, prices, text

RA_URL = "https://www.theroyalamerican.com/schedule"
EFM_URL = "https://www.earformusic.com/events"
EFM_VENUES = {"firefly distillery": "FD", "the refinery": "REF", "the gaillard center": "GC",
              "charleston gaillard center": "GC"}
RA_SKIP = re.compile(r"\bmarket\b|bike night|art binge|ghouls night", re.I)


def articles(html):
    for a in re.findall(r'<article class="eventlist-event.*?</article>', html, re.S):
        date = (re.search(r'datetime="(\d{4}-\d\d-\d\d)"', a) or [None, None])[1]
        title = text((re.search(r'eventlist-title-link[^>]*>(.*?)</a>', a, re.S) or [None, ""])[1])
        start = text((re.search(r'event-time-12hr-start[^>]*>(.*?)</time>', a, re.S) or
                      re.search(r'event-time-12hr[^>]*>(.*?)</time>', a, re.S) or [None, ""])[1])
        venue = text((re.search(r'eventlist-meta-address[^>]*>(.*?)<', a, re.S) or [None, ""])[1])
        page = (re.search(r'href="(/[^"]*events?/[^"]+|/schedule/[^"]+)"', a) or [None, None])[1]
        desc = text((re.search(r'eventlist-description[^>]*>(.*?)</div>\s*</div>', a, re.S) or [None, ""])[1])
        yield a, date, title, start, venue, page, desc


def parse_ra(html):
    out = []
    for a, date, title, start, _, page, desc in articles(html):
        if not date or not title:
            continue
        adv, dos = prices(desc[:400])
        out.append(event("RA", date, title, "royalamerican", show=parse_time(start),
                         price=adv, price_dos=dos, page=("https://www.theroyalamerican.com" + page) if page else None,
                         url=("https://www.theroyalamerican.com" + page) if page else None,
                         skip="market/community event" if RA_SKIP.search(title) else None))
    return out


def parse_efm(html, today):
    """Ear For Music lists past shows too; keep today onward. Its times are a site-wide
    placeholder (6–10 PM), so they're dropped."""
    out = []
    for a, date, title, _, venue, page, _ in articles(html):
        if not date or not title or date < today:
            continue
        code = EFM_VENUES.get(venue.lower().strip())
        if not code:
            continue
        act = re.split(r"\s+at\s+(?:The\s+)?(?:Firefly Distill?ery|Refinery|Gaillard Center|Limbo Lounge)\b", title, flags=re.I)[0]
        tix = links(a, r"https://(?:www\.)?(?:ticketmaster|ticketweb|etix|axs|seetickets|frontgate)[^\"]+")
        out.append(event(code, date, act, "earformusic", url=tix[0] if tix else None,
                         page=("https://www.earformusic.com" + page) if page else None))
    return out


def fetch_ra(http, wants_details):
    return {"events": parse_ra(http.get(RA_URL)), "complete": True}
