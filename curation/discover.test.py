"""Tests for the discovery filter (pool floor + ledger exclusion). Pure, no network.

Run:  python curation/discover.test.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import discover  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


USED = {2, 5}
RESULTS = [
    {"id": 1, "vote_count": 1000, "vote_average": 7.0, "title": "Good Unused"},
    {"id": 2, "vote_count": 2000, "vote_average": 8.0, "title": "Used"},          # in ledger
    {"id": 3, "vote_count": 100,  "vote_average": 9.0, "title": "Too Few Votes"}, # below votes
    {"id": 4, "vote_count": 900,  "vote_average": 6.0, "title": "Too Low Avg"},   # below avg
    {"id": 5, "vote_count": 5000, "vote_average": 9.0, "title": "Used Too"},      # in ledger
    {"id": 6, "vote_count": 800,  "vote_average": 6.5, "title": "Exactly Floor"}, # boundary OK
]


def ids(ms):
    return [m["id"] for m in ms]


# --- the floor is inclusive at the boundary (>= 800, >= 6.5) ---
check("boundary clears the floor", discover.clears_floor(RESULTS[5]), True)
check("too few votes fails", discover.clears_floor(RESULTS[2]), False)
check("too low average fails", discover.clears_floor(RESULTS[3]), False)

# --- candidates: clears floor AND not used ---
check("candidates skip used + below-floor", ids(discover.candidates(RESULTS, USED)), [1, 6])

# --- pick_unused returns the first valid one ---
check("pick_unused is first valid", discover.pick_unused(RESULTS, USED)["id"], 1)
check("pick_unused none left", discover.pick_unused([], USED), None)

# --- a stricter floor can be passed through ---
check("stricter vote floor drops the boundary film",
      ids(discover.candidates(RESULTS, USED, min_votes=1000)), [1])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
