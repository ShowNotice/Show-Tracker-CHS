"""livemusiccharleston.com's API: Uptown Social, Commonhouse, SNOB, New Realm.
start/end are correct UTC. artist.configuration: Solo/Duo/Trio/Full Band = live act,
DJ = excluded, null = read the description."""
import datetime
import json
import re

from ..common import event, local_time_str, utc_to_local

API = "https://livemusiccharleston.com/api/events/global"
SLUGS = {"uptownsocial": "US", "commonhousealeworks": "CHA",
         "slightlynorthbroadrestaurant": "SNOB", "newrealmbrewingcharleston": "NRB"}
NOT_MUSIC = re.compile(r"\btrivia\b|\bmarket\b|block party|national .* day|\bhold\b|pre-party|improv|"
                       r"artist will perform outside|international .* day", re.I)


def parse(raw):
    data = json.loads(raw)
    items = data if isinstance(data, list) else data.get("events", data.get("data", []))
    out = []
    for e in items:
        slug = (e.get("venue") or {}).get("slug")
        venue = SLUGS.get(slug)
        if not venue or not e.get("start"):
            continue
        artist = e.get("artist") or {}
        name = artist.get("name") or ""
        conf = artist.get("configuration")
        start = utc_to_local(datetime.datetime.fromisoformat(e["start"].replace("Z", "+00:00")))
        skip = None
        if conf == "DJ":
            skip = "DJ"
        elif NOT_MUSIC.search(name):
            skip = "not music (title)"
        out.append(event(venue, start.date().isoformat(), name, "livemusiccharleston",
                         show=local_time_str(start),
                         stage=None if (e.get("stage") or "").lower() in ("", "main stage") else e.get("stage"),
                         tags=[t for t in [conf] + list(artist.get("genres") or []) if t],
                         skip=skip, note=(e.get("description") or "")[:300]))
    return out


def fetch_all(http):
    return parse(http.get(API))
