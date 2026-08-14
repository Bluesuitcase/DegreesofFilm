"""Tests for the harvest layer. Pure logic only — no network, no caches.

Run:  python curation/harvest.test.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harvest  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


MOVIE = {
    "credits": {
        "cast": [{"id": 1, "name": "Ann Lee", "popularity": 9.0},
                 {"id": 2, "name": " Bo Ray ", "popularity": 3.0},
                 {"id": 3, "name": "No Popularity"}],
        "crew": [{"id": 10, "name": "Dee Cee", "job": "Director", "popularity": 5.0},
                 {"id": 11, "name": "Gaf Fer", "job": "Best Boy", "popularity": 1.0},
                 {"id": 12, "name": "Cam Op", "job": "Editor", "popularity": 2.0}],
    }
}

people = harvest.extract_people(MOVIE)
check("cast and key crew kept, other crew dropped",
      [n for _i, n, _p in people], ["Ann Lee", "Bo Ray", "No Popularity", "Dee Cee", "Cam Op"])
check("names are trimmed", people[1][1], "Bo Ray")
check("missing popularity defaults to 0", people[2][2], 0)
check("cast_top truncates billing",
      [n for _i, n, _p in harvest.extract_people(MOVIE, cast_top=1)],
      ["Ann Lee", "Dee Cee", "Cam Op"])
check("crew jobs are configurable",
      [n for _i, n, _p in harvest.extract_people(MOVIE, cast_top=0, crew_jobs=("Best Boy",))],
      ["Gaf Fer"])
check("a film with no credits yields nothing", harvest.extract_people({}), [])
check("entries without an id are skipped",
      harvest.extract_people({"credits": {"cast": [{"name": "Nameless"}]}}), [])

# The pool floor is the corpus boundary — pin it so a silent edit is caught.
check("pool floor unchanged", (harvest.POOL_MIN_VOTES, harvest.POOL_MIN_AVG), (800, 6.5))

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
