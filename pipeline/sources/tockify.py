"""Charleston Tin Roof (TR): the tockify ICS feed. DTSTART is correct UTC; door/show
times and prices are usually in SUMMARY ("Door @ 7. Show @ 8. $10 21+", always PM)."""
import datetime
import re
from collections import Counter

from ..common import event, norm, prices, utc_to_local, local_time_str

VENUE = "TR"
FEED = "https://tockify.com/api/feeds/ics/tinroofschedule"
NOT_MUSIC = re.compile(r"private party|comedy|karaoke|open mic|trivia|deep crates|bingo|screening", re.I)


def _pm(h):
    return f"{int(h)}:00 PM" if 1 <= int(h) <= 12 else None


def parse(ics):
    raw = ics.replace("\r\n ", "").replace("\n ", "").replace("\r\n", "\n")
    blocks = raw.split("BEGIN:VEVENT")[1:]
    rows = []
    for b in blocks:
        def g(k):
            m = re.search(r"^" + k + r"[^:\n]*:(.*)$", b, re.M)
            return m.group(1).strip() if m else ""
        rows.append((g("DTSTART"), g("SUMMARY").replace("\\,", ",").replace("\\;", ";"), g("URL")))
    repeats = Counter(norm(re.split(r"\.\s|Door", s)[0]) for _, s, _ in rows)
    out = []
    for ds, summary, url in rows:
        if not ds:
            continue
        if ds.endswith("Z"):
            local = utc_to_local(datetime.datetime.strptime(ds[:15], "%Y%m%dT%H%M%S"))
        elif "T" in ds:
            local = datetime.datetime.strptime(ds[:15], "%Y%m%dT%H%M%S")
        else:
            local = datetime.datetime.strptime(ds[:8], "%Y%m%d")
        title = re.split(r"\.\s+(?=Door|Show)|\s+Door\s*@", summary)[0].strip(" .")
        door = re.search(r"Doors?\s*@\s*(\d{1,2})(?::(\d\d))?", summary, re.I)
        show = re.search(r"Show\s*@\s*(\d{1,2})(?::(\d\d))?", summary, re.I)
        doors_t = f"{int(door.group(1))}:{door.group(2) or '00'} PM" if door else None
        show_t = f"{int(show.group(1))}:{show.group(2) or '00'} PM" if show else None
        if not show_t and "T" in ds:
            show_t = local_time_str(local)
        adv, dos = prices(summary)
        skip = None
        if repeats[norm(re.split(r"\.\s|Door", summary)[0])] > 2:
            skip = "recurring filler (title repeats more than twice)"
        elif NOT_MUSIC.search(summary):
            skip = "not music (title)"
        out.append(event(VENUE, local.date().isoformat(), title, "tockify", doors=doors_t, show=show_t,
                         price=adv, price_dos=dos, url=url, skip=skip, note=summary))
    return out


def fetch(http, wants_details):
    return {"events": parse(http.get(FEED)), "complete": True}
