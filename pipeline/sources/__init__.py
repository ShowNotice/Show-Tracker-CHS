"""Registry of sources. Each fetch(http, wants_details) returns
{"events": [...], "complete": bool}. "complete" means the source lists every upcoming
show it has, so a row missing from it (within its date range) is no longer listed.

Venues without a fetcher here are handled by hand per pipeline/INSTRUCTIONS.md:
REF (Refinery — hand-built Wix page), CJF, RFP (festival sites), CHR (manual entry).
"""
import datetime

from . import lmc, misc, ncc, pourhouse, squarespace, tmcards, tockify, windjammer


def _lmc_for(venue):
    def fetch(http, wants_details, _cache={}):
        if "events" not in _cache:
            _cache["events"] = lmc.fetch_all(http)
        return {"events": [e for e in _cache["events"] if e["venue"] == venue], "complete": True}
    return fetch


def _efm(http, wants_details):
    today = datetime.date.today().isoformat()
    return {"events": squarespace.parse_efm(http.get(squarespace.EFM_URL), today), "complete": False}


# venue code -> (fetch function, description)
SOURCES = {
    "PH": (pourhouse.fetch, "charlestonpourhouse.com/events/list/ + event pages"),
    "MF": (tmcards.fetch_venue("MF"), "musicfarm.com/calendar/"),
    "CMH": (tmcards.fetch_venue("CMH"), "charlestonmusichall.com/calendar/"),
    "NCC": (ncc.fetch, "northcharlestoncoliseumpac.com/events + Load More endpoint + detail pages"),
    "TR": (tockify.fetch, "tockify ICS feed"),
    "RA": (squarespace.fetch_ra, "theroyalamerican.com/schedule"),
    "WJ": (windjammer.fetch, "the-windjammer.com/events/ + events-sitemap.xml + event pages"),
    "FD": (misc.fetch_firefly, "fireflydistillery.com/upcoming-shows/"),
    "GC": (misc.fetch_gaillard, "gaillardcenter.org/buy-tickets/"),
    "C1S": (misc.fetch_creditone, "creditonestadium.com/events/"),
    "US": (_lmc_for("US"), "livemusiccharleston.com API"),
    "CHA": (_lmc_for("CHA"), "livemusiccharleston.com API"),
    "SNOB": (_lmc_for("SNOB"), "livemusiccharleston.com API"),
    "NRB": (_lmc_for("NRB"), "livemusiccharleston.com API"),
}

# Cross-check sources: listed for comparison only, never used to remove rows.
CROSS_CHECKS = {
    "earformusic": (_efm, "earformusic.com/events (promoter for FD, many REF and some GC shows)"),
}
