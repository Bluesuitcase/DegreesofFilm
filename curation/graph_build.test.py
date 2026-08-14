"""Tests for the Degrees corpus builder. Pure logic, no network, no caches needed.

Run:  python curation/graph_build.test.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graph_build as gb  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


def raises(label, fn, needle=""):
    global passed, failed
    try:
        fn()
    except ValueError as e:
        ok = needle in str(e)
        passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
        print(f"{'PASS' if ok else 'FAIL'}  {label}"
              + ("" if ok else f"\n        raised {e!r}, wanted {needle!r} in it"))
        return
    passed, failed = passed, failed + 1
    print(f"FAIL  {label}\n        did not raise")


# A tiny world: two films share Ann; Cid is in one film only (a non-connector);
# film 30 is isolated once Cid is pruned.
FILMS = {10: ("Alpha", 2001), 20: ("The Beta", 1999), 30: ("Gamma", 2010)}
ORDER = [10, 20, 30]
PEOPLE = {
    10: [(1, "Ann Lee", 9.0), (2, "Bo Ray", 3.0)],
    20: [(1, "Ann Lee", 5.0), (2, "Bo Ray", 8.0)],
    30: [(3, "Cid Poe", 7.0)],
}

# --- lever 1: only multi-film people survive ---
check("connector ids drop the one-film person", sorted(gb.connector_ids(PEOPLE)), [1, 2])

# --- people are ordered by their best popularity (Ann 9.0 > Bo 8.0) ---
check("people ranked by max popularity",
      gb.rank_people(PEOPLE, {1, 2}), [(1, "Ann Lee"), (2, "Bo Ray")])
check("rank uses the MAX across credits, not the last seen",
      gb.rank_people({10: [(1, "Ann Lee", 1.0)], 20: [(1, "Ann Lee", 9.0)]}, {1}),
      [(1, "Ann Lee")])

# --- delta-hex round trip ---
check("encode gaps as hex", gb.encode_deltas([0, 3, 4, 20]), "0,3,1,10")
check("decode is the inverse", gb.decode_deltas("0,3,1,10"), [0, 3, 4, 20])
check("empty encodes to empty", gb.encode_deltas([]), "")
check("empty decodes to []", gb.decode_deltas(""), [])
check("encode sorts first", gb.decode_deltas(gb.encode_deltas([9, 2, 7])), [2, 7, 9])
big = list(range(0, 30000, 7))
check("round trip over a wide index range", gb.decode_deltas(gb.encode_deltas(big)), big)

# --- corpus assembly ---
c = gb.build_corpus(ORDER, FILMS, PEOPLE)
check("isolated film dropped once its lone credit is pruned", c["ids"], [10, 20])
check("film labels carry title + year", c["films"], [["Alpha", 2001], ["The Beta", 1999]])
check("people list is names only, rank ordered", c["people"], ["Ann Lee", "Bo Ray"])
check("cast decodes to person indices", [gb.decode_deltas(x) for x in c["cast"]],
      [[0, 1], [0, 1]])
check("film ids are TMDB ids, not array positions", c["ids"][0], 10)
check("version stamped", c["v"], gb.CORPUS_VERSION)
check("valid corpus validates", gb.validate(c), True)

# --- a film whose people are all pruned never reaches the arrays ---
check("no empty cast strings survive", [x for x in c["cast"] if not x], [])

# --- validate is the build-time gate ---
raises("rejects a dangling person index",
       lambda: gb.validate({**c, "cast": ["0,1,5"] + c["cast"][1:]}), "out of range")
raises("rejects mismatched array lengths",
       lambda: gb.validate({**c, "films": c["films"][:1]}), "same length")
raises("rejects duplicate film ids",
       lambda: gb.validate({**c, "ids": [10, 10]}), "duplicate")
raises("rejects an empty cast", lambda: gb.validate({**c, "cast": ["", "0"]}), "empty cast")
raises("rejects a wrong version", lambda: gb.validate({**c, "v": 99}), "version")
raises("rejects a non-connector surviving into the people list",
       lambda: gb.validate({**c, "people": c["people"] + ["Cid Poe"]}), "not connectors")

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
