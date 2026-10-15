import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import validate_shows as vs  # noqa: E402


def doc(shows, venues=None):
    data = {
        "dataUpdatedAt": "2026-10-15",
        "venues": venues or {"PH": {"name": "Pour House", "site": "https://x.test/", "type": "venue", "color": "#123456"}},
        "shows": shows,
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


SHOW = {"id": "ph-20261101-band", "d": "2026-11-01", "b": "Band", "v": "PH", "sh": "8:00 PM", "p": 10}


class CheckFile(unittest.TestCase):
    def errors(self, shows, **kw):
        return vs.check_file(doc(shows, **kw))[1]

    def test_valid(self):
        self.assertEqual(self.errors([SHOW]), [])

    def test_placeholder_time_rejected(self):
        self.assertTrue(self.errors([{**SHOW, "sh": "TBA"}]))
        self.assertTrue(self.errors([{**SHOW, "dr": "see ticket link"}]))

    def test_whole_float_price_rejected(self):
        self.assertTrue(self.errors([{**SHOW, "p": 10.0}]))
        self.assertEqual(self.errors([{**SHOW, "p": 29.5}]), [])

    def test_unknown_venue_and_field(self):
        self.assertTrue(self.errors([{**SHOW, "v": "XX"}]))
        self.assertTrue(self.errors([{**SHOW, "price": 10}]))

    def test_duplicates(self):
        self.assertTrue(self.errors([SHOW, {**SHOW, "id": "other"}]))
        self.assertTrue(self.errors([{**SHOW, "id": "a"}, {**SHOW, "b": "Other", "id": "a"}]))

    def test_id_required(self):
        self.assertTrue(self.errors([{k: v for k, v in SHOW.items() if k != "id"}]))

    def test_do_not_add(self):
        data = json.loads(doc([SHOW]))
        entries = [{"v": "PH", "d": "2026-11-01", "b": "Band", "reason": "owner: not playing"}]
        self.assertEqual(vs.blocked_keys(data, entries), [("PH", "2026-11-01", "Band")])
        self.assertEqual(vs.blocked_keys(data, [{**entries[0], "d": "2026-11-02"}]), [])

    def test_empty_link_rejected(self):
        self.assertTrue(self.errors([{**SHOW, "u": ""}]))

    def test_flag_needs_flagged_date(self):
        self.assertTrue(self.errors([{**SHOW, "flag": "open question"}]))
        self.assertTrue(self.errors([{**SHOW, "flagged": "2026-10-15"}]))
        self.assertTrue(self.errors([{**SHOW, "flag": "q", "flagged": "10/15"}]))
        self.assertEqual(self.errors([{**SHOW, "flag": "q", "flagged": "2026-10-15"}]), [])

    def test_noncanonical_format(self):
        raw = doc([SHOW]).replace("  ", "    ")
        self.assertTrue(vs.check_file(raw)[1])


class Review(unittest.TestCase):
    def base(self, shows):
        return json.loads(doc(shows))

    def test_confirmed_removal_flagged(self):
        old = [{**SHOW, "confirmed": "2026-10-15"}]
        items, _ = vs.review_items(self.base([]), self.base(old), "2026-10-15")
        self.assertTrue(any("owner confirmed" in i for i in items))

    def test_pruning_past_shows_needs_no_review(self):
        old = [{**SHOW, "b": f"B{i}", "id": f"b{i}", "d": "2026-09-01", "confirmed": "2026-08-01"} for i in range(60)]
        items, _ = vs.review_items(self.base([]), self.base(old), "2026-10-15")
        self.assertEqual(items, [])

    def test_mass_removal_flagged(self):
        old = [{**SHOW, "b": f"B{i}", "id": f"b{i}"} for i in range(10)]
        items, _ = vs.review_items(self.base(old[:2]), self.base(old), "2026-10-15")
        self.assertTrue(any("removed" in i for i in items))

    def test_small_change_ok(self):
        old = [{**SHOW, "b": f"B{i}", "id": f"b{i}"} for i in range(10)]
        items, _ = vs.review_items(self.base(old[1:]), self.base(old), "2026-10-15")
        self.assertEqual(items, [])

    def test_date_move_flagged_via_id(self):
        old = [{**SHOW, "id": "ph-x"}]
        new = [{**SHOW, "id": "ph-x", "d": "2027-01-15"}]
        items, counts = vs.review_items(self.base(new), self.base(old), "2026-10-15")
        self.assertEqual(counts["moved"], 1)
        self.assertTrue(any("date moved" in i for i in items))

    def test_price_outlier_flagged(self):
        items, _ = vs.review_items(self.base([{**SHOW, "p": 250}]), self.base([]), "2026-10-15")
        self.assertTrue(any("outside" in i for i in items))


class Prune(unittest.TestCase):
    def test_keeps_last_five_days_and_multi_day(self):
        import prune_past
        shows = [{**SHOW, "id": "a", "b": "A", "d": "2026-10-10"},          # 5 days ago: kept
                 {**SHOW, "id": "b", "b": "B", "d": "2026-10-09"},          # 6 days ago: removed
                 {**SHOW, "id": "c", "b": "C", "d": "2026-10-01", "e": "2026-10-12"},  # ended 3 days ago
                 {**SHOW, "id": "d", "b": "D", "d": "2026-11-01"}]
        data = {"shows": shows}
        self.assertEqual(prune_past.prune(data, "2026-10-15"), 1)
        self.assertEqual([s["id"] for s in data["shows"]], ["a", "c", "d"])


if __name__ == "__main__":
    unittest.main()
