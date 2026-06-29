"""Tests for the rung-ordering data layer. Pure logic, no network/key.

Run:  python curation/build_rungs.test.py
Prints PASS/FAIL lines; exits non-zero on any failure (mirrors the JS tests).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_rungs import order_rungs, build_puzzle, order_cast  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


def roles(rungs):
    return [r["role"] for r in rungs]


def first_answer(rung):
    return rung["answers"][0]


# A synthetic film: billing order deliberately disagrees with popularity so the
# tiebreak/sort behaviour is observable. Lead Two has the HIGHEST popularity but
# is billed 2nd; a popularity sort would wrongly float it (and Support B) up.
MOVIE = {"title": "Test Film", "original_title": "Pelicula de Prueba"}
CREDITS = {
    "cast": [
        {"id": 1, "name": "Lead One",  "order": 0, "popularity": 2.0, "character": "Hero"},
        {"id": 2, "name": "Lead Two",  "order": 1, "popularity": 9.0, "character": "Villain"},
        {"id": 3, "name": "Support A", "order": 2, "popularity": 1.0, "character": "Friend"},
        {"id": 4, "name": "Support B", "order": 3, "popularity": 5.0, "character": "Cop"},
        {"id": 5, "name": "Bit Part",  "order": 4, "popularity": 0.1, "character": "Waiter"},
    ],
    "crew": [
        {"id": 10, "name": "Dee Rector",  "job": "Director",                "popularity": 1.5},
        {"id": 11, "name": "Cam Era",      "job": "Director of Photography", "popularity": 0.9},
        {"id": 12, "name": "Mel Ody",      "job": "Original Music Composer", "popularity": 0.5},
        {"id": 13, "name": "Ed Itor",      "job": "Editor",                  "popularity": 0.4},
        {"id": 14, "name": "Art Deco",     "job": "Production Design",       "popularity": 0.3},
        {"id": 15, "name": "Wri Ter",      "job": "Screenplay",             "popularity": 0.2},
    ],
}

rungs = order_rungs(MOVIE, CREDITS)

# --- shape of the ladder ---
check("ladder role sequence", roles(rungs), [
    "Film", "Cast", "Cast", "Director", "Cast", "Cast", "Cast",
    "Cinematographer", "Composer", "Editor", "Production Designer",
])

# --- cast ordered by BILLING, not popularity ---
check("rung 2 is the lead (order 0), not the high-pop villain",
      first_answer(rungs[1]), "Lead One")
check("rung 3 is billing #2 (high pop, but stays put)",
      first_answer(rungs[2]), "Lead Two")
check("high-pop Support B does not jump the billing order",
      [first_answer(r) for r in rungs if r["role"] == "Cast"],
      ["Lead One", "Lead Two", "Support A", "Support B", "Bit Part"])

# --- director floats early (rung 4), technical crew deepest ---
check("director is rung 4", first_answer(rungs[3]), "Dee Rector")
check("deepest four are the technical crew in fixed order",
      [r["role"] for r in rungs[-4:]],
      ["Cinematographer", "Composer", "Editor", "Production Designer"])
check("writer is NOT a rung", "Wri Ter" in [first_answer(r) for r in rungs], False)

# --- film rung carries the original-language title too ---
check("film answers include original title",
      rungs[0]["answers"], ["Test Film", "Pelicula de Prueba"])

# --- popularity tiebreak only when billing ties ---
TIE = {"cast": [
    {"id": 1, "name": "Same A", "order": 5, "popularity": 3.0, "character": "A"},
    {"id": 2, "name": "Same B", "order": 5, "popularity": 7.0, "character": "B"},
]}
check("equal billing -> higher popularity wins the tiebreak",
      [c["name"] for c in order_cast(TIE, 8)], ["Same B", "Same A"])

# --- max_cast trims the long tail (director still floats after lead) ---
trimmed = order_rungs(MOVIE, CREDITS, max_cast=2)
check("max_cast=2 keeps only two cast rungs",
      sum(1 for r in trimmed if r["role"] == "Cast"), 2)
check("trimmed ladder still has director early",
      roles(trimmed)[:4], ["Film", "Cast", "Cast", "Director"])

# --- multiple people in one role collapse to one rung (e.g. the Coens) ---
COENS = {"cast": [{"id": 1, "name": "A Star", "order": 0, "character": "X"}],
         "crew": [
             {"id": 9, "name": "Joel Coen",  "job": "Director"},
             {"id": 8, "name": "Ethan Coen", "job": "Director"},
         ]}
crungs = order_rungs({"title": "Fargo"}, COENS)
director_rung = next(r for r in crungs if r["role"] == "Director")
check("co-directors become one rung with both names",
      director_rung["answers"], ["Joel Coen", "Ethan Coen"])

# --- build_puzzle wraps the rungs with id/images ---
puz = build_puzzle(MOVIE, CREDITS, puzzle_id=42, images=["a.jpg"])
check("puzzle id", puz["id"], 42)
check("puzzle images", puz["images"], ["a.jpg"])
check("puzzle rungs == order_rungs", puz["rungs"], order_rungs(MOVIE, CREDITS))
check("draft carries no decoys/theme yet (added later in curation)",
      ("decoys" in puz or "theme" in puz), False)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
