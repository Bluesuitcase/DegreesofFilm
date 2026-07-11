"""Tests for title_index.py's pure core (build_entries / coverage_gaps).
No network, no key. Run: python curation/title_index.test.py"""
import sys

sys.path.insert(0, "curation")
import title_index  # noqa: E402

FAILS = 0


def check(label, got, expected):
    global FAILS
    ok = got == expected
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else f"  got={got!r} expected={expected!r}"))
    if not ok:
        FAILS += 1


M = [
    {"id": 1, "title": "The Matrix", "release_date": "1999-03-30"},
    {"id": 2, "title": "Inception", "release_date": "2010-07-15"},
    {"id": 1, "title": "The Matrix", "release_date": "1999-03-30"},   # dup id
    {"id": 3, "title": "", "release_date": "2001-01-01"},             # no title
    {"id": 4, "title": "Undated Film", "release_date": ""},           # no date
    {"id": 5, "title": "Fifth", "release_date": "2005-05-05"},
]

E = title_index.build_entries(M, 10)
check("build: dedupes by id + skips missing titles", len(E), 4)
check("build: keeps input (vote_count) order", E[0], ["The Matrix", 1999])
check("build: year parsed as int", E[1], ["Inception", 2010])
check("build: missing date -> year 0", E[2], ["Undated Film", 0])
check("build: truncates to n", len(title_index.build_entries(M, 2)), 2)
check("build: empty input", title_index.build_entries([], 5), [])

LEDGER = [
    {"title": "The Matrix", "year": "1999", "puzzle": 1},
    {"title": "Inception", "year": "2010", "puzzle": 2},
]
check("coverage: all present -> no gaps", title_index.coverage_gaps(E, LEDGER), [])
check("coverage: case-insensitive title match",
      title_index.coverage_gaps([["the matrix", 1999]], [LEDGER[0]]), [])
check("coverage: missing film reported",
      title_index.coverage_gaps(E, LEDGER + [{"title": "Ghost Film", "year": "1988"}]),
      ["Ghost Film (1988)"])
check("coverage: same title wrong year is a gap",
      title_index.coverage_gaps([["The Matrix", 2003]], [LEDGER[0]]),
      ["The Matrix (1999)"])

print(f"\n{10 - FAILS} passed, {FAILS} failed")
sys.exit(1 if FAILS else 0)
