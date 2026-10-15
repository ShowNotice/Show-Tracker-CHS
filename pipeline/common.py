"""Shared parsing helpers and the Event shape every source returns."""
import datetime
import html as htmllib
import re

try:
    from zoneinfo import ZoneInfo
    EASTERN = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover - only on systems without a tz database
    EASTERN = None

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS["sept"] = 9


def event(venue, date, title, source, **fields):
    """One candidate show. Unknown fields are simply left out.

    Fields: openers, stage, doors, show ("8:00 PM"), price, price_dos, url (ticket or
    event link), page (the venue's event page), tags (list), status ("sold out",
    "low tix", "on sale soon", "cancelled", "rescheduled"), skip (reason this looks
    out of scope), note.
    """
    e = {"venue": venue, "date": date, "title": clean(title), "source": source}
    for k, v in fields.items():
        if v not in (None, "", [], ()):
            e[k] = clean(v) if isinstance(v, str) else v
    return e


def clean(s):
    s = htmllib.unescape(s or "")
    s = s.replace(" ", " ").replace("’", "'")
    return re.sub(r"\s+", " ", s).strip()


def text(html_fragment):
    """Visible text of an HTML fragment (scripts and styles dropped)."""
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_fragment or "", flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    return clean(re.sub(r"<[^>]+>", " ", t))


def norm(s):
    """Lowercase letters and digits only, for fuzzy name matching."""
    s = clean(s).lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", s)


TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\.?(?![a-z])", re.I)


def fmt_time(h, m, ap):
    h = int(h)
    if not 1 <= h <= 12:
        return None
    return f"{h}:{int(m or 0):02d} {ap.upper()}M"


def parse_time(s):
    """'8pm', '8:00 pm', '7:30PM', '12 p.m.' -> '8:00 PM' (None if no time)."""
    m = TIME_RE.search(s or "")
    return fmt_time(*m.groups()) if m else None


def doors_and_show(s):
    """Find doors/show times in text like '5pm doors / 6:30pm show',
    'Doors: 7:30 pm | Show: 8:00 pm', 'Doors at 9:00 pm. Show at 9:30 pm.',
    'Door @ 7. Show @ 8.' (the last form has no am/pm; caller decides)."""
    s = s or ""
    t = r"(\d{1,2}(?::\d{2})?\s*[ap]\.?\s*m\.?)"
    # Label-first ("Doors at 9:00 pm", "Show: 8:00 pm") is checked before time-first
    # ("5pm doors / 6:30pm show"): in "Doors at 9:00 pm. Show at 9:30 pm." the
    # time-first pattern would pair 9:00 with "Show".
    doors = (re.search(r"\bdoors?\s*(?:open)?\s*(?:at|@|:)?\s*" + t, s, re.I) or re.search(t + r"\s*doors", s, re.I))
    show = (re.search(r"\bshow(?:time)?s?\s*(?:starts)?\s*(?:at|@|:)?\s*" + t, s, re.I) or re.search(t + r"\s*show", s, re.I))
    return (parse_time(doors.group(1)) if doors else None, parse_time(show.group(1)) if show else None)


PRICE_RE = re.compile(r"\$\s?(\d+(?:\.\d{2})?)")


def money(x):
    v = float(x)
    return int(v) if v == int(v) else v


def prices(s):
    """Advance and day-of prices from text like '$15 advance / $20 day of show',
    '$10 at the door', '$18 – 20', 'FREE'. Returns (advance, day_of)."""
    s = s or ""
    adv = re.search(r"\$\s?(\d+(?:\.\d{2})?)\s*(?:in\s*)?adv", s, re.I)
    dos = re.search(r"\$\s?(\d+(?:\.\d{2})?)\s*(?:on\s*the\s*)?(?:day\s*of|dos|door|at\s*the\s*door|@\s*the\s*door)", s, re.I)
    if adv or dos:
        a = money(adv.group(1)) if adv else (money(dos.group(1)) if dos else None)
        d = money(dos.group(1)) if dos else None
        return a, (d if d is not None and d != a else None)
    rng = re.search(r"\$?\s?(\d+(?:\.\d{2})?)\s*[–-]\s*\$?\s?(\d+(?:\.\d{2})?)", s)
    if rng and "$" in s[max(0, rng.start() - 1):rng.end()]:
        return money(rng.group(1)), money(rng.group(2))
    one = PRICE_RE.search(s)
    if one:
        return money(one.group(1)), None
    if re.search(r"\bfree\b", s, re.I):
        return 0, None
    return None, None


def month_day(month_name, day, year=None, today=None):
    """Date from a month name and day. Without a year, picks the next occurrence on or
    after today minus a week (so a list of upcoming events maps to the right year)."""
    mo = MONTHS.get(month_name.lower().rstrip("."))
    if not mo:
        return None
    if year:
        return datetime.date(int(year), mo, int(day)).isoformat()
    today = today or datetime.date.today()
    cand = datetime.date(today.year, mo, int(day))
    if cand < today - datetime.timedelta(days=7):
        cand = datetime.date(today.year + 1, mo, int(day))
    return cand.isoformat()


DATE_WORDS = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(20\d\d)?", re.I)


def find_date(s, today=None):
    m = DATE_WORDS.search(s or "")
    return month_day(m.group(1), m.group(2), m.group(3), today) if m else None


def utc_to_local(dt_utc):
    """A naive or aware UTC datetime -> Eastern local datetime."""
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=datetime.timezone.utc)
    if EASTERN is None:
        raise RuntimeError("no time-zone database available")
    return dt_utc.astimezone(EASTERN)


def local_time_str(dt):
    return fmt_time(dt.strftime("%I").lstrip("0") or "12", dt.minute, "a" if dt.hour < 12 else "p")


def links(fragment, pattern):
    return list(dict.fromkeys(re.findall(r'href="(' + pattern + r')"', fragment or "")))
