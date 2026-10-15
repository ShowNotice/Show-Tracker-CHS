"""Music Farm (MF) and Charleston Music Hall (CMH): one calendar page each, made of
<article class="event-card …"> blocks tagged with Ticketmaster classifications."""
import re

from ..common import doors_and_show, event, find_date, text

SITES = {"MF": "https://musicfarm.com/calendar/", "CMH": "https://charlestonmusichall.com/calendar/"}
EXCLUDE = {"comedy", "dance", "food-drink", "sc-ballet", "lecture-seminar", "charleston-comedy-week",
           "family", "children-s-theatre", "magic", "miscellaneous"}
MUSIC = {"music", "rock", "pop", "country", "hip-hop-rap", "r-b", "jazz", "blues", "folk", "alternative",
         "metal", "punk", "reggae", "soul", "indie", "christian", "electronic", "latin", "trap", "bluegrass",
         "americana", "world", "dance-electronic"}


def parse(html, venue, today=None):
    out = []
    for a in re.findall(r'<article class="event-card.*?</article>', html, re.S):
        cls = re.search(r'class="event-card([^"]*)"', a).group(1)
        cats = re.findall(r"tm_classifications-([a-z0-9-]+)", cls)
        body = text(a)
        if not body:
            continue
        date = find_date(body, today)
        alt = (re.search(r'alt="([^"]*)"', a) or [None, ""])[1]
        title = re.split(r" at (?:The )?(?:Charleston Music Hall|Music Farm)", alt)[0] if alt else ""
        if not title:
            title = (re.search(r"<h3[^>]*>(.*?)</h3>", a, re.S) or [None, ""])[1]
        page = (re.search(r'href="(https://[^"]+/event/[^"]+)"', a) or [None, None])[1]
        tix = (re.search(r'href="(https://(?:www\.)?(?:ticketmaster|livenation|boldtypetickets|axs|etix|[a-z.]*tickets?)[^"]*)"', a) or [None, None])[1]
        doors, show = doors_and_show(body)
        status = None
        low = body.lower()
        if "sold out" in low:
            status = "sold out"
        elif "low tix" in low:
            status = "low tix"
        elif "on sale soon" in low:
            status = "on sale soon"
        skip = None
        if re.match(r"\s*cancell?ed", title, re.I) or "CANCELLED" in title.upper()[:12]:
            skip, status = "cancelled", "cancelled"
        elif set(cats) & EXCLUDE and not (set(cats) & MUSIC - {"pop"}):
            skip = "category: " + ", ".join(sorted(set(cats) & EXCLUDE))
        if not date or not title:
            continue
        out.append(event(venue, date, title, f"{venue.lower()}-calendar", doors=doors, show=show,
                         url=tix or page, page=page, tags=cats, status=status, skip=skip))
    return out


def fetch_venue(venue):
    def fetch(http, wants_details):
        return {"events": parse(http.get(SITES[venue]), venue), "complete": True}
    return fetch
