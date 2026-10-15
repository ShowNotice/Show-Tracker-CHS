"""Parser and comparison tests against trimmed copies of real venue pages (2026-10-15)."""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline import common  # noqa: E402
from pipeline.compare import compare, same_act  # noqa: E402
from pipeline.sources import lmc, misc, ncc, pourhouse, squarespace, tmcards, tockify, windjammer  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures")
TODAY = datetime.date(2026, 10, 15)


def fx(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


class Helpers(unittest.TestCase):
    def test_doors_and_show(self):
        self.assertEqual(common.doors_and_show("Doors at 9:00 pm. Show at 9:30 pm."), ("9:00 PM", "9:30 PM"))
        self.assertEqual(common.doors_and_show("5pm doors / 6:30pm show"), ("5:00 PM", "6:30 PM"))
        self.assertEqual(common.doors_and_show("Doors: 7:30 pm | Show: 8:00 pm"), ("7:30 PM", "8:00 PM"))
        self.assertEqual(common.doors_and_show("11:30am doors / 12:00pm show"), ("11:30 AM", "12:00 PM"))

    def test_prices(self):
        self.assertEqual(common.prices("$15 advance / $20 day of show"), (15, 20))
        self.assertEqual(common.prices("$40 Advanced / $40 Day of Show"), (40, None))
        self.assertEqual(common.prices("$10 at the door"), (10, None))
        self.assertEqual(common.prices("$18 – 20"), (18, 20))
        self.assertEqual(common.prices("FREE"), (0, None))

    def test_month_day_rolls_year(self):
        self.assertEqual(common.month_day("January", 9, today=TODAY), "2027-01-09")
        self.assertEqual(common.month_day("October", 16, today=TODAY), "2026-10-16")


class Parsers(unittest.TestCase):
    def test_pourhouse(self):
        evs = pourhouse.parse_list(fx("pourhouse_list.html"))
        self.assertEqual(evs[0]["title"], "LaMP")
        self.assertEqual(evs[0]["stage"], "Main Stage")
        self.assertTrue(evs[0]["url"].startswith("https://aftontickets.com/"))
        info = pourhouse.parse_event_page(fx("pourhouse_event.html"))
        self.assertEqual((info["doors"], info["show"], info["price"]), ("8:00 PM", "9:00 PM", 20))

    def test_tmcards(self):
        evs = tmcards.parse(fx("mf_calendar.html"), "MF", today=TODAY)
        self.assertTrue(evs and all(e["date"] >= "2026-10-15" for e in evs))
        self.assertTrue(any(e.get("show") for e in evs))
        cmh = tmcards.parse(fx("cmh_calendar.html"), "CMH", today=TODAY)
        comedy = [e for e in cmh if "comedy" in e.get("tags", [])]
        self.assertTrue(comedy and all(e.get("skip") for e in comedy))

    def test_ncc(self):
        evs = ncc.parse_items(fx("ncc_list.html"), today=TODAY)
        self.assertTrue(evs)
        self.assertTrue(any(e.get("skip") for e in evs if "Stingrays" in e["title"]))
        d = ncc.parse_detail(fx("ncc_detail.html"))
        self.assertNotIn("skip", d)   # KC & The Sunshine Band: a concert
        self.assertEqual(ncc.parse_detail("<p>Event Details Actor and comedian Tom Segura is one of ...</p>")["skip"],
                         "comedy (detail page)")
        self.assertEqual((d["doors"], d["show"]), ("6:30 PM", "7:30 PM"))
        self.assertIn("ticketmaster.com", d["url"])

    def test_tockify(self):
        evs = tockify.parse(fx("tinroof.ics"))
        lee = next(e for e in evs if e["title"].startswith("Lee Wilder"))
        self.assertEqual((lee["date"], lee["doors"], lee["show"], lee["price"]), ("2026-10-15", "7:30 PM", "8:30 PM", 10))
        self.assertTrue(all(e.get("skip") for e in evs if "Karaoke" in e["title"]))

    def test_lmc(self):
        evs = lmc.parse(fx("lmc.json"))
        self.assertTrue(evs and all(e["venue"] in ("US", "CHA") for e in evs))   # untracked slugs dropped
        self.assertTrue(all(e.get("skip") == "DJ" for e in evs if "DJ" in e.get("tags", [])))

    def test_royalamerican(self):
        evs = squarespace.parse_ra(fx("royalamerican.html"))
        self.assertTrue(evs and evs[0]["date"] and evs[0]["title"])

    def test_earformusic_keeps_upcoming_only(self):
        evs = squarespace.parse_efm(fx("earformusic.html"), "2026-10-15")
        self.assertTrue(evs and all(e["date"] >= "2026-10-15" for e in evs))
        self.assertTrue(all(" at " not in e["title"] for e in evs))

    def test_windjammer(self):
        evs = windjammer.parse_list(fx("windjammer_list.html"))
        self.assertEqual(evs[0]["title"], "FlashMob")
        self.assertEqual(evs[0]["stage"], "Inside Stage")
        e = windjammer.parse_event_page(fx("windjammer_event.html"), "x")
        self.assertEqual((e["date"], e["doors"], e["show"], e["price"]), ("2026-10-16", "9:00 PM", "9:30 PM", 10))
        xml = ("<urlset><url><loc>https://the-windjammer.com/event/a/</loc><lastmod>2026-10-01</lastmod></url>"
               "<url><loc>https://the-windjammer.com/event/b/</loc><lastmod>2025-01-01</lastmod></url></urlset>")
        self.assertEqual(windjammer.parse_sitemap(xml, "2026-06-01"), ["https://the-windjammer.com/event/a/"])

    def test_firefly(self):
        evs = misc.parse_firefly(fx("firefly.html"))
        self.assertEqual([e["date"] for e in evs], ["2026-11-14", "2027-04-24"])
        self.assertEqual(evs[0]["title"], "Hudson Westbrook")

    def test_gaillard(self):
        evs = misc.parse_gaillard(fx("gaillard.html"))
        self.assertTrue(evs)
        for e in evs:
            if "comedy" in e["tags"]:
                self.assertTrue(e.get("skip"))
            if "jazz" in e["tags"]:
                self.assertFalse(e.get("skip"))

    def test_gaillard_uncategorized_is_kept(self):
        blk = ('<div class="column small-12 performance-item" data-timestamp="1796511600" data-categories="">'
               '<div class="performance-item__title"> Shakey Graves</div>'
               '<div class="text-accent performance-item__time">7:30 PM</div>'
               '<div class="text-accent performance-item__venue">Charleston Gaillard Center, 95 Calhoun St.</div>'
               '<a href="https://gaillardcenter.org/events/shakey-graves/">Learn More</a></div>')
        e = misc.parse_gaillard(blk)[0]
        self.assertFalse(e.get("skip"))
        self.assertEqual(e["tags"], ["uncategorized"])

    def test_creditone(self):
        evs = misc.parse_creditone(fx("creditone.html"))
        self.assertEqual(evs[0]["date"], "2026-10-17")


class Compare(unittest.TestCase):
    ROWS = [
        {"d": "2026-11-13", "b": "TAUK", "v": "PH", "sh": "9:00 PM"},
        {"d": "2026-11-20", "b": "Old Show", "v": "PH"},
        {"d": "2026-09-26", "b": "Travis Tritt", "v": "PH"},
    ]

    def test_same_act(self):
        self.assertTrue(same_act("Lee Wilder", "Lee Wilder / Moonswimmer"))
        self.assertTrue(same_act("Hudson Westbrook — The Hits Me Tour", "Hudson Westbrook"))
        self.assertTrue(same_act("TAUK", "Tauk + Les Tauk"))
        self.assertFalse(same_act("Moody Bridge", "Grayson Little"))

    def test_compare(self):
        evs = [
            common.event("PH", "2026-11-13", "Tuak + lespecial", "t", show="9:00 PM"),
            common.event("PH", "2026-11-14", "Travis Tritt", "t"),
            common.event("PH", "2026-11-21", "Brand New", "t", show="8:00 PM"),
            common.event("PH", "2026-11-22", "Kids Drum Circle", "t", skip="kids"),
        ]
        c = compare(self.ROWS, "PH", evs, True, "2026-10-15")
        # The Travis Tritt row is dated in the past, so its new date shows up as new.
        self.assertEqual([e["title"] for e in c["new"]], ["Travis Tritt", "Brand New"])
        self.assertEqual([e["title"] for e in c["skipped_new"]], ["Kids Drum Circle"])
        self.assertEqual([r["b"] for r in c["missing"]], ["Old Show"])
        self.assertEqual(c["date_changes"], [])

    def test_do_not_add_and_confirmed(self):
        rows = [{"d": "2026-11-20", "b": "Kept", "v": "PH", "confirmed": "2026-10-15"}]
        evs = [common.event("PH", "2026-11-21", "Grayson Little", "t"), common.event("PH", "2026-11-22", "Other", "t")]
        dna = [{"v": "PH", "d": "2026-11-21", "b": "Grayson Little", "reason": "not playing"}]
        c = compare(rows, "PH", evs, True, "2026-10-15", do_not_add=dna)
        self.assertEqual([e["title"] for e in c["new"]], ["Other"])
        self.assertEqual(c["skipped_new"][0]["skip"], "owner: not playing")
        self.assertEqual(c["missing"], [])
        self.assertEqual([r["b"] for r in c["confirmed_unlisted"]], ["Kept"])

    def test_partial_source_never_reports_missing(self):
        c = compare(self.ROWS, "PH", [common.event("PH", "2026-11-21", "Brand New", "t")], False, "2026-10-15")
        self.assertEqual(c["missing"], [])


if __name__ == "__main__":
    unittest.main()
